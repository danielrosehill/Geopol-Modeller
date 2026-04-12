Run a backfill of N simulation runs across specified pools to seed the predictions database for analysis.

$ARGUMENTS format: `<scenario-name> [pool1,pool2,...] [count-per-pool]`

Examples:
- `iran-israel-war` — runs once with default pool (deepseek)
- `iran-israel-war deepseek,anthropic` — runs once per pool
- `iran-israel-war deepseek,anthropic,openai 2` — runs twice per pool (6 total)

Steps:

1. **Parse $ARGUMENTS:**
   - First word: scenario name (required)
   - Second word: comma-separated pool names (default: deepseek)
   - Third word: number of runs per pool (default: 1)

2. **Validate inputs:**
   - Verify the scenario exists: `snowglobe --list-scenarios`
   - Verify each pool exists in `config/pools.yaml`
   - Confirm with the user: "This will run N simulations (pools x count). Each takes ~2-5 minutes. Proceed?"

3. **Check API keys:**
   ```bash
   echo "OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:+set}"
   echo "TAVILY_API_KEY: ${TAVILY_API_KEY:+set}"
   ```

4. **Run simulations sequentially:**
   For each pool, for each iteration:
   ```bash
   cd /home/daniel/repos/github/forks/snowglobe
   snowglobe --scenario <name> --pool <pool> --report --rich false
   ```
   Between runs, report progress: "Completed run N/M (pool: X, iteration: Y)"

5. **After all runs complete, show a summary:**
   ```bash
   python3 -c "
   from src.llm_snowglobe.predictions.store import PredictionStore
   store = PredictionStore()
   runs = store.get_runs()
   print(f'Total runs: {len(runs)}')
   for r in runs:
       n = store.count_predictions(run_id=r['id'])
       print(f\"  {r['id'][:8]}  {r['created_at'][:19]}  pool={r['pool_name']:<12}  preds={n}  {r['scenario_title']}\")
   store.close()
   "
   ```

6. **Suggest next steps:**
   - "Run /post-run-analysis to score predictions against real-world outcomes"
   - "Run /self-heal to analyse variance and suggest improvements"
   - "Wait for prediction windows to close before assessing accuracy"

Notes:
- Each run generates a SITREP independently (Tavily search results may vary slightly between runs)
- Runs share the same predictions.db, so cross-pool comparison is built in
- PDF reports are generated for each run (--report flag)
- Checkpoints are saved at each turn if a run is interrupted
- The pipeline_versions table tracks git hash + config for each run, enabling reproducibility auditing
