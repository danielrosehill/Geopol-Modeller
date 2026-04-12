#!/usr/bin/env python3

"""Runnable simulation functions invoked by the CLI."""

import os
from .core.llm import LLMClient, load_pools
from .core import Database, History, Player, Control, build_simulation_graph
from .planning import PlanningAgent


async def run_ac_sim(pool_name=None, pools_path=None, verbosity=1):
    """Run the Azuristan/Crimsonia geopolitical simulation."""

    # Load pool
    if pools_path is None:
        pools_path = os.path.join("config", "pools.yaml")
    pools, active, base_url = load_pools(pools_path)
    pool = pools.get(pool_name or active)

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

    # Planning agent
    planner = PlanningAgent(llm_client=client, model=pool.planner, verbosity=verbosity)
    briefing = await planner.create_briefing(scenario=scenario, title=title)

    # Database
    db_dir = os.path.join(os.getcwd(), ".snowglobe_data")
    os.makedirs(db_dir, exist_ok=True)
    db = Database(ioid="sim_ac", path=db_dir, initialize=True)

    # Players
    players = [
        Player(
            database=db, verbosity=verbosity,
            llm_client=client, model_id=pool.player,
            name="President of Azuristan",
            persona=f"the leader of Azuristan. {goals['azuristan_dove']}",
        ),
        Player(
            database=db, verbosity=verbosity,
            llm_client=client, model_id=pool.player,
            name="Premier of Crimsonia",
            persona=f"the leader of Crimsonia. {goals['crimsonia_dove']}",
        ),
    ]

    # Narrator
    narrator = Control(
        database=db, verbosity=verbosity,
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

    # Run
    graph = build_simulation_graph()
    result = await graph.ainvoke({
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
        "moves_total": 3,
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
    })

    print("\n\n=== ASSESSMENTS ===\n")
    for a in result.get("assessments", []):
        print(f"Q: {a['question']}")
        print(f"A: {a['answer']}")
        print()

    return result
