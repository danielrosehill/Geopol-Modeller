"""Automated self-healing analysis — identifies prediction weaknesses and generates improvement recommendations."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field

from .models import GRADE_SCORES
from .store import PredictionStore


@dataclass
class CalibrationBucket:
    """Tracks predicted probability vs. actual score for calibration analysis."""
    predicted_prob_sum: float = 0.0
    actual_score_sum: float = 0.0
    count: int = 0

    @property
    def avg_predicted(self) -> float:
        return self.predicted_prob_sum / self.count if self.count else 0.0

    @property
    def avg_actual(self) -> float:
        return self.actual_score_sum / self.count if self.count else 0.0

    @property
    def calibration_error(self) -> float:
        return abs(self.avg_predicted - self.avg_actual)


@dataclass
class SelfHealReport:
    """Structured output from self-heal analysis."""
    total_runs: int = 0
    total_predictions: int = 0
    total_assessed: int = 0
    overall_avg_score: float | None = None

    # Per-dimension analysis
    by_pool: dict = field(default_factory=dict)
    by_horizon: dict = field(default_factory=dict)
    by_confidence: dict = field(default_factory=dict)
    calibration_buckets: dict = field(default_factory=dict)
    grade_distribution: dict = field(default_factory=dict)

    # Recommendations
    recommendations: list = field(default_factory=list)

    def to_text(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("  SELF-HEALING ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"  Total runs:        {self.total_runs}")
        lines.append(f"  Total predictions: {self.total_predictions}")
        lines.append(f"  Total assessed:    {self.total_assessed}")
        if self.overall_avg_score is not None:
            lines.append(f"  Overall accuracy:  {self.overall_avg_score:.3f}")
        lines.append("")

        if self.grade_distribution:
            lines.append("  Grade distribution:")
            for grade, count in sorted(self.grade_distribution.items()):
                pct = (count / self.total_assessed * 100) if self.total_assessed else 0
                lines.append(f"    {grade:<25} {count:3d}  ({pct:.0f}%)")
            lines.append("")

        if self.by_pool:
            lines.append("  ACCURACY BY MODEL POOL:")
            for pool, stats in sorted(self.by_pool.items(), key=lambda x: x[1].get("avg", 0)):
                lines.append(
                    f"    {pool:<20} avg={stats['avg']:.3f}  n={stats['count']}"
                )
            lines.append("")

        if self.by_horizon:
            lines.append("  ACCURACY BY HORIZON:")
            for horizon, stats in sorted(self.by_horizon.items()):
                lines.append(
                    f"    {horizon:<10} avg={stats['avg']:.3f}  n={stats['count']}"
                )
            lines.append("")

        if self.calibration_buckets:
            lines.append("  CONFIDENCE CALIBRATION:")
            lines.append(f"    {'Bucket':<15} {'Predicted':>10} {'Actual':>10} {'Error':>10}  {'N':>5}")
            for bucket_name, bucket in sorted(self.calibration_buckets.items()):
                lines.append(
                    f"    {bucket_name:<15} {bucket.avg_predicted:>10.2f} "
                    f"{bucket.avg_actual:>10.2f} {bucket.calibration_error:>10.2f}  "
                    f"{bucket.count:>5}"
                )
            lines.append("")

        if self.recommendations:
            lines.append("  RECOMMENDED CHANGES (ranked by expected impact):")
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"    {i}. [{rec['category']}] {rec['summary']}")
                lines.append(f"       Impact: {rec['impact']}")
                if rec.get("file"):
                    lines.append(f"       File: {rec['file']}")
                lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)


def _bucket_probability(prob: float | None) -> str:
    """Assign a probability to a calibration bucket."""
    if prob is None:
        return "unknown"
    if prob < 0.2:
        return "0-20%"
    elif prob < 0.4:
        return "20-40%"
    elif prob < 0.6:
        return "40-60%"
    elif prob < 0.8:
        return "60-80%"
    else:
        return "80-100%"


def analyze(store: PredictionStore) -> SelfHealReport:
    """Run full self-heal analysis across all assessed predictions.

    Returns a SelfHealReport with per-dimension accuracy breakdown
    and ranked improvement recommendations.
    """
    report = SelfHealReport()

    runs = store.get_runs()
    report.total_runs = len(runs)
    report.total_predictions = store.count_predictions()

    # Build run lookup for pool name
    run_pool = {}
    for run in runs:
        run_pool[run["id"]] = run.get("pool_name", "unknown")

    # Get all predictions with their assessments
    all_preds = store.get_predictions()
    assessments_by_pred = {}
    for run in runs:
        run_summary = store.get_accuracy_summary(run_id=run["id"])
        # We need individual assessments — query directly
    rows = store._conn.execute(
        """SELECT p.*, a.grade, a.score AS a_score, a.outcome_summary
           FROM predictions p
           JOIN assessments a ON a.prediction_id = p.id"""
    ).fetchall()

    assessed = [dict(r) for r in rows]
    report.total_assessed = len(assessed)

    if not assessed:
        report.recommendations.append({
            "category": "data",
            "summary": "No assessed predictions found. Run /post-run-analysis first.",
            "impact": "Cannot perform self-healing without graded predictions.",
            "file": None,
        })
        return report

    # Overall accuracy
    scored = [r for r in assessed if r["a_score"] is not None]
    if scored:
        report.overall_avg_score = sum(r["a_score"] for r in scored) / len(scored)

    # Grade distribution
    for r in assessed:
        g = r["grade"]
        report.grade_distribution[g] = report.grade_distribution.get(g, 0) + 1

    # --- By pool ---
    pool_scores = defaultdict(list)
    for r in assessed:
        pool = run_pool.get(r["run_id"], "unknown")
        if r["a_score"] is not None:
            pool_scores[pool].append(r["a_score"])
    for pool, scores in pool_scores.items():
        report.by_pool[pool] = {
            "avg": sum(scores) / len(scores),
            "count": len(scores),
        }

    # --- By horizon ---
    horizon_scores = defaultdict(list)
    for r in assessed:
        h = r.get("horizon") or "none"
        if r["a_score"] is not None:
            horizon_scores[h].append(r["a_score"])
    for horizon, scores in horizon_scores.items():
        report.by_horizon[horizon] = {
            "avg": sum(scores) / len(scores),
            "count": len(scores),
        }

    # --- Confidence calibration ---
    buckets = {}
    for r in assessed:
        bucket_name = _bucket_probability(r.get("probability"))
        if bucket_name not in buckets:
            buckets[bucket_name] = CalibrationBucket()
        b = buckets[bucket_name]
        prob = r.get("probability")
        if prob is not None and r["a_score"] is not None:
            b.predicted_prob_sum += prob
            b.actual_score_sum += r["a_score"]
            b.count += 1
    report.calibration_buckets = buckets

    # --- Generate recommendations ---
    _generate_recommendations(report, assessed, run_pool)

    return report


def _generate_recommendations(report: SelfHealReport, assessed: list, run_pool: dict):
    """Analyze patterns and generate ranked improvement recommendations."""

    # 1. Model pool performance
    if len(report.by_pool) > 1:
        worst_pool = min(report.by_pool.items(), key=lambda x: x[1]["avg"])
        best_pool = max(report.by_pool.items(), key=lambda x: x[1]["avg"])
        if worst_pool[1]["avg"] < best_pool[1]["avg"] - 0.15:
            report.recommendations.append({
                "category": "model",
                "summary": (
                    f"Pool '{worst_pool[0]}' scores {worst_pool[1]['avg']:.2f} vs "
                    f"'{best_pool[0]}' at {best_pool[1]['avg']:.2f}. "
                    f"Consider replacing '{worst_pool[0]}' or adjusting its temperature."
                ),
                "impact": f"~{(best_pool[1]['avg'] - worst_pool[1]['avg']):.0%} accuracy gap",
                "file": "config/pools.yaml",
            })

    # 2. Horizon accuracy decay
    short_horizons = ["24h", "48h", "72h"]
    long_horizons = ["3m", "6m", "1y"]
    short_scores = [
        s for h, data in report.by_horizon.items()
        if h in short_horizons
        for s in [data["avg"]]
    ]
    long_scores = [
        s for h, data in report.by_horizon.items()
        if h in long_horizons
        for s in [data["avg"]]
    ]
    if short_scores and long_scores:
        short_avg = sum(short_scores) / len(short_scores)
        long_avg = sum(long_scores) / len(long_scores)
        if short_avg > long_avg + 0.1:
            report.recommendations.append({
                "category": "horizon",
                "summary": (
                    f"Short-term predictions ({short_avg:.2f}) significantly outperform "
                    f"long-term ({long_avg:.2f}). Consider widening confidence intervals "
                    f"for long horizons or adding calibration instructions to extraction."
                ),
                "impact": f"{short_avg - long_avg:.0%} accuracy decay at longer horizons",
                "file": "src/llm_snowglobe/predictions/extractor.py",
            })

    # 3. Confidence calibration
    overconfident_buckets = []
    for name, bucket in report.calibration_buckets.items():
        if bucket.count >= 3 and bucket.calibration_error > 0.2:
            if bucket.avg_predicted > bucket.avg_actual:
                overconfident_buckets.append((name, bucket))
    if overconfident_buckets:
        worst = max(overconfident_buckets, key=lambda x: x[1].calibration_error)
        report.recommendations.append({
            "category": "calibration",
            "summary": (
                f"Predictions in the {worst[0]} bucket are overconfident: "
                f"predicted {worst[1].avg_predicted:.2f} but scored {worst[1].avg_actual:.2f}. "
                f"Add calibration warning to extraction prompt for high-confidence predictions."
            ),
            "impact": f"Calibration error: {worst[1].calibration_error:.2f}",
            "file": "src/llm_snowglobe/predictions/extractor.py",
        })

    # 4. Extraction quality — check for vague/untestable predictions
    not_testable_count = report.grade_distribution.get("not_yet_testable", 0)
    if report.total_assessed > 0 and not_testable_count / report.total_assessed > 0.3:
        report.recommendations.append({
            "category": "extraction",
            "summary": (
                f"{not_testable_count}/{report.total_assessed} predictions graded "
                f"'not_yet_testable'. Extraction prompt may be generating vague or "
                f"unfalsifiable predictions. Tighten the extraction rules."
            ),
            "impact": "30%+ of predictions are wasted — cannot be scored",
            "file": "src/llm_snowglobe/predictions/extractor.py",
        })

    # 5. Incorrect predictions pattern
    incorrect_count = report.grade_distribution.get("incorrect", 0)
    if report.total_assessed > 0 and incorrect_count / report.total_assessed > 0.3:
        report.recommendations.append({
            "category": "actors",
            "summary": (
                f"{incorrect_count}/{report.total_assessed} predictions scored 'incorrect'. "
                f"Actor personas or the adjudication prompt may be systematically biased. "
                f"Review actor red_lines and constraints for unrealistic assumptions."
            ),
            "impact": f"{incorrect_count / report.total_assessed:.0%} incorrect rate",
            "file": "config/actors/",
        })

    # Sort by impact (rough heuristic: calibration/model first)
    priority = {"model": 0, "calibration": 1, "horizon": 2, "extraction": 3, "actors": 4, "data": 5}
    report.recommendations.sort(key=lambda r: priority.get(r["category"], 99))
