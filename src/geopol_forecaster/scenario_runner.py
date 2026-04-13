#!/usr/bin/env python3

"""Generic scenario runner — loads any scenario YAML + optional actor cluster.

Supports two modes:
1. Run config (config/runs/*.yaml) — composes scenario, actors, questions,
   timeframe, graph config as first-class entities.
2. Legacy scenario (config/scenarios/*.yaml with inline questions/timeframes) —
   backward compatible.
"""

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


# Legacy hardcoded presets — used as fallback when config/timeframes/ not found
TIMEFRAME_PRESETS = {
    "short": ["+24h"],
    "medium": ["+24h", "+72h", "+2 weeks"],
    "long": ["+24h", "+72h", "+2 weeks", "+1 month", "+3 months"],
    "daily": ["+24h", "+48h"],
}


# ============================================================
#  Entity loaders
# ============================================================

def load_scenario(scenario_path):
    """Load a scenario YAML file and return the parsed dict."""
    yaml = YAML(typ="safe")
    with open(scenario_path, "r") as f:
        return yaml.load(f)


def load_questions_file(questions_name, config_dir):
    """Load a questions YAML from config/questions/<name>.yaml.

    Returns:
        (questions_list, mc_questions_list) where each is a list ready
        for the simulation.
    """
    questions_path = os.path.join(config_dir, "questions", f"{questions_name}.yaml")
    if not os.path.exists(questions_path):
        raise FileNotFoundError(f"Questions file not found: {questions_path}")
    yaml = YAML(typ="safe")
    with open(questions_path, "r") as f:
        data = yaml.load(f)

    questions = [q["text"] for q in data.get("questions", [])]
    mc_questions = []
    for mcq in data.get("mc_questions", []):
        mc_questions.append([mcq["question"], mcq["options"]])

    return questions, mc_questions


def load_timeframe_file(timeframe_name, config_dir):
    """Load a timeframe YAML from config/timeframes/<name>.yaml.

    Returns:
        List of timeframe strings like ["+24h", "+72h", "+2 weeks"].
    """
    timeframe_path = os.path.join(config_dir, "timeframes", f"{timeframe_name}.yaml")
    if not os.path.exists(timeframe_path):
        # Fall back to hardcoded presets
        if timeframe_name in TIMEFRAME_PRESETS:
            return TIMEFRAME_PRESETS[timeframe_name]
        raise FileNotFoundError(f"Timeframe file not found: {timeframe_path}")
    yaml = YAML(typ="safe")
    with open(timeframe_path, "r") as f:
        data = yaml.load(f)
    return list(data.get("timeframes", ["+24h"]))


def load_run_config(run_path):
    """Load a run config YAML from config/runs/<name>.yaml.

    A run config composes:
      - scenario (reference to config/scenarios/)
      - actor_cluster (reference to config/actors/)
      - graph_config (reference to config/graphs/)
      - questions (list of references to config/questions/)
      - timeframe (reference to config/timeframes/)
      - nature, mode, pool (runtime params)

    Returns:
        Parsed dict.
    """
    yaml = YAML(typ="safe")
    with open(run_path, "r") as f:
        return yaml.load(f)


def resolve_timeframes(scenario_data, config_dir=None):
    """Resolve timeframes from scenario config.

    Priority: custom timeframes > preset file > preset name > legacy timestep/moves.

    Returns:
        (timeframes, timestep, moves_total) where timeframes is a list of
        label strings like ["+24h", "+72h"] or None if using legacy mode.
    """
    # Custom timeframes list takes priority
    custom = scenario_data.get("timeframes")
    if custom:
        return list(custom), custom[0], len(custom)

    # Named preset — try file first, then hardcoded
    preset_name = scenario_data.get("timeframe_preset") or scenario_data.get("timeframe")
    if preset_name:
        if config_dir:
            try:
                timeframes = load_timeframe_file(preset_name, config_dir)
                return list(timeframes), timeframes[0], len(timeframes)
            except FileNotFoundError:
                pass
        # Hardcoded fallback
        if preset_name not in TIMEFRAME_PRESETS:
            print(f"Warning: unknown timeframe '{preset_name}', "
                  f"available: {', '.join(TIMEFRAME_PRESETS.keys())}")
        timeframes = TIMEFRAME_PRESETS.get(preset_name, TIMEFRAME_PRESETS["short"])
        return list(timeframes), timeframes[0], len(timeframes)

    # Legacy: timestep + moves
    timestep = scenario_data.get("timestep", "month")
    moves = scenario_data.get("moves", 3)
    return None, timestep, moves


