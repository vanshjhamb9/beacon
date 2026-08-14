"""Prediction validation — analytics only. Never changes scoring."""

from __future__ import annotations

from typing import Any

from revenue_validation.models.types import BinaryState, PredictionValidation, TriState


class PredictionValidationEngine:
    def record(
        self,
        *,
        company_id: str,
        company: str,
        interested: str = "UNKNOWN",
        decision_maker_correct: str = "UNKNOWN",
        why_now_accurate: str = "UNKNOWN",
        service_accepted: str = "UNKNOWN",
        confidence_realistic: str = "UNKNOWN",
        notes: str | None = None,
    ) -> PredictionValidation:
        return PredictionValidation(
            company_id=company_id,
            company=company,
            interested=TriState(interested),
            decision_maker_correct=TriState(decision_maker_correct),
            why_now_accurate=TriState(why_now_accurate),
            service_accepted=TriState(service_accepted),
            confidence_realistic=BinaryState(confidence_realistic),
            notes=notes,
        )

    def accuracy(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        if not rows:
            return {
                "prediction_accuracy": 0.0,
                "decision_maker_accuracy": 0.0,
                "why_now_accuracy": 0.0,
                "service_accuracy": 0.0,
                "confidence_accuracy": 0.0,
                "coverage": 0.0,
                "n": 0,
            }

        def rate(key: str, *, binary: bool = False) -> float:
            scored = 0
            yes = 0
            for r in rows:
                val = str(r.get(key) or "UNKNOWN")
                if val == "UNKNOWN":
                    continue
                scored += 1
                if binary:
                    yes += 1 if val == "YES" else 0
                else:
                    yes += 1 if val == "YES" else (0.5 if val == "PARTIAL" else 0)
            return round(100.0 * yes / scored, 1) if scored else 0.0

        covered = sum(1 for r in rows if str(r.get("interested") or "UNKNOWN") != "UNKNOWN")
        return {
            "prediction_accuracy": rate("interested"),
            "decision_maker_accuracy": rate("decision_maker_correct"),
            "why_now_accuracy": rate("why_now_accurate"),
            "service_accuracy": rate("service_accepted"),
            "confidence_accuracy": rate("confidence_realistic", binary=True),
            "coverage": round(100.0 * covered / len(rows), 1) if rows else 0.0,
            "n": len(rows),
        }
