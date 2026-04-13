#!/usr/bin/env python3

"""Runnable simulation functions invoked by the CLI."""

import os
import sys
import time

from .core.llm import LLMClient, load_pools
from .core import Database, History, Player, Control, build_simulation_graph
from .planning import PlanningAgent
from .output import SimulationProgress, NullProgress
from .output.checkpoint import save_checkpoint, load_checkpoint


async def run_ac_sim(
    pool_name=None,
    pool_override=None,
    base_url=None,
    pools_path=None,
    verbosity=1,
    use_rich=None,
    checkpoint=True,
    resume_path=None,
    report=False,
    podcast=False,
    podcast_voice="en-US-GuyNeural",
    reference_urls=None,
):
    """Run the Azuristan/Crimsonia geopolitical simulation."""

    # Load pool — use override if provided (e.g. from custom builder)
    if pool_override is not None:
        pool = pool_override
        if base_url is None:
            base_url = "https://openrouter.ai/api/v1"
    else:
        if pools_path is None:
            pools_path = os.path.join("config", "pools.yaml")
        pools, active, base_url_loaded = load_pools(pools_path)
        pool = pools.get(pool_name or active)
        if base_url is None:
            base_url = base_url_loaded

    client = LLMClient(base_url=base_url)

    title = "Azuristan and Crimsonia"
    scenario = """\
Azuristan and Crimsonia are neighboring countries in Central Asia.  Azuristan is a \
Western-backed democracy that suffers from endemic corruption.  Crimsonia is controlled \
by an autocratic government that stifles dissent and commits human rights violations.

Both countries have modern professional militaries, although Crimsonia's is slightly \
larger than Azuristan's.  In addition, Azuristan possesses ten nuclear weapons and \
Crimsonia has eight.

Most citizens of Azuristan are from the Azuristani ethnic group, and most citizens of \
Crimsonia are from the Crimsonian ethnic group.  The only exception is Azuristan's \
province of Tyriana, on the border with Crimsonia.  Most residents of Tyriana belong \
to the Crimsonian ethnic group.

The animosity between Azuristan and Crimsonia extends back over centuries of ethnic \
tension and intermittent warfare.  Recent years have been fairly calm.  However, that \
suddenly changes when Tyriana declares independence.  Amidst the crisis, local leaders \
in Tyriana ask Crimsonia to come to the province's defense, and the same leaders \
indicate that they want Tyriana to become part of Crimsonia."""

    goals = {
        'azuristan_dove': "Your goal is to avoid war at all costs, and to preserve the sovereignty of Azuristan if possible.",
        'crimsonia_dove': "Your goal is to avoid war at all costs, and to unify the Crimsonian people if possible.",
    }

    moves_total = 3
    num_players = 2

    # Progress reporter
    if use_rich is None:
        use_rich = sys.stdout.isatty()
    if use_rich:
        progress = SimulationProgress(total_moves=moves_total, total_players=num_players)
    else:
        progress = NullProgress(total_moves=moves_total, total_players=num_players)

    # Resume from checkpoint
    resuming = False
    initial_state_override = {}
    if resume_path:
        if verbosity >= 1:
            print(f"[resume] Loading checkpoint: {resume_path}")
        initial_state_override = load_checkpoint(resume_path)
        resuming = True
        if verbosity >= 1:
            move = initial_state_override.get("move_current", "?")
            total = initial_state_override.get("moves_total", "?")
            print(f"[resume] Resuming from move {move}/{total}")

    # Planning agent (skip if resuming — briefing is in the checkpoint)
    if not resuming:
        planner = PlanningAgent(
            llm_client=client, model=pool.planner,
            verbosity=verbosity, progress=progress,
        )
        briefing = await planner.create_briefing(
            scenario=scenario, title=title,
            reference_urls=reference_urls,
        )
    else:
        briefing = initial_state_override.get("briefing", "")

    # Database
    db_dir = os.path.join(os.getcwd(), ".geopol_data")
    os.makedirs(db_dir, exist_ok=True)
    db = Database(ioid="sim_ac", path=db_dir, initialize=True)

    # Players
    players = [
        Player(
            database=db, verbosity=verbosity, progress=progress,
            llm_client=client, model_id=pool.player,
            name="President of Azuristan",
            persona=f"the leader of Azuristan. {goals['azuristan_dove']}",
        ),
        Player(
            database=db, verbosity=verbosity, progress=progress,
            llm_client=client, model_id=pool.player,
            name="Premier of Crimsonia",
            persona=f"the leader of Crimsonia. {goals['crimsonia_dove']}",
        ),
    ]

    # Narrator
    narrator = Control(
        database=db, verbosity=verbosity, progress=progress,
        llm_client=client, model_id=pool.narrator,
    )

    # Graph callback wiring
    async def player_respond_fn(player_config, history):
        player_obj = next(p for p in players if p.name == player_config["name"])
        h = History()
        for entry in history:
            h.add(entry["name"], entry["text"])
        return await player_obj.respond(history=h)

    async def adjudicate_fn(history, responses, nature, timestep, mode):
        h = History()
        for entry in history:
            h.add(entry["name"], entry["text"])
        r = History()
        for entry in responses:
            r.add(entry["name"], entry["text"])
        return await narrator.adjudicate(
            history=h, responses=r, nature=nature, timestep=timestep, mode=mode
        )

    async def assess_fn(history, query, mc=None):
        h = History()
        for entry in history:
            h.add(entry["name"], entry["text"])
        return await narrator.assess(history=h, query=query, mc=mc)

    # Build initial state
    initial_state = {
        "scenario": scenario,
        "briefing": briefing,
        "title": title,
        "timestep": "month",
        "nature": 1.0,
        "mode": ["geopol"],
        "player_configs": [
            {"name": p.name, "persona": p.persona, "model_id": p.model_id}
            for p in players
        ],
        "moves_total": moves_total,
        "move_current": 0,
        "current_player_idx": 0,
        "history": [],
        "current_responses": [],
        "questions": ["In one sentence, what was the outcome?"],
        "mc_questions": [
            ["What was the final status of Tyriana?",
             ["part of Azuristan", "part of Crimsonia", "independent", "not yet determined"]],
            ["Did armed conflict occur?", ["yes", "no"]],
        ],
        "assessments": [],
        "_player_respond": player_respond_fn,
        "_adjudicate": adjudicate_fn,
        "_assess": assess_fn,
        "_verbosity": verbosity,
        "_progress": progress,
        "_checkpoint": checkpoint,
        "_resuming": resuming,
    }

    # Merge checkpoint state (overrides history, move_current, etc.)
    if resuming:
        for key in ("history", "move_current", "current_player_idx",
                     "current_responses", "assessments", "moves_total",
                     "briefing", "scenario"):
            if key in initial_state_override:
                initial_state[key] = initial_state_override[key]

    # Run
    graph = build_simulation_graph()
    t_start = time.monotonic()
    result = await graph.ainvoke(initial_state)
    runtime_seconds = time.monotonic() - t_start

    # Assessments
    print("\n\n=== ASSESSMENTS ===\n")
    for a in result.get("assessments", []):
        print(f"Q: {a['question']}")
        print(f"A: {a['answer']}")
        print()

    progress.finish()

    # Print runtime summary
    if runtime_seconds < 60:
        rt_str = f"{runtime_seconds:.1f}s"
    else:
        rt_min = int(runtime_seconds // 60)
        rt_sec = int(runtime_seconds % 60)
        rt_str = f"{rt_min}m {rt_sec}s"
    print(f"\n[runtime] Simulation completed in {rt_str}")
    print(f"[runtime] Pool: {pool_name or 'custom'}")

    # Post-simulation outputs
    if report:
        try:
            from .output.report import generate_report
            print("[report] Generating PDF report...")
            pdf_path = generate_report(result, runtime_seconds=runtime_seconds)
            print(f"[report] PDF saved: {pdf_path}")
        except Exception as e:
            print(f"[report] Failed to generate report: {e}")

    if podcast:
        try:
            from .output.podcast import generate_podcast
            print("[podcast] Generating podcast episode...")
            mp3_path = await generate_podcast(
                result, llm_client=client, model=pool.narrator,
                voice=podcast_voice, verbosity=verbosity,
            )
            print(f"[podcast] MP3 saved: {mp3_path}")
        except Exception as e:
            print(f"[podcast] Failed to generate podcast: {e}")

    return result
