#!/usr/bin/env python3

"""Generic scenario runner — loads any scenario YAML + optional actor cluster."""

import os
import random
import sys
import time

from ruamel.yaml import YAML

from .core.llm import LLMClient, load_pools
from .core import Database, History, Player, Control, build_simulation_graph
from .planning.sitrep import SitrepAgent
from .output import SimulationProgress, NullProgress
from .output.checkpoint import save_checkpoint, load_checkpoint
from .graph_config import load_graph_config, parse_escalation_from_output


TIMEFRAME_PRESETS = {
    "short": ["+24h"],
    "medium": ["+24h", "+72h", "+2 weeks"],
    "long": ["+24h", "+72h", "+2 weeks", "+1 month", "+3 months"],
    "daily": ["+24h", "+48h"],
}


def load_scenario(scenario_path):
    """Load a scenario YAML file and return the parsed dict."""
    yaml = YAML(typ="safe")
    with open(scenario_path, "r") as f:
        return yaml.load(f)


def resolve_timeframes(scenario_data):
    """Resolve timeframes from scenario config.

    Priority: custom timeframes > preset > legacy timestep/moves fields.

    Returns:
        (timeframes, timestep, moves_total) where timeframes is a list of
        label strings like ["+24h", "+72h"] or None if using legacy mode.
    """
    # Custom timeframes list takes priority
    custom = scenario_data.get("timeframes")
    if custom:
        return list(custom), custom[0], len(custom)

    # Named preset
    preset_name = scenario_data.get("timeframe_preset")
    if preset_name:
        if preset_name not in TIMEFRAME_PRESETS:
            print(f"Warning: unknown timeframe_preset '{preset_name}', "
                  f"available: {', '.join(TIMEFRAME_PRESETS.keys())}")
        timeframes = TIMEFRAME_PRESETS.get(preset_name, TIMEFRAME_PRESETS["short"])
        return list(timeframes), timeframes[0], len(timeframes)

    # Legacy: timestep + moves
    timestep = scenario_data.get("timestep", "month")
    moves = scenario_data.get("moves", 3)
    return None, timestep, moves


def load_actor_cluster(cluster_name, config_dir):
    """Load an actor cluster YAML by name from config/actors/."""
    cluster_path = os.path.join(config_dir, "actors", f"{cluster_name}.yaml")
    if not os.path.exists(cluster_path):
        raise FileNotFoundError(f"Actor cluster not found: {cluster_path}")
    yaml = YAML(typ="safe")
    with open(cluster_path, "r") as f:
        return yaml.load(f)


def build_persona(actor):
    """Build a persona string from an actor definition.

    Incorporates red lines, response patterns, and constraints into the
    persona so the LLM has full character context.
    """
    parts = [actor["persona"].strip()]

    if actor.get("red_lines"):
        lines = "; ".join(actor["red_lines"])
        parts.append(f"Known red lines: {lines}.")

    if actor.get("response_pattern"):
        parts.append(f"Typical response pattern: {actor['response_pattern'].strip()}")

    if actor.get("constraints"):
        cons = "; ".join(actor["constraints"])
        parts.append(f"Constraints: {cons}.")

    return " ".join(parts)


def resolve_actors(scenario_data, config_dir):
    """Resolve actors from scenario inline definitions and/or cluster reference."""
    actors = []

    # Load from cluster if specified
    cluster_name = scenario_data.get("actor_cluster")
    if cluster_name:
        cluster = load_actor_cluster(cluster_name, config_dir)
        cluster_actors = cluster.get("actors", [])

        # Filter to active_actors if specified
        active_ids = scenario_data.get("active_actors")
        if active_ids:
            active_set = set(active_ids)
            cluster_actors = [a for a in cluster_actors if a["id"] in active_set]

        actors.extend(cluster_actors)

    # Add/override with inline actors
    inline_actors = scenario_data.get("actors", [])
    if inline_actors:
        existing_ids = {a["id"] for a in actors}
        for actor in inline_actors:
            if actor["id"] in existing_ids:
                # Replace cluster actor with inline override
                actors = [a if a["id"] != actor["id"] else actor for a in actors]
            else:
                actors.append(actor)

    return actors


