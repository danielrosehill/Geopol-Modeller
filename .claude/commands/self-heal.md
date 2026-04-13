Analyse previous simulation runs to identify prediction variance and suggest pipeline improvements.

This is a "self-healing experiment" — the goal is to close the gap between what the simulation predicted and what actually happened, then implement approved changes.

Steps:

1. **Load run history from the predictions database:**
   ```bash
   cd /home/daniel/repos/github/forks/geopol
   python3 -c "
   from src.geopol_forecaster.predictions.store import PredictionStore
   import json
   store = PredictionStore()
   runs = store.get_runs()
   for r in runs:
       preds = store.get_predictions(run_id=r['id'])
       summary = store.get_accuracy_summary(run_id=r['id'])
       print(json.dumps({'run': r, 'prediction_count': len(preds), 'accuracy': summary}, indent=2, default=str))
   store.close()
   "
   ```

2. **If no assessed predictions exist**, tell the user they need to run `/post-run-analysis` first to grade predictions before self-healing can begin.

3. **Pull detailed assessment data for each run:**
   ```bash
   python3 -c "
   from src.geopol_forecaster.predictions.store import PredictionStore
   import json
   store = PredictionStore()
   for run in store.get_runs():
       preds = store.get_predictions(run_id=run['id'])
       for p in preds:
           # Get assessment if exists
           row = store._conn.execute(
               'SELECT * FROM assessments WHERE prediction_id = ?', (p['id'],)
           ).fetchone()
           if row:
               p['assessment'] = dict(row)
       print(json.dumps({'run_id': run['id'], 'title': run['scenario_title'],
                          'pool': run['pool_name'], 'predictions': preds}, indent=2, default=str))
   store.close()
   "
   ```

4. **Analyse the variance across these dimensions:**

   a. **Accuracy by pool/model** — Do certain model pools systematically score lower? Recommend swapping underperforming models.

   b. **Accuracy by horizon** — Are short-term (24h, 72h) predictions more accurate than long-term (1m, 3m)? Recommend adjusting confidence calibration or horizon scope.

   c. **Accuracy by actor** — Read the scenario YAML and actor cluster to identify which actors' actions were least predictable. Recommend persona refinements.

   d. **Confidence calibration** — Compare stated probability vs. actual grade. If predictions at 90% are scoring 0.5, the pipeline is overconfident. Recommend adjusting the extraction prompt or adding calibration instructions.

   e. **Nature parameter impact** — Check if runs with high `nature` (unexpected events) scored worse. Recommend tuning the nature value.

   f. **Prediction extraction quality** — Look for predictions that are vague, untestable, or duplicated. Recommend extraction prompt improvements.

5. **Present findings as a structured report:**

   ```
   === SELF-HEALING ANALYSIS ===

   Overall accuracy: X.XX (across N runs, M predictions)

   DIMENSION ANALYSIS:
   - Model performance: [findings]
   - Horizon accuracy: [findings]
   - Actor predictability: [findings]
   - Confidence calibration: [findings]
   - Nature parameter: [findings]
   - Extraction quality: [findings]

   RECOMMENDED CHANGES (ranked by expected impact):
   1. [Change] — Expected improvement: [X]
   2. [Change] — Expected improvement: [X]
   ...
   ```

6. **Ask the user which changes to implement.** Wait for explicit approval before modifying any files.

7. **Implement approved changes.** These may include:
   - Editing `config/pools.yaml` to swap models
   - Editing actor YAML files in `config/actors/` to refine personas, red_lines, constraints
   - Editing scenario YAML files in `config/scenarios/` to adjust nature, timeframes, questions
   - Editing `src/geopol_forecaster/predictions/extractor.py` to improve the extraction prompt
   - Editing `src/geopol_forecaster/predictions/accuracy.py` to refine the grading prompt
   - Adding calibration notes to actor personas

8. **After implementing changes, summarise what was changed and why**, so the next run can be compared against this baseline. Note the git diff for the pipeline_versions changelog.

Important:
- Never implement changes without explicit user approval
- Always show the specific file edits before applying them
- If fewer than 2 assessed runs exist, warn that the analysis may not be statistically meaningful
- Compare across pools when multi-pool data exists — this is the key value of running the same scenario across different model families
