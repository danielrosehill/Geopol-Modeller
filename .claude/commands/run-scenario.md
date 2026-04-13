Run a geopol simulation using a scenario file. $ARGUMENTS should be in the format: `<scenario-name> [pool-name]`.

Examples:
- `hormuz-blockade-apr2026` — runs with default pool (deepseek)
- `hormuz-blockade-apr2026 anthropic` — runs with anthropic pool

Steps:
1. Parse $ARGUMENTS: first word is the scenario name, second (optional) is the pool name (default: deepseek)
2. Check that OPENROUTER_API_KEY is set (warn if not)
3. Check if TAVILY_API_KEY is set (note if planning agent will be skipped)
4. Verify the scenario exists: `geopol --list-scenarios`
5. Run: `geopol --scenario <name> --pool <pool> --report`
6. Monitor output and report results when complete
7. If a PDF report was generated, tell the user the path
