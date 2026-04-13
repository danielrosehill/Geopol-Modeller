"""Sync the local prediction store to a Hugging Face dataset."""

from __future__ import annotations

import os
from typing import Optional

HF_DATASET_ID = "danielrosehill/Geopol-Forecaster-Predictions"


def sync_to_huggingface(
    db_path: str | None = None,
    dataset_id: str = HF_DATASET_ID,
    token: str | None = None,
    verbosity: int = 1,
) -> dict:
    """Export all runs + predictions from the local SQLite store and push
    to a Hugging Face dataset as Parquet.

    Returns a dict with counts of rows synced per table.
    """
    try:
        from huggingface_hub import HfApi
    except ImportError:
        raise RuntimeError(
            "huggingface_hub is required for HF sync. "
            "Install it with: pip install huggingface_hub"
        )

    from .store import PredictionStore

    store = PredictionStore(db_path=db_path)

    runs = store.get_runs()
    predictions = store.get_predictions()
    # Assessments — reuse the raw query since there's no get_all_assessments
    rows = store._conn.execute(
        "SELECT * FROM assessments ORDER BY assessed_at"
    ).fetchall()
    assessments = [store._row_to_dict(r) for r in rows]

    if not runs and not predictions:
        if verbosity >= 1:
            print("[hf-sync] Nothing to sync — store is empty.")
        return {"runs": 0, "predictions": 0, "assessments": 0}

    # Build CSV content for each table
    import csv
    import io
    import tempfile

    api = HfApi(token=token or os.environ.get("HF_TOKEN"))

    counts = {}

    for name, data in [
        ("runs", runs),
        ("predictions", predictions),
        ("assessments", assessments),
    ]:
        if not data:
            counts[name] = 0
            continue

        # Flatten dict values to JSON strings for CSV compatibility
        import json

        flat_data = []
        for row in data:
            flat = {}
            for k, v in row.items():
                if isinstance(v, (dict, list)):
                    flat[k] = json.dumps(v)
                else:
                    flat[k] = v
            flat_data.append(flat)

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=flat_data[0].keys())
        writer.writeheader()
        writer.writerows(flat_data)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, prefix=f"{name}_"
        ) as f:
            f.write(buf.getvalue())
            tmp_path = f.name

        try:
            api.upload_file(
                path_or_fileobj=tmp_path,
                path_in_repo=f"data/{name}.csv",
                repo_id=dataset_id,
                repo_type="dataset",
                commit_message=f"Sync {name} ({len(flat_data)} rows)",
            )
            counts[name] = len(flat_data)
            if verbosity >= 1:
                print(f"[hf-sync] Pushed {len(flat_data)} {name} rows to {dataset_id}")
        finally:
            os.unlink(tmp_path)

    store.close()
    return counts
