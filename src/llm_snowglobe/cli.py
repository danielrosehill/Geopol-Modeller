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


def parse_args():
    """Parse CLI arguments for simulation options."""
    parser = argparse.ArgumentParser(
        description="Snowglobe — Multi-agent wargaming simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  snowglobe                              Run with interactive pool selection
  snowglobe --pool anthropic             Run with a specific pool (no menu)
  snowglobe --pool deepseek --report     Run and generate PDF report
  snowglobe --report --podcast           Run and generate PDF + podcast
  snowglobe --refs URL1 URL2             Include reference URLs in briefing
  snowglobe --resume checkpoint.json     Resume from a saved checkpoint
  snowglobe --no-rich -v 0               Minimal output, no Rich formatting
        """,
    )

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

    # Pool selection
    pool_group = parser.add_argument_group("pool selection")
    pool_group.add_argument(
        "--pool", type=str, default=None, metavar="NAME",
        help="Use a named pool from pools.yaml (skips interactive menu)",
    )

    # General
    parser.add_argument(
        "-v", "--verbosity", type=int, default=1,
        help="Verbosity level 0-4 (default: 1)",
    )

    return parser.parse_args()


def main():
    """CLI entry point: select pool, then run the Azuristan/Crimsonia simulation."""
    args = parse_args()

    pools_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "pools.yaml")
    if not os.path.exists(pools_path):
        pools_path = os.path.join("config", "pools.yaml")
    if not os.path.exists(pools_path):
        print("Cannot find config/pools.yaml. Run from the snowglobe repo root.")
        sys.exit(1)

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


if __name__ == "__main__":
    main()
