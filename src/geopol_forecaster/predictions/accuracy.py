"""Accuracy assessment agent — searches for ground truth and grades predictions."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from ..core.llm import LLMClient
from .models import AccuracyGrade, GRADE_SCORES
from .store import PredictionStore


GRADING_PROMPT = """\
You are grading a geopolitical prediction against real-world outcomes.

PREDICTION: {prediction_text}
PROBABILITY ASSIGNED: {probability}
CONFIDENCE: {confidence}
HORIZON: {horizon}
WINDOW: {window_opens} to {window_closes}

SEARCH RESULTS (ground truth):
{search_results}

RUBRIC:
- correct (1.0): Core prediction matched reality in direction and approximate magnitude/timing
- largely_correct (0.75): Direction right, magnitude or timing off by modest margin
- partially_correct (0.5): General direction right but significantly off on timing/magnitude/mechanism
- incorrect (0.0): Prediction contradicted by what actually happened
- not_yet_testable: Insufficient data to assess, or window hasn't fully closed

Respond with a JSON object:
{{"grade": "...", "score": ..., "outcome_summary": "one sentence describing what actually happened", "reasoning": "brief explanation of the grade"}}
"""


class AccuracyAgent:
    """Searches for ground truth and grades predictions against outcomes."""

    def __init__(
        self,
        llm_client: LLMClient,
        model: str,
        tavily_api_key: str | None = None,
        store: PredictionStore | None = None,
        verbosity: int = 1,
    ):
        self.llm_client = llm_client
        self.model = model
        self.tavily_api_key = tavily_api_key or os.environ.get("TAVILY_API_KEY")
        self.store = store
        self.verbosity = verbosity

    async def assess_all(self, as_of: str | None = None) -> list[AccuracyGrade]:
        """Assess all unassessed predictions with closed windows."""
        if not self.store:
            raise ValueError("PredictionStore required for assess_all")

        unassessed = self.store.get_unassessed(as_of=as_of)
        if not unassessed:
            if self.verbosity >= 1:
                print("[assess] No unassessed predictions with closed windows.")
            return []

        if self.verbosity >= 1:
            print(f"[assess] Found {len(unassessed)} predictions to assess.")

        grades = []
        for pred in unassessed:
            grade = await self.assess_single_dict(pred)
            if grade:
                self.store.save_assessment(grade)
                grades.append(grade)

        if self.verbosity >= 1:
            scored = [g for g in grades if g.score is not None]
            if scored:
                avg = sum(g.score for g in scored) / len(scored)
                print(f"[assess] Assessed {len(grades)} predictions. Average score: {avg:.2f}")
            else:
                print(f"[assess] Assessed {len(grades)} predictions (none scored).")

        return grades

    async def assess_single(self, prediction_id: str) -> AccuracyGrade | None:
        """Assess a single prediction by ID."""
        if not self.store:
            raise ValueError("PredictionStore required")

        preds = self.store.get_predictions()
        pred = next((p for p in preds if p["id"] == prediction_id), None)
        if not pred:
            if self.verbosity >= 1:
                print(f"[assess] Prediction {prediction_id} not found.")
            return None

        grade = await self.assess_single_dict(pred)
        if grade and self.store:
            self.store.save_assessment(grade)
        return grade

    async def assess_single_dict(self, pred: dict) -> AccuracyGrade | None:
        """Assess a prediction from its dict representation."""
        prediction_text = pred["prediction_text"]

        if self.verbosity >= 1:
            short = prediction_text[:80] + ("..." if len(prediction_text) > 80 else "")
            print(f"[assess] Grading: {short}")

        # Search for ground truth
        search_results = await self._search_ground_truth(prediction_text)
        if not search_results:
            return AccuracyGrade(
                prediction_id=pred["id"],
                grade="not_yet_testable",
                score=None,
                outcome_summary="Insufficient search results to assess.",
                assessor="auto",
            )

        # Grade via LLM
        prompt = GRADING_PROMPT.format(
            prediction_text=prediction_text,
            probability=pred.get("probability", "N/A"),
            confidence=pred.get("confidence", "N/A"),
            horizon=pred.get("horizon", "N/A"),
            window_opens=pred.get("window_opens", "N/A"),
            window_closes=pred.get("window_closes", "N/A"),
            search_results=search_results["text"][:6000],
        )

        response = await self.llm_client.complete(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )

        return self._parse_grade(response, pred["id"], search_results.get("urls", []))

    async def _search_ground_truth(self, prediction_text: str) -> dict | None:
        """Search for real-world outcomes using Tavily."""
        if not self.tavily_api_key:
            if self.verbosity >= 1:
                print("[assess] No TAVILY_API_KEY — cannot search for ground truth.")
            return None

        try:
            from tavily import AsyncTavilyClient
        except ImportError:
            if self.verbosity >= 1:
                print("[assess] tavily-python not installed.")
            return None

        client = AsyncTavilyClient(api_key=self.tavily_api_key)

        # Generate a targeted search query
        query_prompt = (
            f"Generate a single concise web search query to find out whether "
            f"this prediction came true:\n\n{prediction_text}\n\n"
            f"Return only the search query, nothing else."
        )
        query = await self.llm_client.complete(
            model=self.model,
            messages=[{"role": "user", "content": query_prompt}],
            temperature=0.1,
            max_tokens=100,
        )
        query = query.strip().strip('"')

        if self.verbosity >= 2:
            print(f"[assess] Search query: {query}")

        try:
            response = await client.search(query, max_results=5)
            results = response.get("results", [])
            if not results:
                return None

            texts = []
            urls = []
            for r in results:
                title = r.get("title", "")
                content = r.get("content", "")
                url = r.get("url", "")
                texts.append(f"**{title}**\n{content}")
                if url:
                    urls.append(url)

            return {"text": "\n\n---\n\n".join(texts), "urls": urls}

        except Exception as e:
            if self.verbosity >= 1:
                print(f"[assess] Search failed: {e}")
            return None

    def _parse_grade(
        self, response: str, prediction_id: str, evidence_urls: list[str]
    ) -> AccuracyGrade:
        """Parse the LLM grading response into an AccuracyGrade."""
        import json as _json
        import re

        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        try:
            data = _json.loads(text)
        except _json.JSONDecodeError:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    data = _json.loads(match.group())
                except _json.JSONDecodeError:
                    data = {}
            else:
                data = {}

        grade_str = data.get("grade", "not_yet_testable")
        if grade_str not in GRADE_SCORES:
            grade_str = "not_yet_testable"

        score = GRADE_SCORES.get(grade_str)

        return AccuracyGrade(
            prediction_id=prediction_id,
            grade=grade_str,
            score=score,
            outcome_summary=data.get("outcome_summary", ""),
            evidence_urls=evidence_urls or None,
            evidence_text=data.get("reasoning", ""),
            assessor="auto",
        )

    def summary_report(self, run_id: str | None = None) -> str:
        """Generate a formatted accuracy summary."""
        if not self.store:
            return "No store available."

        summary = self.store.get_accuracy_summary(run_id=run_id)
        runs = self.store.get_runs()
        total_preds = self.store.count_predictions(run_id=run_id)

        lines = []
        lines.append("=" * 50)
        lines.append("  PREDICTION ACCURACY SUMMARY")
        lines.append("=" * 50)
        lines.append("")

        if run_id:
            run = self.store.get_run(run_id)
            if run:
                lines.append(f"  Run:      {run['scenario_title']}")
                lines.append(f"  Date:     {run['created_at']}")
                lines.append(f"  Source:   {run['source']}")
                lines.append("")

        lines.append(f"  Total predictions:  {total_preds}")
        lines.append(f"  Total assessed:     {summary['total_assessed']}")
        lines.append(f"  Total scored:       {summary['total_scored']}")
        if summary["average_score"] is not None:
            lines.append(f"  Average score:      {summary['average_score']:.3f}")
        lines.append("")

        if summary["grade_counts"]:
            lines.append("  Grade breakdown:")
            for grade, count in sorted(summary["grade_counts"].items()):
                score = GRADE_SCORES.get(grade, "?")
                lines.append(f"    {grade:<25} {count:3d}  (score: {score})")
            lines.append("")

        if not run_id and len(runs) > 1:
            lines.append("  Per-run breakdown:")
            for run in runs:
                run_summary = self.store.get_accuracy_summary(run_id=run["id"])
                n = run_summary["total_scored"]
                avg = run_summary["average_score"]
                avg_str = f"{avg:.3f}" if avg is not None else "N/A"
                lines.append(
                    f"    {run['scenario_title'][:35]:<35}  "
                    f"scored={n}  avg={avg_str}"
                )
            lines.append("")

        lines.append("=" * 50)
        return "\n".join(lines)
