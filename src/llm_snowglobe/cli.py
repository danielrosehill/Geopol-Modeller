#!/usr/bin/env python3

"""Interactive CLI for running snowglobe simulations with model pool selection."""

import asyncio
import os
import sys

from .core.llm import load_pools


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


def select_pool(pools_path):
    """Interactive pool selection menu. Returns (pool_name, pools_dict, base_url)."""
    pools, active, base_url = load_pools(pools_path)

    if not pools:
        print("No pools found in", pools_path)
        sys.exit(1)

    pool_names = list(pools.keys())

    print()
    print("=" * 40)
    print("  SNOWGLOBE — Model Pool Selection")
    print("=" * 40)

    print_pool_table(pools, active)

    while True:
        try:
            choice = input(f"Select pool [1-{len(pools)}, or Enter for '{active}']: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if choice == "":
            return active, pools, base_url

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(pool_names):
                selected = pool_names[idx]
                pool = pools[selected]
                print(f"\n  Selected: {selected}")
                print(f"    Planner:  {pool.planner}")
                print(f"    Narrator: {pool.narrator}")
                print(f"    Player:   {pool.player}")
                print(f"    Advisor:  {pool.advisor}")
                print()
                return selected, pools, base_url
            else:
                print(f"  Please enter a number between 1 and {len(pools)}.")
        except ValueError:
            # Try matching by name
            if choice in pools:
                return choice, pools, base_url
            print(f"  Invalid input. Enter a number or pool name.")


def main():
    """CLI entry point: select pool, then run the Azuristan/Crimsonia simulation."""
    pools_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "pools.yaml")
    # Also check relative to CWD
    if not os.path.exists(pools_path):
        pools_path = os.path.join("config", "pools.yaml")
    if not os.path.exists(pools_path):
        print("Cannot find config/pools.yaml. Run from the snowglobe repo root.")
        sys.exit(1)

    pool_name, pools, base_url = select_pool(pools_path)

    # Import here to avoid circular imports at module level
    from .examples_runner import run_ac_sim
    asyncio.run(run_ac_sim(pool_name=pool_name, pools_path=pools_path))


if __name__ == "__main__":
    main()
