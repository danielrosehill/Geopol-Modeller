Run a snowglobe simulation sequentially across ALL available model pools, generating a PDF report for each.

Steps:
1. Check that OPENROUTER_API_KEY is set (abort if not)
2. Check if TAVILY_API_KEY is set (note if planning agent will be skipped)
3. Read config/pools.yaml to get the full list of pool names
4. For each pool, run: `snowglobe --pool <name> --report --no-rich -v 0`
5. Collect all PDF report paths
6. Summarize which pools succeeded and which failed, with PDF paths for each