def resolve_questions(run_data, scenario_data, config_dir,
                      question_filter=None):
    """Resolve questions from run config, scenario, or individual selection.

    Args:
        run_data: Run config dict (may be None for legacy mode).
        scenario_data: Scenario dict (may have inline questions).
        config_dir: Path to config/ directory.
        question_filter: Optional list of question IDs or texts to select.

    Returns:
        (questions, mc_questions) where questions is a list of strings
        and mc_questions is a list of [question, options] pairs.
    """
    all_questions = []
    all_mc_questions = []

    # Load from run config question references
    if run_data and run_data.get("questions"):
        q_refs = run_data["questions"]
        if isinstance(q_refs, str):
            q_refs = [q_refs]
        for q_ref in q_refs:
            qs, mcs = load_questions_file(q_ref, config_dir)
            all_questions.extend(qs)
            all_mc_questions.extend(mcs)

    # Fall back to inline questions in scenario
    if not all_questions and not all_mc_questions:
        for q in scenario_data.get("questions", []):
            if isinstance(q, dict):
                all_questions.append(q.get("text", ""))
            else:
                all_questions.append(q)
        for mcq in scenario_data.get("mc_questions", []):
            all_mc_questions.append([mcq["question"], mcq["options"]])

    # Default question if nothing found
    if not all_questions and not all_mc_questions:
        all_questions = ["In one sentence, what was the outcome?"]

    # Apply question filter if specified
    if question_filter:
        filter_set = set(question_filter)
        # Filter open-ended questions by text match or index
        filtered_q = []
        for i, q in enumerate(all_questions):
            if q in filter_set or str(i) in filter_set:
                filtered_q.append(q)
            # Also match by question ID if we loaded from files
            # (partial text match for convenience)
            elif any(f.lower() in q.lower() for f in filter_set):
                filtered_q.append(q)

        # Filter MC questions similarly
        filtered_mc = []
        for mc_q, mc_opts in all_mc_questions:
            if mc_q in filter_set:
                filtered_mc.append([mc_q, mc_opts])
            elif any(f.lower() in mc_q.lower() for f in filter_set):
                filtered_mc.append([mc_q, mc_opts])

        if filtered_q or filtered_mc:
            all_questions = filtered_q
            all_mc_questions = filtered_mc
        else:
            print(f"Warning: question filter matched nothing, using all questions.")

    return all_questions, all_mc_questions


def load_actor_registry(config_dir):
    """Load the shared actor registry from config/actors/_registry.yaml."""
    registry_path = os.path.join(config_dir, "actors", "_registry.yaml")
    if not os.path.exists(registry_path):
        return {}
    yaml = YAML(typ="safe")
    with open(registry_path, "r") as f:
        data = yaml.load(f)
    if not data or "actors" not in data:
        return {}
    return {a["id"]: a for a in data["actors"]}


def load_actor_cluster(cluster_name, config_dir):
    """Load an actor cluster YAML by name from config/actors/.

    Supports two formats:
    1. Full inline definitions (legacy): actors list with full persona etc.
    2. Registry references: actors list with just {id: "xxx"} or {id: "xxx", overrides...}
       These are resolved against _registry.yaml, with any extra fields used as overrides.
    """
    cluster_path = os.path.join(config_dir, "actors", f"{cluster_name}.yaml")
    if not os.path.exists(cluster_path):
        raise FileNotFoundError(f"Actor cluster not found: {cluster_path}")
    yaml = YAML(typ="safe")
    with open(cluster_path, "r") as f:
        data = yaml.load(f)

    # Resolve registry references if actors lack a 'persona' field
    registry = None
    actors = data.get("actors", [])
    resolved = []
    for actor in actors:
        if "persona" not in actor:
            # This is a registry reference — resolve it
            if registry is None:
                registry = load_actor_registry(config_dir)
            base = registry.get(actor["id"])
            if base is None:
                raise ValueError(
                    f"Actor '{actor['id']}' not found in _registry.yaml "
                    f"and has no inline persona."
                )
            # Merge: registry base + cluster overrides
            merged = {**base, **actor}
            resolved.append(merged)
        else:
            resolved.append(actor)

    data["actors"] = resolved
    return data


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


def resolve_actors(scenario_data, config_dir, run_data=None):
    """Resolve actors from run config, scenario, or actor cluster."""
    actors = []

    # Actor cluster from run config or scenario
    cluster_name = None
    if run_data:
        cluster_name = run_data.get("actor_cluster")
    if not cluster_name:
        cluster_name = scenario_data.get("actor_cluster")

    if cluster_name:
        cluster = load_actor_cluster(cluster_name, config_dir)
        cluster_actors = cluster.get("actors", [])

        # Filter to active_actors if specified
        active_ids = scenario_data.get("active_actors")
        if run_data and run_data.get("active_actors"):
            active_ids = run_data["active_actors"]
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


# ============================================================
#  Run config resolver
# ============================================================

