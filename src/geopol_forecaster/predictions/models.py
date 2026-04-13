"""Pydantic models for prediction tracking."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel, Field


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Horizon helpers
# ---------------------------------------------------------------------------

HORIZON_DELTAS = {
    "24h": timedelta(hours=24),
    "48h": timedelta(hours=48),
    "72h": timedelta(hours=72),
    "1w": timedelta(weeks=1),
    "1m": timedelta(days=30),
    "3m": timedelta(days=90),
    "6m": timedelta(days=180),
    "1y": timedelta(days=365),
}


def horizon_to_timedelta(horizon: str) -> timedelta:
    """Map a horizon string like '24h', '1w', '1y' to a timedelta."""
    h = horizon.strip().lower()
    if h in HORIZON_DELTAS:
        return HORIZON_DELTAS[h]
    # Try parsing NNh / NNd patterns
    if h.endswith("h") and h[:-1].isdigit():
        return timedelta(hours=int(h[:-1]))
    if h.endswith("d") and h[:-1].isdigit():
        return timedelta(days=int(h[:-1]))
    if h.endswith("w") and h[:-1].isdigit():
        return timedelta(weeks=int(h[:-1]))
    if h.endswith("m") and h[:-1].isdigit():
        return timedelta(days=int(h[:-1]) * 30)
    if h.endswith("y") and h[:-1].isdigit():
        return timedelta(days=int(h[:-1]) * 365)
    raise ValueError(f"Unknown horizon format: {horizon!r}")


def parse_probability(value: str | float | None) -> float | None:
    """Parse probability from various formats: '85%', '0.85', 85, '70-80%' (midpoint)."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if value <= 1.0 else float(value) / 100.0
    s = str(value).strip().rstrip("%")
    # Range like "70-80"
    if "-" in s:
        parts = s.split("-")
        try:
            lo, hi = float(parts[0].strip()), float(parts[1].strip().rstrip("%"))
            mid = (lo + hi) / 2.0
            return mid / 100.0 if mid > 1.0 else mid
        except (ValueError, IndexError):
            pass
    # "< 1" or "~55"
    s = s.lstrip("<>~≈ ")
    try:
        v = float(s)
        return v / 100.0 if v > 1.0 else v
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class PredictionRun(BaseModel):
    """A single simulation run that produced predictions."""
    id: str = Field(default_factory=_new_id)
    created_at: str = Field(default_factory=_now_iso)
    scenario_title: str
    run_name: Optional[str] = None
    scenario_hash: Optional[str] = None
    pool_name: Optional[str] = None
    models_used: Optional[dict] = None
    runtime_seconds: Optional[float] = None
    checkpoint_path: Optional[str] = None
    report_path: Optional[str] = None
    source: str = "geopol-forecaster"
    pipeline_version: Optional[str] = None


class Prediction(BaseModel):
    """A discrete testable prediction extracted from a simulation run."""
    id: str = Field(default_factory=_new_id)
    run_id: str
    prediction_text: str
    probability: Optional[float] = None
    confidence: Optional[str] = None
    horizon: Optional[str] = None
    window_opens: Optional[str] = None
    window_closes: Optional[str] = None
    source_question: Optional[str] = None
    raw_answer: Optional[str] = None
    lens: Optional[str] = None
    actor_name: Optional[str] = None
    perspective_name: Optional[str] = None
    created_at: str = Field(default_factory=_now_iso)


class AccuracyGrade(BaseModel):
    """An accuracy assessment of a single prediction."""
    id: str = Field(default_factory=_new_id)
    prediction_id: str
    assessed_at: str = Field(default_factory=_now_iso)
    grade: str  # correct, largely_correct, partially_correct, incorrect, not_yet_testable
    score: Optional[float] = None  # 1.0, 0.75, 0.5, 0.0, None
    outcome_summary: Optional[str] = None
    evidence_urls: Optional[list[str]] = None
    evidence_text: Optional[str] = None
    assessor: str = "auto"
    notes: Optional[str] = None


class PipelineVersion(BaseModel):
    """Snapshot of pipeline state at time of a run."""
    id: str = Field(default_factory=_new_id)
    run_id: Optional[str] = None
    recorded_at: str = Field(default_factory=_now_iso)
    git_hash: Optional[str] = None
    git_dirty: bool = False
    pools_yaml_hash: Optional[str] = None
    scenario_yaml_hash: Optional[str] = None
    config_snapshot: Optional[dict] = None


# Grade-to-score mapping
GRADE_SCORES = {
    "correct": 1.0,
    "largely_correct": 0.75,
    "partially_correct": 0.5,
    "incorrect": 0.0,
    "not_yet_testable": None,
}
