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

    counts = {}

    for name, data in [
        ("runs", runs),
        ("predictions", predictions),
        ("assessments", assessments),
    ]:
        if not data:
            counts[name] = 0
            continue

        flat_data = []
        for row in data:
            flat = {}
            for k, v in row.items():
                if isinstance(v, (dict, list)):
                    flat[k] = json.dumps(v)
                else:
                    flat[k] = v
            flat_data.append(flat)

        csv_path = os.path.join(output_dir, f"{name}.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=flat_data[0].keys())
            writer.writeheader()
            writer.writerows(flat_data)

        counts[name] = len(flat_data)
        if verbosity >= 1:
            print(f"[export] Wrote {len(flat_data)} {name} rows → {csv_path}")

    store.close()
    return counts