def resolve_run_config(run_path, config_dir):
    """Resolve a run config into all component data.

    Returns:
        Dict with resolved scenario_data, actors, questions, timeframes,
        and runtime params.
    """
    run_data = load_run_config(run_path)

    # Load the scenario
    scenario_name = run_data.get("scenario")
    if not scenario_name:
        raise ValueError("Run config must specify a 'scenario'.")
    scenario_path = os.path.join(config_dir, "scenarios", f"{scenario_name}.yaml")
    if not os.path.exists(scenario_path):
        raise FileNotFoundError(f"Scenario not found: {scenario_path}")
    scenario_data = load_scenario(scenario_path)

    # Merge run-level fields into scenario_data for downstream compat
    # (run config overrides scenario defaults)
    for key in ("nature", "mode", "graph_config", "actor_cluster",
                "timeframe", "timeframe_preset", "timeframes"):
        if key in run_data and run_data[key] is not None:
            scenario_data[key] = run_data[key]

    # Map 'timeframe' key to 'timeframe_preset' for resolve_timeframes()
    if "timeframe" in run_data and "timeframe_preset" not in scenario_data:
        scenario_data["timeframe_preset"] = run_data["timeframe"]

    return run_data, scenario_data, scenario_path


# ============================================================
#  Main runner
# ============================================================

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
    sync_hf=True,
    run_config_path=None,
    question_filter=None,
):
    """Run a simulation from a scenario YAML file or run config.

    Args:
        scenario_path: Path to scenario YAML (used if run_config_path is None).
        run_config_path: Path to run config YAML (overrides scenario_path).
        question_filter: Optional list of question texts/IDs to run (subset).
    """

    # Resolve config directory
    config_dir = os.path.dirname(scenario_path)
    if os.path.basename(config_dir) == "scenarios":
        config_dir = os.path.dirname(config_dir)
    elif os.path.basename(config_dir) == "runs":
        config_dir = os.path.dirname(config_dir)

    # Load via run config or direct scenario
    run_data = None
    if run_config_path:
        run_data, scenario_data, scenario_path = resolve_run_config(
            run_config_path, config_dir,
        )
    else:
        scenario_data = load_scenario(scenario_path)

    title = scenario_data["title"]
    scenario_text = scenario_data["scenario"]
    timeframes, timestep, moves_total = resolve_timeframes(scenario_data, config_dir)
    nature = scenario_data.get("nature", True)
    mode = scenario_data.get("mode", ["geopol"])

    # Resolve actors
    actors = resolve_actors(scenario_data, config_dir, run_data)
    if not actors:
        print("Error: No actors defined in scenario or actor cluster.")
        sys.exit(1)

    num_players = len(actors)

    # Load graph config (scenario subgraph)
    graph_config = load_graph_config(scenario_data, config_dir)

    # Build actor name→id map for visibility filtering
    actor_id_map = {a["name"]: a["id"] for a in actors}
    actor_name_map = {a["id"]: a["name"] for a in actors}

    # Resolve questions
    questions, mc_questions = resolve_questions(
        run_data, scenario_data, config_dir, question_filter,
    )

    if verbosity >= 1:
        print(f"\n  Scenario: {title}")
        print(f"  Actors:   {num_players}")
        if timeframes:
            print(f"  Timeframes: {' → '.join(timeframes)}")
        else:
            print(f"  Moves:    {moves_total} × {timestep}")
        print(f"  Actors:   {', '.join(a['name'] for a in actors)}")
        print(f"  Questions: {len(questions)} open + {len(mc_questions)} MC")
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
        if run_data:
            print(f"  Run config: {os.path.basename(run_config_path or '')}")
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
    db_dir = os.path.join(os.getcwd(), ".geopol_data")
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
    async def player_respond_fn(player_config, history, timestep=None,
                                move_current=None, moves_total=None):
        player_obj = next(p for p in players if p.name == player_config["name"])

        # Information asymmetry: filter history based on bloc visibility
        actor_id = actor_id_map.get(player_config["name"])
        if graph_config.has_visibility_rules and actor_id:
            visible_history = graph_config.filter_history_for_actor(
                history, actor_id, actor_id_map,
            )
        else:
            visible_history = history

        # Use timeframe label for current move if available
        effective_timestep = timestep
        if timeframes and move_current is not None and move_current < len(timeframes):
            effective_timestep = timeframes[move_current]

        h = History()
        for entry in visible_history:
            h.add(entry["name"], entry["text"])
        return await player_obj.respond(
            history=h, timestep=effective_timestep,
            move_current=move_current, moves_total=moves_total,
        )

    # Track which move we're on for timeframe labelling
    _move_counter = [0]
    _current_escalation = [None]  # track for adaptive tempo

    async def adjudicate_fn(history, responses, nature=None, timestep=None, mode=None, **kwargs):
        # Use timeframe label for current move if available
        if timeframes and _move_counter[0] < len(timeframes):
            timestep = timeframes[_move_counter[0]]

        # Adaptive tempo: override timestep based on escalation level
        if graph_config.has_adaptive_tempo and _current_escalation[0] is not None:
            adaptive_ts = graph_config.get_adaptive_timestep(_current_escalation[0])
            if adaptive_ts:
                if verbosity >= 2:
                    print(f"  [adaptive-tempo] escalation={_current_escalation[0]} → timestep={adaptive_ts}")
                timestep = adaptive_ts

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
        if graph_config.has_shocks and random.random() < nature:
            shock = graph_config.select_shock()
            if shock:
                shock_inject = shock
                if verbosity >= 1:
                    print(f"  [shock] {shock['id']}: {shock['trigger'][:80]}...")

        # Build custom query with shock and escalation instructions
        custom_query = None
        if shock_inject or graph_config.has_escalation_tracking:
            parts = []
            if "geopol" in mode:
                parts.append(
                    "Describe these plans being carried out, assuming the "
                    "leaders above issue no further orders."
                )
            else:
                parts.append(
                    f"Weave these plans into a cohesive narrative of what "
                    f"happens in the next {timestep}."
                )

            if shock_inject:
                parts.append(
                    f"\n\nIMPORTANT — an exogenous event occurs during this "
                    f"period that all actors must react to:\n"
                    f"{shock_inject['trigger']}\n"
                    f"Consequences: {shock_inject.get('consequences', '')}"
                )
            elif random.random() < nature:
                parts.append(" Include unexpected consequences.")

            parts.append(graph_config.get_escalation_prompt_suffix())
            custom_query = "".join(parts)

        if custom_query is not None:
            # We handled nature/shocks ourselves — pass nature=0 to avoid double-roll
            output = await narrator.adjudicate(
                history=h, responses=r, nature=0,
                timestep=timestep, mode=mode,
                query=custom_query,
            )
        else:
            # No graph config features active — use default adjudication
            output = await narrator.adjudicate(
                history=h, responses=r, nature=nature,
                timestep=timestep, mode=mode,
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
            # Build a human-readable run name
            run_name = f"{title} — {pool_name or 'custom'} pool"

            actor_names_list = [a["name"] for a in actors] if actors else []

            run_record = PredictionRun(
                scenario_title=title,
                run_name=run_name,
                scenario_hash=scenario_hash,
                pool_name=pool_name or "custom",
                models_used=models_dict,
                moves_total=moves_total,
                timestep=timestep,
                actors=actor_names_list,
                runtime_seconds=runtime_seconds,
                source="geopol-forecaster",
            )
            store.save_run(run_record)

            # Extract structured predictions via LLM
            if verbosity >= 1:
                print("[track] Extracting predictions from assessments...")
            extractor = PredictionExtractor(llm_client=client, model=pool.narrator)
            predictions = await extractor.extract(
                assessments=result["assessments"],
                run_id=run_record.id,
                actor_names=actor_names_list,
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

            # Auto-assess predictions with closed windows from prior runs
            try:
                from .predictions.accuracy import AccuracyAgent
                unassessed = store.get_unassessed()
                if unassessed:
                    if verbosity >= 1:
                        print(f"[assess] Found {len(unassessed)} prior predictions with closed windows — grading...")
                    accuracy_agent = AccuracyAgent(
                        llm_client=client, model=pool.narrator,
                        store=store, verbosity=verbosity,
                    )
                    grades = await accuracy_agent.assess_all()
                    if grades:
                        scored = [g for g in grades if g.score is not None]
                        if scored:
                            avg = sum(g.score for g in scored) / len(scored)
                            print(f"[assess] Graded {len(grades)} predictions. Average score: {avg:.2f}")
                        else:
                            print(f"[assess] Graded {len(grades)} predictions (none yet scorable).")
            except Exception as assess_err:
                if verbosity >= 1:
                    print(f"[assess] Auto-assessment failed: {assess_err}")

        except Exception as e:
            if verbosity >= 1:
                print(f"[track] Prediction tracking failed: {e}")

    # Export predictions to data/ CSVs (synced to HF via GitHub Actions on push)
    if sync_hf and track_predictions:
        try:
            from .predictions.hf_sync import export_predictions_csv
            if verbosity >= 1:
                print("[export] Exporting predictions to data/ CSVs...")
            counts = export_predictions_csv(verbosity=verbosity)
            if verbosity >= 1 and any(counts.values()):
                total = sum(counts.values())
                print(f"[export] Done — {total} rows exported.")
        except Exception as e:
            if verbosity >= 1:
                print(f"[export] CSV export failed: {e}")

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
