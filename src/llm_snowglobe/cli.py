#!/usr/bin/env python3

"""Interactive CLI for running snowglobe simulations with model pool selection."""

import argparse
import asyncio
import os
import sys

from .core.llm import load_pools, ModelPool


def print_pool_table(pools, active):
    """Print a numbered menu of available model pools."""
    print()
    print("  #  Pool              Planner                        Player")
    print("  " + "-" * 78)
    for i, (name, pool) in enumerate(pools.items(), 1):
        marker = " *" if name == active else "  "
        planner = pool.planner[:30].ljust(30)
        player = pool.player[:28]
        print(f" {i:2}. {name:<17} {planner} {player}{marker}")
    print()
    print("  (* = active pool)")
    print()


def print_pool_detail(name, pool):
    """Print all 4 roles for a pool."""
    print(f"\n  Selected: {name}")
    print(f"    Planner:  {pool.planner}")
    print(f"    Narrator: {pool.narrator}")
    print(f"    Player:   {pool.player}")
    print(f"    Advisor:  {pool.advisor}")
    print()


def prompt_model(role, default=None):
    """Prompt user for a model ID for a given role."""
    hint = f" [{default}]" if default else ""
    while True:
        try:
            val = input(f"    {role}{hint}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if val == "" and default:
            return default
        if val:
            return val
        print(f"      Please enter a model ID (e.g. 'deepseek/deepseek-v3.2')")


def build_custom_pool():
    """Interactive builder for a custom model pool."""
    print()
    print("  ----------------------------------------")
    print("  CUSTOM POOL BUILDER")
    print("  ----------------------------------------")
    print()
    print("  Enter an OpenRouter model ID for each role.")
    print("  Browse models: https://openrouter.ai/models")
    print()
    print("  Tip: press Enter to reuse the previous value,")
    print("       or type a single model ID for all 4 roles.")
    print()

    # Ask if they want one model for everything
    try:
        shortcut = input("  Use one model for all roles? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)

    if shortcut in ("y", "yes"):
        model = prompt_model("Model ID")
        pool = ModelPool(planner=model, narrator=model, player=model, advisor=model)
        print_pool_detail("custom", pool)
        return pool

    # Per-role selection
    print()
    planner = prompt_model("Planner  (research + briefing)")
    narrator = prompt_model("Narrator (adjudication)      ", default=planner)
    player = prompt_model("Player   (in-character moves) ", default=planner)
    advisor = prompt_model("Advisor  (human player help)  ", default=player)

    pool = ModelPool(planner=planner, narrator=narrator, player=player, advisor=advisor)
    print_pool_detail("custom", pool)
    return pool


def select_pool(pools_path):
    """Interactive pool selection menu. Returns (pool_name, pool, base_url)."""
    pools, active, base_url = load_pools(pools_path)

    if not pools:
        print("No pools found in", pools_path)
        sys.exit(1)

    pool_names = list(pools.keys())
    n = len(pools)

    print()
    print("=" * 40)
    print("  SNOWGLOBE — Model Pool Selection")
    print("=" * 40)

    print_pool_table(pools, active)

    print(f"  {n + 1}. [Custom] — build your own stack")
    print()

    while True:
        try:
            choice = input(f"  Select pool [1-{n + 1}, or Enter for '{active}']: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if choice == "":
            return active, pools[active], base_url

        # Check for "custom" by name
        if choice.lower() == "custom":
            pool = build_custom_pool()
            return "custom", pool, base_url

        try:
            idx = int(choice) - 1
            if idx == n:
                # Custom option
                pool = build_custom_pool()
                return "custom", pool, base_url
            if 0 <= idx < n:
                selected = pool_names[idx]
                pool = pools[selected]
                print_pool_detail(selected, pool)
                return selected, pool, base_url
            else:
                print(f"  Please enter a number between 1 and {n + 1}.")
        except ValueError:
            if choice in pools:
                return choice, pools[choice], base_url
            print(f"  Invalid input. Enter a number, pool name, or 'custom'.")


def _add_run_args(parser):
    """Add simulation run arguments to a parser (shared between top-level and 'run' subcommand)."""
    # Output features
    output = parser.add_argument_group("output features")
    output.add_argument(
        "--rich", action=argparse.BooleanOptionalAction, default=None,
        help="Rich terminal progress display (default: auto-detect TTY)",
    )
    output.add_argument(
        "--report", action=argparse.BooleanOptionalAction, default=False,
        help="Generate a Typst PDF report after simulation",
    )
    output.add_argument(
        "--podcast", action=argparse.BooleanOptionalAction, default=False,
        help="Generate an edge-tts podcast episode after simulation",
    )
    output.add_argument(
        "--podcast-voice", type=str, default="en-US-GuyNeural",
        metavar="VOICE",
        help="TTS voice for podcast (default: en-US-GuyNeural)",
    )

    # Checkpointing
    ckpt = parser.add_argument_group("checkpointing")
    ckpt.add_argument(
        "--checkpoint", action=argparse.BooleanOptionalAction, default=True,
        help="Save checkpoints after each move (default: on)",
    )
    ckpt.add_argument(
        "--resume", type=str, default=None, metavar="FILE",
        help="Resume simulation from a checkpoint JSON file",
    )

    # Reference inputs
    refs = parser.add_argument_group("reference inputs")
    refs.add_argument(
        "--refs", nargs="+", metavar="URL",
        help="Reference URLs to fetch and include in the briefing context",
    )

    # Scenario selection
    scenario_group = parser.add_argument_group("scenario selection")
    scenario_group.add_argument(
        "--scenario", type=str, default=None, metavar="NAME",
        help="Run a named scenario from config/scenarios/ (e.g. hormuz-blockade-apr2026)",
    )
    scenario_group.add_argument(
        "--list-scenarios", action="store_true", default=False,
        help="List available scenarios and exit",
    )

    # Pool selection
    pool_group = parser.add_argument_group("pool selection")
    pool_group.add_argument(
        "--pool", type=str, default=None, metavar="NAME",
        help="Use a named pool from pools.yaml (skips interactive menu)",
    )

    # Prediction tracking
    track_group = parser.add_argument_group("prediction tracking")
    track_group.add_argument(
        "--track", action=argparse.BooleanOptionalAction, default=True,
        help="Extract and store predictions after simulation (default: on)",
    )

    # General
    parser.add_argument(
        "-v", "--verbosity", type=int, default=1,
        help="Verbosity level 0-4 (default: 1)",
    )


def parse_args():
    """Parse CLI arguments for simulation options."""
    parser = argparse.ArgumentParser(
        description="Snowglobe — Multi-agent wargaming simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  snowglobe                              Run default scenario with pool menu
  snowglobe --scenario hormuz-blockade-apr2026
                                         Run a named scenario
  snowglobe --pool anthropic             Run with a specific pool (no menu)
  snowglobe --pool deepseek --report     Run and generate PDF report
  snowglobe assess                       Run accuracy assessment on predictions
  snowglobe predictions list             List tracked predictions
  snowglobe predictions summary          Show accuracy summary
  snowglobe predictions import PATH      Import from a Geopol forecast repo
  snowglobe changelog                    Show pipeline version history
        """,
    )

    subparsers = parser.add_subparsers(dest="command")

    # --- 'run' subcommand (explicit) ---
    run_parser = subparsers.add_parser("run", help="Run a simulation")
    _add_run_args(run_parser)

    # --- 'assess' subcommand ---
    assess_parser = subparsers.add_parser("assess", help="Run accuracy assessment")
    assess_parser.add_argument(
        "--run-id", type=str, default=None,
        help="Assess predictions from a specific run",
    )
    assess_parser.add_argument(
        "--all", action="store_true", default=False,
        help="Assess all unassessed predictions with closed windows",
    )
    assess_parser.add_argument(
        "--dry-run", action="store_true", default=False,
        help="Show what would be assessed without making changes",
    )
    assess_parser.add_argument(
        "--pool", type=str, default=None, metavar="NAME",
        help="Model pool to use for assessment LLM calls",
    )
    assess_parser.add_argument(
        "-v", "--verbosity", type=int, default=1,
        help="Verbosity level 0-4 (default: 1)",
    )

    # --- 'predictions' subcommand ---
    pred_parser = subparsers.add_parser("predictions", help="Manage predictions")
    pred_sub = pred_parser.add_subparsers(dest="pred_command")

    pred_list = pred_sub.add_parser("list", help="List tracked predictions")
    pred_list.add_argument("--run-id", type=str, default=None,
                           help="Filter by run ID")
    pred_list.add_argument("--limit", type=int, default=50,
                           help="Max predictions to show")

    pred_summary = pred_sub.add_parser("summary", help="Show accuracy summary")
    pred_summary.add_argument("--run-id", type=str, default=None,
                              help="Summary for a specific run")

    pred_import = pred_sub.add_parser("import", help="Import from a Geopol forecast repo")
    pred_import.add_argument("path", type=str,
                             help="Path to forecast repo or index directory")
    pred_import.add_argument("--index", action="store_true", default=False,
                             help="Treat path as an index directory (import all sub-repos)")
    pred_import.add_argument("-v", "--verbosity", type=int, default=1)

    # --- 'changelog' subcommand ---
    cl_parser = subparsers.add_parser("changelog", help="Pipeline changelog")
    cl_parser.add_argument("--limit", type=int, default=20,
                           help="Number of entries to show")

    # --- Add run args to top-level parser for backward compat ---
    _add_run_args(parser)

    return parser.parse_args()


def find_config_dir():
    """Locate the config/ directory."""
    # Try relative to source
    src_relative = os.path.join(os.path.dirname(__file__), "..", "..", "config")
    if os.path.isdir(src_relative):
        return os.path.abspath(src_relative)
    # Try CWD
    if os.path.isdir("config"):
        return os.path.abspath("config")
    return None


def list_scenarios(config_dir):
    """Print available scenarios from config/scenarios/."""
    scenarios_dir = os.path.join(config_dir, "scenarios")
    if not os.path.isdir(scenarios_dir):
        print("No scenarios directory found.")
        return

    from ruamel.yaml import YAML
    yaml = YAML(typ="safe")

    print()
    print("  Available scenarios:")
    print("  " + "-" * 60)
    for f in sorted(os.listdir(scenarios_dir)):
        if f.endswith(".yaml") or f.endswith(".yml"):
            name = f.rsplit(".", 1)[0]
            try:
                with open(os.path.join(scenarios_dir, f)) as fh:
                    data = yaml.load(fh)
                title = data.get("title", "")
                actors = data.get("actor_cluster", "inline")
                # Resolve timeframe display
                if data.get("timeframes"):
                    tf = " → ".join(data["timeframes"])
                elif data.get("timeframe_preset"):
                    tf = f"preset:{data['timeframe_preset']}"
                else:
                    moves = data.get("moves", "?")
                    ts = data.get("timestep", "?")
                    tf = f"{moves}×{ts}"
                print(f"  {name:<35} {title}")
                print(f"  {'':35} actors: {actors}, {tf}")
            except Exception:
                print(f"  {name:<35} (error reading file)")
    print()


def _run_simulation(args, config_dir, pools_path):
    """Handle simulation run (default command and 'run' subcommand)."""
    # List scenarios and exit
    if getattr(args, "list_scenarios", False):
        list_scenarios(config_dir)
        sys.exit(0)

    # Pool selection
    pools_data, active, base_url = load_pools(pools_path)

    if args.pool:
        if args.pool not in pools_data:
            print(f"Unknown pool '{args.pool}'. Available: {', '.join(pools_data.keys())}")
            sys.exit(1)
        pool_name = args.pool
        pool = pools_data[pool_name]
        print(f"  Using pool: {pool_name}")
    else:
        pool_name, pool, base_url = select_pool(pools_path)

    # Scenario mode vs legacy mode
    if args.scenario:
        # Resolve scenario file
        scenario_path = os.path.join(config_dir, "scenarios", f"{args.scenario}.yaml")
        if not os.path.exists(scenario_path):
            scenario_path = os.path.join(config_dir, "scenarios", f"{args.scenario}.yml")
        if not os.path.exists(scenario_path):
            scenario_path = args.scenario
        if not os.path.exists(scenario_path):
            print(f"Scenario not found: {args.scenario}")
            print("Use --list-scenarios to see available scenarios.")
            sys.exit(1)

        from .scenario_runner import run_scenario
        asyncio.run(run_scenario(
            scenario_path=scenario_path,
            pool_name=pool_name,
            pool_override=pool,
            base_url=base_url,
            pools_path=pools_path,
            verbosity=args.verbosity,
            use_rich=args.rich,
            checkpoint=args.checkpoint,
            resume_path=args.resume,
            report=args.report,
            podcast=args.podcast,
            podcast_voice=args.podcast_voice,
            reference_urls=args.refs,
            track_predictions=getattr(args, "track", True),
        ))
    else:
        from .examples_runner import run_ac_sim
        asyncio.run(run_ac_sim(
            pool_name=pool_name,
            pool_override=pool,
            base_url=base_url,
            pools_path=pools_path,
            verbosity=args.verbosity,
            use_rich=args.rich,
            checkpoint=args.checkpoint,
            resume_path=args.resume,
            report=args.report,
            podcast=args.podcast,
            podcast_voice=args.podcast_voice,
            reference_urls=args.refs,
        ))


def _run_assess(args, config_dir, pools_path):
    """Handle the 'assess' subcommand."""
    from .predictions import PredictionStore, AccuracyAgent
    from .core.llm import LLMClient, load_pools as _load_pools

    store = PredictionStore()

    if args.dry_run:
        unassessed = store.get_unassessed()
        if not unassessed:
            print("No unassessed predictions with closed windows.")
            return
        print(f"Found {len(unassessed)} predictions to assess:\n")
        for p in unassessed:
            short = p["prediction_text"][:70] + ("..." if len(p["prediction_text"]) > 70 else "")
            print(f"  [{p['id'][:8]}] {short}")
            print(f"           horizon={p.get('horizon', '?')}  window_closes={p.get('window_closes', '?')}")
        return

    # Need an LLM client for grading
    pools_data, active, base_url = _load_pools(pools_path)
    pool_name = args.pool or active
    pool = pools_data.get(pool_name)
    if not pool:
        print(f"Unknown pool '{pool_name}'.")
        sys.exit(1)

    client = LLMClient(base_url=base_url)
    agent = AccuracyAgent(
        llm_client=client, model=pool.narrator,
        store=store, verbosity=args.verbosity,
    )

    asyncio.run(agent.assess_all())
    print()
    print(agent.summary_report(run_id=args.run_id))


def _run_predictions(args):
    """Handle the 'predictions' subcommand."""
    from .predictions import PredictionStore, AccuracyAgent

    store = PredictionStore()

    if args.pred_command == "list":
        preds = store.get_predictions(run_id=args.run_id)
        if not preds:
            print("No predictions found.")
            return
        preds = preds[:args.limit]
        print(f"\n  Showing {len(preds)} predictions:\n")
        for p in preds:
            prob_str = f"{p['probability']:.0%}" if p.get("probability") is not None else "N/A"
            short = p["prediction_text"][:65] + ("..." if len(p["prediction_text"]) > 65 else "")
            print(f"  [{p['id'][:8]}] {short}")
            print(f"           prob={prob_str}  horizon={p.get('horizon', '?')}  "
                  f"lens={p.get('lens', '?')}  window_closes={p.get('window_closes', '?')}")
        print()

    elif args.pred_command == "summary":
        # Use a lightweight agent just for the report
        agent = AccuracyAgent.__new__(AccuracyAgent)
        agent.store = store
        print(agent.summary_report(run_id=args.run_id))

    elif args.pred_command == "import":
        from .predictions.backfill import backfill_from_repo, backfill_index

        path = os.path.abspath(args.path)
        verbosity = getattr(args, "verbosity", 1)

        if args.index:
            run_ids = backfill_index(store, path, verbosity=verbosity)
            print(f"\n[import] Imported {len(run_ids)} runs.")
        else:
            run_id = backfill_from_repo(store, path, verbosity=verbosity)
            n = store.count_predictions(run_id=run_id)
            print(f"\n[import] Run {run_id}: {n} predictions imported.")

    else:
        print("Usage: snowglobe predictions {list|summary|import}")
        sys.exit(1)


def _run_changelog(args):
    """Handle the 'changelog' subcommand."""
    from .predictions.store import PredictionStore
    from .predictions.changelog import get_changelog

    store = PredictionStore()
    print(get_changelog(store, limit=args.limit))


def main():
    """CLI entry point: select pool and scenario, then run simulation."""
    args = parse_args()

    # Subcommand dispatch
    if args.command == "assess":
        config_dir = find_config_dir()
        pools_path = os.path.join(config_dir, "pools.yaml") if config_dir else None
        _run_assess(args, config_dir, pools_path)
        return

    if args.command == "predictions":
        _run_predictions(args)
        return

    if args.command == "changelog":
        _run_changelog(args)
        return

    # Default: run simulation (either 'run' subcommand or no subcommand)
    config_dir = find_config_dir()
    if config_dir is None:
        print("Cannot find config/ directory. Run from the snowglobe repo root.")
        sys.exit(1)

    pools_path = os.path.join(config_dir, "pools.yaml")
    if not os.path.exists(pools_path):
        print("Cannot find config/pools.yaml.")
        sys.exit(1)

    _run_simulation(args, config_dir, pools_path)


if __name__ == "__main__":
    main()