async def run_scenario(
    scenario_path,
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
    track_predictions=True,
):
    """Run a simulation from a scenario YAML file."""

    # Resolve config directory
    config_dir = os.path.dirname(scenario_path)
    if os.path.basename(config_dir) == "scenarios":
        config_dir = os.path.dirname(config_dir)

    # Load scenario
    scenario_data = load_scenario(scenario_path)
    title = scenario_data["title"]
    scenario_text = scenario_data["scenario"]
    timeframes, timestep, moves_total = resolve_timeframes(scenario_data)
    nature = scenario_data.get("nature", True)
    mode = scenario_data.get("mode", ["geopol"])

    # Resolve actors
    actors = resolve_actors(scenario_data, config_dir)
    if not actors:
        print("Error: No actors defined in scenario or actor cluster.")
        sys.exit(1)

    num_players = len(actors)

    # Load graph config (scenario subgraph)
    graph_config = load_graph_config(scenario_data, config_dir)

    # Build actor name→id map for visibility filtering
    actor_id_map = {a["name"]: a["id"] for a in actors}
    actor_name_map = {a["id"]: a["name"] for a in actors}

    if verbosity >= 1:
        print(f"\n  Scenario: {title}")
        print(f"  Actors:   {num_players}")
        if timeframes:
            print(f"  Timeframes: {' → '.join(timeframes)}")
        else:
            print(f"  Moves:    {moves_total} × {timestep}")
        print(f"  Actors:   {', '.join(a['name'] for a in actors)}")
        if graph_config.name != "default":
            features = []
            if graph_config.has_visibility_rules:
                features.append("info-asymmetry")
            if graph_config.has_shocks:
                features.append("shocks")
            if graph_config.has_escalation_tracking:
                features.append("escalation-tracking")
            if graph_config.has_adaptive_tempo:
                features.append("adaptive-tempo")
            print(f"  Subgraph: {graph_config.name} ({', '.join(features)})")
        print()

    # Load pool
    if pool_override is not None:
        pool = pool_override
        if base_url is None:
            base_url = "https://openrouter.ai/api/v1"
    else:
        if pools_path is None:
            pools_path = os.path.join(config_dir, "pools.yaml")
        pools, active, base_url_loaded = load_pools(pools_path)
        pool = pools.get(pool_name or active)
        if base_url is None:
            base_url = base_url_loaded

    client = LLMClient(base_url=base_url)

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

    # SITREP generation
    sitrep_path = None
    if not resuming:
        sitrep_agent = SitrepAgent(
            llm_client=client, model=pool.planner,
            verbosity=verbosity, progress=progress,
        )
        actor_names = [a["name"] for a in actors]
        briefing, sitrep_path = await sitrep_agent.generate_sitrep(
            scenario=scenario_text, title=title,
            reference_urls=reference_urls,
            actor_names=actor_names,
        )
    else:
        briefing = initial_state_override.get("briefing", "")

    # Database
    db_dir = os.path.join(os.getcwd(), ".snowglobe_data")
    os.makedirs(db_dir, exist_ok=True)
    db = Database(ioid="sim_scenario", path=db_dir, initialize=True)

    # Build players from actors
    players = []
    for actor in actors:
        persona = build_persona(actor)
        players.append(Player(
            database=db, verbosity=verbosity, progress=progress,
            llm_client=client, model_id=pool.player,
            name=actor["name"],
            persona=persona,
        ))

    # Narrator
    narrator = Control(
        database=db, verbosity=verbosity, progress=progress,
        llm_client=client, model_id=pool.narrator,
    )

    # Graph callback wiring
    async def player_respond_fn(player_config, history):
        player_obj = next(p for p in players if p.name == player_config["name"])

        # Information asymmetry: filter history based on bloc visibility
        actor_id = actor_id_map.get(player_config["name"])
        if graph_config.has_visibility_rules and actor_id:
            visible_history = graph_config.filter_history_for_actor(
                history, actor_id, actor_id_map,
            )
        else:
            visible_history = history

        h = History()
        for entry in visible_history:
            h.add(entry["name"], entry["text"])
        return await player_obj.respond(history=h)

    # Track which move we're on for timeframe labelling
    _move_counter = [0]
    _current_escalation = [None]  # track for adaptive tempo

    async def adjudicate_fn(history, responses, nature_val, timestep_val, mode_val):
        # Use timeframe label for current move if available
        if timeframes and _move_counter[0] < len(timeframes):
            timestep_val = timeframes[_move_counter[0]]

        # Adaptive tempo: override timestep based on escalation level
        if graph_config.has_adaptive_tempo and _current_escalation[0] is not None:
            adaptive_ts = graph_config.get_adaptive_timestep(_current_escalation[0])
            if adaptive_ts:
                if verbosity >= 2:
                    print(f"  [adaptive-tempo] escalation={_current_escalation[0]} → timestep={adaptive_ts}")
                timestep_val = adaptive_ts

        _move_counter[0] += 1

        h = History()
        for entry in history:
            h.add(entry["name"], entry["text"])
        r = History()
        for entry in responses:
            r.add(entry["name"], entry["text"])

        # Shock injection: replace generic "unexpected consequences" with
        # domain-specific shocks from the graph config taxonomy
        shock_inject = None
        if graph_config.has_shocks and random.random() < nature_val:
            shock = graph_config.select_shock()
            if shock:
                shock_inject = shock
                if verbosity >= 1:
                    print(f"  [shock] {shock['id']}: {shock['trigger'][:80]}...")

        # Build custom query with shock and escalation instructions
        custom_query = None
        if shock_inject or graph_config.has_escalation_tracking:
            parts = []
            if "geopol" in mode_val:
                parts.append(
                    "Describe these plans being carried out, assuming the "
                    "leaders above issue no further orders."
                )
            else:
                parts.append(
                    f"Weave these plans into a cohesive narrative of what "
                    f"happens in the next {timestep_val}."
                )

            if shock_inject:
                parts.append(
                    f"\n\nIMPORTANT — an exogenous event occurs during this "
                    f"period that all actors must react to:\n"
                    f"{shock_inject['trigger']}\n"
                    f"Consequences: {shock_inject.get('consequences', '')}"
                )
            elif random.random() < nature_val:
                parts.append(" Include unexpected consequences.")

            parts.append(graph_config.get_escalation_prompt_suffix())
            custom_query = "".join(parts)

        if custom_query is not None:
            # We handled nature/shocks ourselves — pass nature=0 to avoid double-roll
            output = await narrator.adjudicate(
                history=h, responses=r, nature=0,
                timestep=timestep_val, mode=mode_val,
                query=custom_query,
            )
        else:
            # No graph config features active — use default adjudication
            output = await narrator.adjudicate(
                history=h, responses=r, nature=nature_val,
                timestep=timestep_val, mode=mode_val,
            )

        # Parse escalation data from output if tracking is enabled
        if graph_config.has_escalation_tracking:
            level, direction, clean_output = parse_escalation_from_output(output)
            if level is not None:
                _current_escalation[0] = level
                if verbosity >= 1:
                    level_name = graph_config.escalation_levels.get(level, "unknown")
                    print(f"  [escalation] level={level} ({level_name}) direction={direction}")
            return clean_output

        return output

    async def assess_fn(history, query, mc=None):
        h = History()
        for entry in history:
            h.add(entry["name"], entry["text"])
        return await narrator.assess(history=h, query=query, mc=mc)

    # Questions
    questions = scenario_data.get("questions", [
        "In one sentence, what was the outcome?",
    ])
    mc_questions = []
    for mcq in scenario_data.get("mc_questions", []):
        mc_questions.append([mcq["question"], mcq["options"]])

    # Build initial state
    initial_state = {
        "scenario": scenario_text,
        "briefing": briefing,
        "title": title,
        "timestep": timestep,
        "nature": 1.0 if nature is True else (float(nature) if nature else 0.0),
        "mode": mode,
        "player_configs": [
            {"name": p.name, "persona": p.persona, "model_id": p.model_id}
            for p in players
        ],
        "moves_total": moves_total,
        "move_current": 0,
        "current_player_idx": 0,
        "history": [],
        "current_responses": [],
        "questions": questions,
        "mc_questions": mc_questions,
        "assessments": [],
        "escalation_history": [],
        "_player_respond": player_respond_fn,
        "_adjudicate": adjudicate_fn,
        "_assess": assess_fn,
        "_verbosity": verbosity,
        "_progress": progress,
        "_checkpoint": checkpoint,
        "_resuming": resuming,
    }

    # Merge checkpoint state
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

    # Runtime summary
    if runtime_seconds < 60:
        rt_str = f"{runtime_seconds:.1f}s"
    else:
        rt_min = int(runtime_seconds // 60)
        rt_sec = int(runtime_seconds % 60)
        rt_str = f"{rt_min}m {rt_sec}s"
    print(f"\n[runtime] Simulation completed in {rt_str}")
    print(f"[runtime] Pool: {pool_name or 'custom'}")
    print(f"[runtime] Scenario: {os.path.basename(scenario_path)}")
    if sitrep_path:
        print(f"[runtime] SITREP: {sitrep_path}")

    # Prediction tracking
    if track_predictions and result.get("assessments"):
        try:
            from .predictions.store import PredictionStore
            from .predictions.extractor import PredictionExtractor
            from .predictions.changelog import capture_pipeline_version
            from .predictions.models import PredictionRun
            import hashlib

            store = PredictionStore()

            # Create run record
            scenario_hash = hashlib.sha256(scenario_text.encode()).hexdigest()[:16]
            models_dict = {
                "planner": pool.planner, "narrator": pool.narrator,
                "player": pool.player, "advisor": pool.advisor,
            }
            run_record = PredictionRun(
                scenario_title=title,
                scenario_hash=scenario_hash,
                pool_name=pool_name or "custom",
                models_used=models_dict,
                runtime_seconds=runtime_seconds,
                source="snowglobe",
            )
            store.save_run(run_record)

            # Extract structured predictions via LLM
            if verbosity >= 1:
                print("[track] Extracting predictions from assessments...")
            extractor = PredictionExtractor(llm_client=client, model=pool.narrator)
            predictions = await extractor.extract(
                assessments=result["assessments"],
                run_id=run_record.id,
            )
            if predictions:
                store.save_predictions_batch(predictions)
                if verbosity >= 1:
                    print(f"[track] Stored {len(predictions)} predictions (run {run_record.id[:8]})")
            else:
                if verbosity >= 1:
                    print("[track] No extractable predictions found.")

            # Record pipeline version
            capture_pipeline_version(
                store, run_id=run_record.id,
                pools_path=pools_path,
                scenario_path=scenario_path,
                config_snapshot=models_dict,
            )

        except Exception as e:
            if verbosity >= 1:
                print(f"[track] Prediction tracking failed: {e}")

    # Post-simulation outputs
    if report:
        try:
            from .output.report_agent import generate_report_agent
            print("[report] Generating PDF report via LLM agent...")
            pdf_path = await generate_report_agent(
                result, llm_client=client, model=pool.narrator,
                runtime_seconds=runtime_seconds,
            )
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
