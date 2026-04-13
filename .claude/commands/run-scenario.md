Run a geopol simulation with PDF report generation via Modal (cloud backend) or locally in tmux.

$ARGUMENTS format: `<scenario-name> <pool-name> [--local] [extra-flags...]`

Examples:
- `iran-israel-war minimax` — run on Modal (default)
- `iran-war-regional deepseek` — run on Modal with DeepSeek
- `iran-israel-war anthropic --local` — run locally in tmux
- `iran-israel-war openai --local --refs https://example.com/article` — local with ref URL

## Steps

### 1. Parse arguments
- First word: scenario name (required)
- Second word: pool name (required)
- `--local` flag: run locally in tmux instead of Modal
- If either is missing, run `geopol --list-scenarios` and `geopol --list-pools` (or use MCP `list_scenarios`/`list_pools`), then ask the user.

### 2. Log the run
Create a run log entry in `outputs/logs/` with a timestamped filename:
```
outputs/logs/run-<scenario>-<pool>-<YYYYMMDD-HHMMSS>.json
```
Contents: `{"scenario": "...", "pool": "...", "mode": "modal|local", "started": "ISO8601", "call_id": "...", "status": "running"}`

This file persists across sessions so a new Claude instance can pick up where we left off.

### 3a. Modal mode (default)
1. Use `mcp__geopol__run_simulation` with the scenario and pool. Save the returned `call_id` to the log file.
2. Use the Monitor tool to poll status every 30 seconds:
   ```
   while true; do echo "$(date +%H:%M:%S) polling..."; sleep 30; done
   ```
   Set `persistent: true`, description "geopol <scenario> (<pool>) Modal sim".
3. On each Monitor tick, call `mcp__geopol__check_simulation` with the `call_id`.
4. When complete, update the log file with status "completed" and the results.
5. If a PDF was generated, use `mcp__geopol__get_report_url` to get the download link.
6. Report results (assessments, key narrative, PDF link) to the user.

### 3b. Local mode (--local)
1. Check that OPENROUTER_API_KEY is set (warn if not).
2. Check if TAVILY_API_KEY is set (note if SITREP agent will be skipped).
3. Launch in tmux:
   ```
   ./scripts/run-in-tmux.sh geopol-sim /tmp/geopol-sim.log --scenario <name> --pool <pool> --report -v 3 <extra-flags>
   ```
4. Monitor with:
   ```
   tail -f /tmp/geopol-sim.log | grep --line-buffered -E '.'
   ```
   Set `persistent: true`, description "geopol <scenario> (<pool>) local sim".
5. When "SIMULATION COMPLETE" appears, report results and PDF path.

### 4. Error handling
- If the simulation errors, show the full traceback to the user.
- For Modal: the error comes back in the check_simulation response.
- For local: check the log at /tmp/geopol-sim.log.
- Update the run log file with status "error" and the error message.

### 5. Recovery
If the user says a previous run was interrupted, check `outputs/logs/` for the most recent run file with status "running". If found, resume polling with the saved `call_id` (Modal) or reattach to tmux (local).
