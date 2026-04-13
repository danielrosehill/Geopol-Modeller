Run a Geopol Forecaster wargaming simulation on the Modal cloud backend using the geopol MCP server.

$ARGUMENTS format: `<scenario-name> [pool-name] [ref-urls...]`

Examples:
- `iran-israel-war` — runs with default pool (deepseek)
- `iran-israel-war anthropic` — runs with anthropic pool
- `iran-israel-war deepseek https://example.com/article` — with reference URL

Steps:

1. Parse $ARGUMENTS:
   - First word: scenario name (required, default: iran-israel-war)
   - Second word: pool name (default: deepseek)
   - Remaining words starting with http: reference URLs

2. Use the `list_scenarios` MCP tool to verify the scenario exists.

3. Use the `run_simulation` MCP tool to trigger the simulation:
   - Pass scenario, pool, and reference_urls
   - This returns a call_id

4. Poll with the `check_simulation` MCP tool every 30 seconds using the call_id.
   Report status to the user while waiting.

5. When complete, display the assessments and key narrative points from the result.

6. If a PDF was generated, use `get_report_url` to provide the download link.
