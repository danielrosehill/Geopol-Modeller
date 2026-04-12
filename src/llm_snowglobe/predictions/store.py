"""SQLite-backed prediction store — separate from the per-session game DB."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from .models import (
    PredictionRun, Prediction, AccuracyGrade, PipelineVersion, GRADE_SCORES,
)


_SCHEMA = """\
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    scenario_title TEXT NOT NULL,
    scenario_hash TEXT,
    pool_name TEXT,
    models_used TEXT,
    runtime_seconds REAL,
    checkpoint_path TEXT,
    report_path TEXT,
    source TEXT DEFAULT 'snowglobe',
    pipeline_version TEXT
);

CREATE TABLE IF NOT EXISTS predictions (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(id),
    prediction_text TEXT NOT NULL,
    probability REAL,
    confidence TEXT,
    horizon TEXT,
    window_opens TEXT,
    window_closes TEXT,
    source_question TEXT,
    raw_answer TEXT,
    lens TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assessments (
    id TEXT PRIMARY KEY,
    prediction_id TEXT NOT NULL REFERENCES predictions(id),
    assessed_at TEXT NOT NULL,
    grade TEXT NOT NULL,
    score REAL,
    outcome_summary TEXT,
    evidence_urls TEXT,
    evidence_text TEXT,
    assessor TEXT DEFAULT 'auto',
    notes TEXT
);

CREATE TABLE IF NOT EXISTS pipeline_versions (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES runs(id),
    recorded_at TEXT NOT NULL,
    git_hash TEXT,
    git_dirty INTEGER DEFAULT 0,
    pools_yaml_hash TEXT,
    scenario_yaml_hash TEXT,
    config_snapshot TEXT
);

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);
"""

_CURRENT_SCHEMA_VERSION = 1


class PredictionStore:
    """SQLite store for prediction runs, predictions, and accuracy grades."""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_dir = os.path.join(os.getcwd(), ".snowglobe_data")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "predictions.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def _create_tables(self):
        self._conn.executescript(_SCHEMA)
        # Check/set schema version
        row = self._conn.execute(
            "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
        ).fetchone()
        if row is None:
            self._conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (_CURRENT_SCHEMA_VERSION,),
            )
            self._conn.commit()

    def close(self):
        self._conn.close()

    # ------------------------------------------------------------------
    # Runs
    # ------------------------------------------------------------------

    def save_run(self, run: PredictionRun) -> str:
        self._conn.execute(
            """INSERT OR REPLACE INTO runs
               (id, created_at, scenario_title, scenario_hash, pool_name,
                models_used, runtime_seconds, checkpoint_path, report_path,
                source, pipeline_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run.id, run.created_at, run.scenario_title, run.scenario_hash,
                run.pool_name, json.dumps(run.models_used) if run.models_used else None,
                run.runtime_seconds, run.checkpoint_path, run.report_path,
                run.source, run.pipeline_version,
            ),
        )
        self._conn.commit()
        return run.id

    def get_runs(self, source: str | None = None) -> list[dict]:
        if source:
            rows = self._conn.execute(
                "SELECT * FROM runs WHERE source = ? ORDER BY created_at DESC", (source,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM runs ORDER BY created_at DESC"
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_run(self, run_id: str) -> dict | None:
        row = self._conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    # ------------------------------------------------------------------
    # Predictions
    # ------------------------------------------------------------------

    def save_prediction(self, pred: Prediction) -> str:
        self._conn.execute(
            """INSERT OR REPLACE INTO predictions
               (id, run_id, prediction_text, probability, confidence, horizon,
                window_opens, window_closes, source_question, raw_answer, lens,
                created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                pred.id, pred.run_id, pred.prediction_text, pred.probability,
                pred.confidence, pred.horizon, pred.window_opens, pred.window_closes,
                pred.source_question, pred.raw_answer, pred.lens, pred.created_at,
            ),
        )
        self._conn.commit()
        return pred.id

    def save_predictions_batch(self, preds: list[Prediction]):
        self._conn.executemany(
            """INSERT OR REPLACE INTO predictions
               (id, run_id, prediction_text, probability, confidence, horizon,
                window_opens, window_closes, source_question, raw_answer, lens,
                created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    p.id, p.run_id, p.prediction_text, p.probability,
                    p.confidence, p.horizon, p.window_opens, p.window_closes,
                    p.source_question, p.raw_answer, p.lens, p.created_at,
                )
                for p in preds
            ],
        )
        self._conn.commit()

    def get_predictions(self, run_id: str | None = None) -> list[dict]:
        if run_id:
            rows = self._conn.execute(
                "SELECT * FROM predictions WHERE run_id = ? ORDER BY created_at",
                (run_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM predictions ORDER BY created_at"
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_unassessed(self, as_of: str | None = None) -> list[dict]:
        """Get predictions with closed windows that have no assessment."""
        if as_of is None:
            as_of = datetime.now(timezone.utc).isoformat()
        rows = self._conn.execute(
            """SELECT p.* FROM predictions p
               LEFT JOIN assessments a ON a.prediction_id = p.id
               WHERE a.id IS NULL
                 AND (p.window_closes IS NULL OR p.window_closes <= ?)
               ORDER BY p.created_at""",
            (as_of,),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def count_predictions(self, run_id: str | None = None) -> int:
        if run_id:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM predictions WHERE run_id = ?", (run_id,)
            ).fetchone()
        else:
            row = self._conn.execute("SELECT COUNT(*) FROM predictions").fetchone()
        return row[0]

    # ------------------------------------------------------------------
    # Assessments
    # ------------------------------------------------------------------

    def save_assessment(self, grade: AccuracyGrade) -> str:
        self._conn.execute(
            """INSERT OR REPLACE INTO assessments
               (id, prediction_id, assessed_at, grade, score,
                outcome_summary, evidence_urls, evidence_text, assessor, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                grade.id, grade.prediction_id, grade.assessed_at, grade.grade,
                grade.score, grade.outcome_summary,
                json.dumps(grade.evidence_urls) if grade.evidence_urls else None,
                grade.evidence_text, grade.assessor, grade.notes,
            ),
        )
        self._conn.commit()
        return grade.id

    def get_accuracy_summary(self, run_id: str | None = None) -> dict:
        """Compute accuracy summary across all or a specific run."""
        if run_id:
            rows = self._conn.execute(
                """SELECT a.grade, a.score FROM assessments a
                   JOIN predictions p ON a.prediction_id = p.id
                   WHERE p.run_id = ?""",
                (run_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT grade, score FROM assessments"
            ).fetchall()

        total = len(rows)
        scored = [r for r in rows if r["score"] is not None]
        grades = {}
        for r in rows:
            g = r["grade"]
            grades[g] = grades.get(g, 0) + 1

        avg_score = (
            sum(r["score"] for r in scored) / len(scored)
            if scored else None
        )

        return {
            "total_assessed": total,
            "total_scored": len(scored),
            "average_score": round(avg_score, 3) if avg_score is not None else None,
            "grade_counts": grades,
        }

    # ------------------------------------------------------------------
    # Pipeline versions
    # ------------------------------------------------------------------

    def save_pipeline_version(self, pv: PipelineVersion) -> str:
        self._conn.execute(
            """INSERT OR REPLACE INTO pipeline_versions
               (id, run_id, recorded_at, git_hash, git_dirty,
                pools_yaml_hash, scenario_yaml_hash, config_snapshot)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                pv.id, pv.run_id, pv.recorded_at, pv.git_hash,
                1 if pv.git_dirty else 0, pv.pools_yaml_hash,
                pv.scenario_yaml_hash,
                json.dumps(pv.config_snapshot) if pv.config_snapshot else None,
            ),
        )
        self._conn.commit()
        return pv.id

    def get_pipeline_versions(self, limit: int = 20) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM pipeline_versions ORDER BY recorded_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        d = dict(row)
        # Deserialize JSON fields
        for key in ("models_used", "evidence_urls", "config_snapshot"):
            if key in d and isinstance(d[key], str):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d
