"""LLM-based structured prediction extraction from free-text assessments."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from ..core.llm import LLMClient
from .models import Prediction, parse_probability, horizon_to_timedelta


EXTRACTION_PROMPT = """\
You are extracting discrete, testable predictions from a geopolitical simulation assessment.

For each prediction, provide:
- prediction_text: A specific, falsifiable claim (one sentence)
- probability: Numeric probability as a decimal 0.0-1.0
- confidence: One of "Low", "Medium", "High", "Very High"
- horizon: Time horizon using one of: 24h, 72h, 1w, 1m, 3m, 6m, 1y
- actor_name: The primary actor/decision-maker this prediction is about (or null if systemic)
- perspective_name: The analytical perspective (e.g. "military", "diplomatic", "economic", "consensus", or null)

{actors_hint}

Return a JSON array. If no extractable predictions exist, return [].

RULES:
- Only extract claims that can be verified against real-world outcomes
- Convert vague language to specific claims where possible
- If the text gives a probability as a percentage, convert to decimal (85% -> 0.85)
- If a range is given (e.g. "70-80%"), use the midpoint
- Ignore meta-commentary and caveats — extract the core prediction

Assessment question: {question}

Assessment answer:
{answer}

Simulation date: {run_date}
"""


class PredictionExtractor:
    """Extracts structured predictions from simulation assessment text."""

    def __init__(self, llm_client: LLMClient, model: str):
        self.llm_client = llm_client
        self.model = model

    async def extract(
        self,
        assessments: list[dict],
        run_id: str,
        run_date: str | None = None,
        actor_names: list[str] | None = None,
    ) -> list[Prediction]:
        """Extract predictions from assessment Q&A pairs.

        Args:
            assessments: List of {"question": str, "answer": str} dicts.
            run_id: The run ID to associate predictions with.
            run_date: ISO date string for the simulation run (for computing windows).
            actor_names: List of actor names in the simulation (for structured extraction).

        Returns:
            List of Prediction objects ready for storage.
        """
        if run_date is None:
            run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        all_predictions = []

        for assessment in assessments:
            question = assessment.get("question", "")
            answer = assessment.get("answer", "")
            if not answer:
                continue

            preds = await self._extract_from_single(
                question=question,
                answer=answer,
                run_id=run_id,
                run_date=run_date,
                actor_names=actor_names,
            )
            all_predictions.extend(preds)

        return all_predictions

    async def _extract_from_single(
        self,
        question: str,
        answer: str,
        run_id: str,
        run_date: str,
        actor_names: list[str] | None = None,
    ) -> list[Prediction]:
        actors_hint = ""
        if actor_names:
            actors_hint = f"Actors in this simulation: {', '.join(actor_names)}\nUse these exact names for actor_name when applicable."

        prompt = EXTRACTION_PROMPT.format(
            question=question,
            answer=answer[:4000],
            run_date=run_date,
            actors_hint=actors_hint,
        )

        response = await self.llm_client.complete(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000,
        )

        predictions = self._parse_response(response, question, answer, run_id, run_date)
        return predictions

    def _parse_response(
        self,
        response: str,
        question: str,
        answer: str,
        run_id: str,
        run_date: str,
    ) -> list[Prediction]:
        # Extract JSON from response (may be wrapped in markdown code fences)
        text = response.strip()
        if text.startswith("```"):
            # Strip code fences
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        try:
            items = json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON array in the response
            import re
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                try:
                    items = json.loads(match.group())
                except json.JSONDecodeError:
                    return []
            else:
                return []

        if not isinstance(items, list):
            return []

        predictions = []
        for item in items:
            if not isinstance(item, dict) or not item.get("prediction_text"):
                continue

            prob = parse_probability(item.get("probability"))
            horizon = item.get("horizon")

            # Compute window dates
            window_opens = run_date
            window_closes = None
            if horizon:
                try:
                    base = datetime.fromisoformat(run_date.replace("Z", "+00:00"))
                except ValueError:
                    base = datetime.now(timezone.utc)
                try:
                    delta = horizon_to_timedelta(horizon)
                    window_closes = (base + delta).isoformat()
                except ValueError:
                    pass

            predictions.append(Prediction(
                run_id=run_id,
                prediction_text=item["prediction_text"],
                probability=prob,
                confidence=item.get("confidence"),
                horizon=horizon,
                window_opens=window_opens,
                window_closes=window_closes,
                source_question=question,
                raw_answer=answer,
                actor_name=item.get("actor_name"),
                perspective_name=item.get("perspective_name"),
            ))

        return predictions
