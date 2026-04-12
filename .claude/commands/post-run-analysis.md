Score the most recent simulation run (or a specified run) for prediction accuracy using the Geopol Forecasts Index rubric.

$ARGUMENTS format: `[run-id]` — optional. If omitted, analyses the most recent run.

Rating schema (from danielrosehill/Geopol-Forecasts-Index):

| Grade | Score | Criteria |
|-------|-------|----------|
| correct | 1.0 | Core prediction matched reality in direction and approximate magnitude/timing |
| largely_correct | 0.75 | Direction right, magnitude or timing off by modest margin |
| partially_correct | 0.5 | General direction right but significantly off on timing/magnitude/mechanism |
| incorrect | 0.0 | Prediction contradicted by what actually happened |
| not_yet_testable | — | Window still open or insufficient data to assess |

Scoring rules:
- Direction is scored first, then adjusted for timing and magnitude
- >2x timing error drops correct to largely_correct or below
- Binary predictions ("X won't happen") scored on the stated claim
- Wire services (Reuters, AP) take precedence over opinion sources for ground truth

Steps:

1. **List available runs:**
   ```bash
   cd /home/daniel/repos/github/forks/snowglobe
   python3 -c "
   from src.llm_snowglobe.predictions.store import PredictionStore
   import json
   store = PredictionStore()
   runs = store.get_runs()
   for r in runs:
       n = store.count_predictions(run_id=r['id'])
       s = store.get_accuracy_summary(run_id=r['id'])
       print(f\"  {r['id'][:8]}  {r['created_at'][:19]}  pool={r['pool_name']:<12}  preds={n}  assessed={s['total_assessed']}  avg={s['average_score'] or 'N/A'}  {r['scenario_title']}\")
   store.close()
   "
   ```

2. **Select the target run:**
   - If $ARGUMENTS contains a run ID (or prefix), use that
   - Otherwise, use the most recent run
   - If no runs exist, tell the user to run a simulation first

3. **Check if TAVILY_API_KEY and OPENROUTER_API_KEY are set.** Both are required for automated assessment. Warn if missing.

4. **Run the accuracy assessment:**
   ```bash
   cd /home/daniel/repos/github/forks/snowglobe
   snowglobe assess --run-id <RUN_ID>
   ```
   This uses the built-in `AccuracyAgent` which:
   - Searches for ground truth via Tavily
   - Grades each prediction using the rubric above
   - Stores results in `.snowglobe_data/predictions.db`

5. **Generate the accuracy report:**
   ```bash
   python3 -c "
   from src.llm_snowglobe.predictions.store import PredictionStore
   from src.llm_snowglobe.predictions.accuracy import AccuracyAgent
   from src.llm_snowglobe.predictions.models import GRADE_SCORES
   import json
   store = PredictionStore()
   run_id = '<RUN_ID>'
   preds = store.get_predictions(run_id=run_id)
   summary = store.get_accuracy_summary(run_id=run_id)
   print(json.dumps({'summary': summary}, indent=2, default=str))
   for p in preds:
       row = store._conn.execute('SELECT * FROM assessments WHERE prediction_id = ?', (p['id'],)).fetchone()
       grade_info = dict(row) if row else None
       print(json.dumps({'prediction': p['prediction_text'][:100], 'prob': p['probability'],
                          'horizon': p['horizon'], 'grade': grade_info}, indent=2, default=str))
   store.close()
   "
   ```

6. **Present a structured scorecard to the user:**

   ```
   === POST-RUN ACCURACY SCORECARD ===

   Run:       [scenario title]
   Date:      [run date]
   Pool:      [pool name]
   Models:    [planner, narrator, player, advisor]

   OVERALL SCORE: X.XX / 1.00

   GRADE BREAKDOWN:
     correct (1.0):           N predictions
     largely_correct (0.75):  N predictions
     partially_correct (0.5): N predictions
     incorrect (0.0):         N predictions
     not_yet_testable:        N predictions

   PREDICTION DETAILS:
   #  | Prediction (truncated)          | Prob  | Horizon | Grade            | Score
   ---|--------------------------------|-------|---------|------------------|------
   1  | Iran will escalate...          | 0.85  | 72h     | correct          | 1.00
   2  | US will impose new sanctions...| 0.70  | 1w      | largely_correct  | 0.75
   ...

   CALIBRATION CHECK:
   - High confidence (>0.8): N/M correct (X%)
   - Medium confidence (0.5-0.8): N/M correct (X%)
   - Low confidence (<0.5): N/M correct (X%)
   ```

7. **If multiple runs exist for the same scenario**, offer a cross-run comparison showing how different pools/models performed on the same scenario.

8. **Suggest next steps:**
   - If accuracy < 0.5: "Consider running /self-heal to diagnose and improve the pipeline"
   - If accuracy > 0.75: "Strong performance. Consider running the same scenario with a different pool for comparison"
   - If many not_yet_testable: "Some prediction windows haven't closed yet. Re-run this analysis after [earliest window_closes date]"
