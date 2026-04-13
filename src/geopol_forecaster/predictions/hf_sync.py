"""Export prediction data to CSV files in the data/ directory.

These CSVs are committed to git and synced to the Hugging Face dataset
(danielrosehill/Geopol-Forecaster-Predictions) via GitHub Actions on push.
"""

from __future__ import annotations

import csv
import json
import os


def export_predictions_csv(
    db_path: str | None = None,
    output_dir: str | None = None,
    verbosity: int = 1,
) -> dict:
    """Export all runs, predictions, and assessments from the local SQLite
    store to CSV files in the data/ directory.

    Predictions are denormalized with run metadata (run_name, pool_name,
    models_used) for easier analysis.

    Returns a dict with counts of rows exported per table.
    """
    from .store import PredictionStore

    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(output_dir, exist_ok=True)

    store = PredictionStore(db_path=db_path)

    runs = store.get_runs()
    predictions = store.get_predictions()
    rows = store._conn.execute(
        "SELECT * FROM assessments ORDER BY assessed_at"
    ).fetchall()
    assessments = [store._row_to_dict(r) for r in rows]

    if not runs and not predictions:
        if verbosity >= 1:
            print("[export] Nothing to export — store is empty.")
        return {"runs": 0, "predictions": 0, "assessments": 0}

    # Build run lookup for denormalization
    run_lookup = {r["id"]: r for r in runs}

    counts = {}

    # --- Runs CSV ---
    if runs:
        _write_csv(os.path.join(output_dir, "runs.csv"), runs, verbosity, "runs")
        counts["runs"] = len(runs)
    else:
        counts["runs"] = 0

    # --- Predictions CSV (denormalized with run metadata) ---
    if predictions:
        enriched = []
        for p in predictions:
            run = run_lookup.get(p["run_id"], {})
            row = {**p}
            row["run_name"] = run.get("run_name") or run.get("scenario_title", "")
            row["pool_name"] = run.get("pool_name", "")
            row["models_used"] = json.dumps(run["models_used"]) if isinstance(run.get("models_used"), dict) else (run.get("models_used") or "")
            enriched.append(row)
        _write_csv(os.path.join(output_dir, "predictions.csv"), enriched, verbosity, "predictions")
        counts["predictions"] = len(enriched)
    else:
        counts["predictions"] = 0

    # --- Assessments CSV (denormalized with prediction + run metadata) ---
    if assessments:
        pred_lookup = {p["id"]: p for p in predictions}
        enriched_assessments = []
        for a in assessments:
            pred = pred_lookup.get(a["prediction_id"], {})
            run = run_lookup.get(pred.get("run_id", ""), {})
            row = {**a}
            row["prediction_text"] = pred.get("prediction_text", "")
            row["probability"] = pred.get("probability")
            row["horizon"] = pred.get("horizon", "")
            row["run_name"] = run.get("run_name") or run.get("scenario_title", "")
            row["pool_name"] = run.get("pool_name", "")
            enriched_assessments.append(row)
        _write_csv(os.path.join(output_dir, "assessments.csv"), enriched_assessments, verbosity, "assessments")
        counts["assessments"] = len(enriched_assessments)
    else:
        counts["assessments"] = 0

    store.close()
    return counts


def _write_csv(path: str, data: list[dict], verbosity: int, label: str):
    """Write a list of dicts to a CSV file."""
    flat_data = []
    for row in data:
        flat = {}
        for k, v in row.items():
            if isinstance(v, (dict, list)):
                flat[k] = json.dumps(v)
            else:
                flat[k] = v
        flat_data.append(flat)

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=flat_data[0].keys())
        writer.writeheader()
        writer.writerows(flat_data)

    if verbosity >= 1:
        print(f"[export] Wrote {len(flat_data)} {label} rows → {path}")
