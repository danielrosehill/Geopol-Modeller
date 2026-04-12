Run a snowglobe simulation. If $ARGUMENTS is provided, use it as the pool name. Otherwise use the default (deepseek).

Steps:
1. Check that OPENROUTER_API_KEY is set (warn if not)
2. Check if TAVILY_API_KEY is set (note if planning agent will be skipped)
3. Run the simulation: `python examples/ac_sim.py $ARGUMENTS`
4. Monitor output and report results when complete
