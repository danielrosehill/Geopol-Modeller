Run a snowglobe simulation. If $ARGUMENTS is provided, use it as the pool name. Otherwise use the default (deepseek).

Steps:
1. Check that OPENROUTER_API_KEY is set (warn if not)
2. Check if TAVILY_API_KEY is set (note if planning agent will be skipped)
3. Run the simulation using the CLI with `--pool` and `--report` flags:
   - If $ARGUMENTS is a pool name: `snowglobe --pool $ARGUMENTS --report`
   - If no arguments: `snowglobe --pool deepseek --report`
   - If $ARGUMENTS contains extra flags, pass them through
4. Monitor output and report results when complete
5. If a PDF report was generated, tell the user the path
