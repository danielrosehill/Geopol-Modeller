"""Backfill importer for existing Geopol-Forecasts-Index runs."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

from .models import PredictionRun, Prediction, parse_probability, horizon_to_timedelta
from .store import PredictionStore


# ---------------------------------------------------------------------------
# Horizon normalisation
# ---------------------------------------------------------------------------

_HORIZON_MAP = {
    "24h": "24h", "24 hours": "24h", "+24h": "24h",
    "48h": "48h", "48 hours": "48h", "+48h": "48h",
    "72h": "72h", "72 hours": "72h", "+72h": "72h",
    "1w": "1w", "1 week": "1w", "+1 week": "1w", "1week": "1w",
    "1m": "1m", "1 month": "1m", "+1 month": "1m", "1month": "1m",
    "3m": "3m", "3 months": "3m", "+3 months": "3m",
    "6m": "6m", "6 months": "6m", "+6 months": "6m",
    "1y": "1y", "1 year": "1y", "+1 year": "1y", "1year": "1y",
}


def _normalise_horizon(raw: str) -> str:
    """Normalise a horizon string like '+1 month' to '1m'."""
    key = raw.strip().lower()
    return _HORIZON_MAP.get(key, key)


# ---------------------------------------------------------------------------
# Auto-detect and route
# ---------------------------------------------------------------------------

def backfill_from_repo(store: PredictionStore, repo_path: str, verbosity: int = 1) -> str:
    """Auto-detect format and import a Geopol forecast repo.

    Returns the run_id of the imported run.
    """
    report_dir = os.path.join(repo_path, "report")
    if not os.path.isdir(report_dir):
        raise FileNotFoundError(f"No report/ directory in {repo_path}")

    # Detect format
    has_forecasts_json = os.path.exists(os.path.join(report_dir, "03-forecasts.json"))
    has_chairman = os.path.exists(os.path.join(report_dir, "chairman_report.md"))

    # Extract run date from folder name (e.g. Iran-Israel-Ceasefire-Prediction-090426)
    folder_name = os.path.basename(repo_path.rstrip("/"))
    run_date = _extract_date_from_folder(folder_name)

    # Extract title from README
    title = _extract_title(repo_path) or folder_name

    if has_forecasts_json:
        run_id = _import_forecasts_json(store, repo_path, title, run_date, verbosity)
    elif has_chairman:
        run_id = _import_chairman_report(store, repo_path, title, run_date, verbosity)
    else:
        raise ValueError(f"Unrecognised format in {repo_path} — no 03-forecasts.json or chairman_report.md")

    if verbosity >= 1:
        n = store.count_predictions(run_id=run_id)
        print(f"[backfill] Imported {n} predictions from {folder_name}")

    return run_id


def _extract_date_from_folder(name: str) -> str:
    """Extract a date from folder name like 'Iran-Israel-Ceasefire-Prediction-090426'."""
    # Try DDMMYY suffix
    match = re.search(r'(\d{6})$', name)
    if match:
        ddmmyy = match.group(1)
        try:
            dt = datetime.strptime(ddmmyy, "%d%m%y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Try DDMM suffix (no year, assume 2026)
    match = re.search(r'(\d{4})$', name)
    if match:
        ddmm = match.group(1)
        try:
            dt = datetime.strptime(ddmm + "26", "%d%m%y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _extract_title(repo_path: str) -> str | None:
    """Try to extract a title from the README."""
    readme_path = os.path.join(repo_path, "README.md")
    if not os.path.exists(readme_path):
        return None
    with open(readme_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
    return None


# ---------------------------------------------------------------------------
# Format 1: 03-forecasts.json + 04-summary.json (Run 1)
# ---------------------------------------------------------------------------

def _import_forecasts_json(
    store: PredictionStore,
    repo_path: str,
    title: str,
    run_date: str,
    verbosity: int,
) -> str:
    report_dir = os.path.join(repo_path, "report")

    # Create run
    run = PredictionRun(
        scenario_title=title,
        created_at=run_date + "T00:00:00+00:00",
        source="geopol-import",
    )
    store.save_run(run)

    predictions = []

    # Parse per-lens forecasts
    forecasts_path = os.path.join(report_dir, "03-forecasts.json")
    with open(forecasts_path, "r") as f:
        data = json.load(f)

    for lens_name, lens_data in data.items():
        timeframes = lens_data.get("timeframes", {})
        for horizon_key, tf_data in timeframes.items():
            horizon = _normalise_horizon(horizon_key)
            for pred_obj in tf_data.get("predictions", []):
                text = pred_obj.get("prediction", "")
                if not text:
                    continue

                prob = parse_probability(pred_obj.get("probability"))
                confidence = pred_obj.get("confidence")

                # Compute window
                window_closes = _compute_window_close(run_date, horizon)

                predictions.append(Prediction(
                    run_id=run.id,
                    prediction_text=text,
                    probability=prob,
                    confidence=confidence,
                    horizon=horizon,
                    window_opens=run_date,
                    window_closes=window_closes,
                    lens=lens_name,
                    created_at=run_date + "T00:00:00+00:00",
                ))

    # Parse consensus predictions from 04-summary.json
    summary_path = os.path.join(report_dir, "04-summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, "r") as f:
            summary = json.load(f)

        for pred_obj in summary.get("highConfidencePredictions", []):
            text = pred_obj.get("prediction", "")
            if not text:
                continue
            predictions.append(Prediction(
                run_id=run.id,
                prediction_text=text,
                confidence=pred_obj.get("confidence"),
                lens="consensus",
                created_at=run_date + "T00:00:00+00:00",
            ))

    if predictions:
        store.save_predictions_batch(predictions)

    if verbosity >= 2:
        print(f"[backfill] Run 1 format: {len(predictions)} predictions from {len(data)} lenses")

    return run.id


# ---------------------------------------------------------------------------
# Format 2: chairman_report.md with Key Predictions table (Runs 2 & 3)
# ---------------------------------------------------------------------------

def _import_chairman_report(
    store: PredictionStore,
    repo_path: str,
    title: str,
    run_date: str,
    verbosity: int,
) -> str:
    report_dir = os.path.join(repo_path, "report")

    # Create run
    run = PredictionRun(
        scenario_title=title,
        created_at=run_date + "T00:00:00+00:00",
        source="geopol-import",
    )
    store.save_run(run)

    chairman_path = os.path.join(report_dir, "chairman_report.md")
    with open(chairman_path, "r") as f:
        content = f.read()

    predictions = _parse_predictions_table(content, run.id, run_date)

    if predictions:
        store.save_predictions_batch(predictions)

    if verbosity >= 2:
        print(f"[backfill] Chairman report format: {len(predictions)} predictions")

    return run.id


def _parse_predictions_table(content: str, run_id: str, run_date: str) -> list[Prediction]:
    """Parse a markdown table of predictions from chairman_report.md."""
    predictions = []

    # Find lines that look like table rows (pipe-delimited with content)
    lines = content.split("\n")
    in_table = False
    header_found = False

    for line in lines:
        stripped = line.strip()

        # Look for the Key Predictions heading
        if re.match(r'^##\s+\d+\.?\s+KEY\s+PREDICTIONS', stripped, re.IGNORECASE):
            in_table = True
            header_found = False
            continue

        if not in_table:
            continue

        # Skip if we hit the next heading
        if stripped.startswith("## ") and "KEY PREDICTIONS" not in stripped.upper():
            in_table = False
            continue

        # Skip empty lines
        if not stripped:
            continue

        # Skip non-table lines
        if "|" not in stripped:
            continue

        # Skip separator rows (---|---|---)
        if re.match(r'^\|[\s\-:]+\|', stripped):
            header_found = True
            continue

        # Skip the header row (bold headers)
        if not header_found:
            header_found = "Prediction" in stripped or "prediction" in stripped
            continue

        # Parse table row
        cells = [c.strip() for c in stripped.split("|")]
        # Remove empty first/last from leading/trailing pipes
        cells = [c for c in cells if c]

        if len(cells) < 4:
            continue

        pred_text = cells[0].strip("* ")
        horizon_raw = cells[1].strip("* ")
        prob_raw = cells[2].strip("* ")
        confidence = cells[3].strip("* ")

        if not pred_text or pred_text.lower() == "prediction":
            continue

        horizon = _normalise_horizon(horizon_raw)
        prob = parse_probability(prob_raw)
        window_closes = _compute_window_close(run_date, horizon)

        predictions.append(Prediction(
            run_id=run_id,
            prediction_text=pred_text,
            probability=prob,
            confidence=confidence,
            horizon=horizon,
            window_opens=run_date,
            window_closes=window_closes,
            lens="chairman",
            created_at=run_date + "T00:00:00+00:00",
        ))

    return predictions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_window_close(run_date: str, horizon: str) -> str | None:
    """Compute window_closes from run_date + horizon."""
    try:
        base = datetime.fromisoformat(run_date)
    except ValueError:
        return None
    try:
        delta = horizon_to_timedelta(horizon)
        return (base + delta).isoformat()
    except ValueError:
        return None


def backfill_index(store: PredictionStore, index_path: str, verbosity: int = 1) -> list[str]:
    """Backfill all forecast repos found under an index directory.

    Args:
        store: PredictionStore to write into.
        index_path: Path to the Geopol-Forecasts-Index repo.
        verbosity: Output level.

    Returns:
        List of imported run IDs.
    """
    run_ids = []
    for entry in sorted(os.listdir(index_path)):
        entry_path = os.path.join(index_path, entry)
        report_dir = os.path.join(entry_path, "report")
        if os.path.isdir(entry_path) and os.path.isdir(report_dir):
            try:
                run_id = backfill_from_repo(store, entry_path, verbosity=verbosity)
                run_ids.append(run_id)
            except Exception as e:
                if verbosity >= 1:
                    print(f"[backfill] Skipping {entry}: {e}")
    return run_ids
