from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

from outcome_intelligence.metrics.lifecycle import outcome_score
from outcome_intelligence.models.types import AccuracyMetric, OutcomeLifecycle


class OutcomeEvaluationEngine:
    """Measure prediction quality against recorded outcomes. Does not alter scoring engines."""

    POSITIVE = {
        OutcomeLifecycle.REPLIED.value,
        OutcomeLifecycle.MEETING_SCHEDULED.value,
        OutcomeLifecycle.QUALIFIED.value,
        OutcomeLifecycle.PROPOSAL_SENT.value,
        OutcomeLifecycle.NEGOTIATION.value,
        OutcomeLifecycle.WON.value,
    }

    def opportunity_score_accuracy(self, records: list[dict[str, Any]]) -> list[AccuracyMetric]:
        if not records:
            return []
        errors: list[float] = []
        positives = 0
        for row in records:
            predicted = float(row.get("opportunity_score") or 0.0)
            actual = outcome_score(str(row.get("lifecycle_stage") or "new"))
            errors.append(abs(predicted - actual))
            if str(row.get("lifecycle_stage")) in self.POSITIVE and predicted >= 58:
                positives += 1
            elif str(row.get("lifecycle_stage")) not in self.POSITIVE and predicted < 58:
                positives += 1
        total = max(len(records), 1)
        avg_error = mean(errors) if errors else 0.0
        accuracy = max(0.0, 100.0 - avg_error)
        return [
            AccuracyMetric(
                category="prediction",
                key="opportunity_score",
                sample_size=len(records),
                accuracy_score=round(accuracy, 4),
                precision=round(positives / total * 100.0, 4),
                recall=round(positives / total * 100.0, 4),
                average_prediction_error=round(avg_error, 4),
                details={"threshold": 58.0},
            )
        ]

    def dimension_accuracy(
        self,
        records: list[dict[str, Any]],
        *,
        category: str,
        dimension: str,
    ) -> list[AccuracyMetric]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in records:
            key = str(row.get(dimension) or "unknown")
            grouped[key].append(row)
        metrics: list[AccuracyMetric] = []
        for key, rows in grouped.items():
            positives = sum(1 for row in rows if str(row.get("lifecycle_stage")) in self.POSITIVE)
            errors = [
                abs(float(row.get("opportunity_score") or 0.0) - outcome_score(str(row.get("lifecycle_stage") or "new")))
                for row in rows
            ]
            total = max(len(rows), 1)
            avg_error = mean(errors) if errors else 0.0
            metrics.append(
                AccuracyMetric(
                    category=category,
                    key=key,
                    sample_size=len(rows),
                    accuracy_score=round(max(0.0, 100.0 - avg_error), 4),
                    precision=round(positives / total * 100.0, 4),
                    recall=round(positives / total * 100.0, 4),
                    average_prediction_error=round(avg_error, 4),
                )
            )
        return sorted(metrics, key=lambda item: item.accuracy_score, reverse=True)

    def decision_maker_accuracy(self, records: list[dict[str, Any]]) -> list[AccuracyMetric]:
        evaluated = [row for row in records if row.get("decision_maker_role")]
        if not evaluated:
            return [
                AccuracyMetric(
                    category="decision_maker",
                    key="all",
                    sample_size=0,
                    accuracy_score=0.0,
                    precision=0.0,
                    recall=0.0,
                    average_prediction_error=0.0,
                )
            ]
        # Persona match: positive outcomes where recommended persona equals recorded owner role when present.
        hits = 0
        for row in evaluated:
            stage = str(row.get("lifecycle_stage") or "")
            persona = str(row.get("buyer_persona") or "").lower()
            role = str(row.get("decision_maker_role") or "").lower()
            if stage in self.POSITIVE and persona and (persona in role or role in persona):
                hits += 1
            elif stage in self.POSITIVE and not persona:
                hits += 1
        total = max(len(evaluated), 1)
        score = hits / total * 100.0
        return [
            AccuracyMetric(
                category="decision_maker",
                key="persona_match",
                sample_size=len(evaluated),
                accuracy_score=round(score, 4),
                precision=round(score, 4),
                recall=round(score, 4),
                average_prediction_error=round(100.0 - score, 4),
            )
        ]

    def lead_quality_accuracy(self, records: list[dict[str, Any]]) -> list[AccuracyMetric]:
        if not records:
            return []
        high_intent = [row for row in records if float(row.get("opportunity_score") or 0.0) >= 72]
        converted = [row for row in high_intent if str(row.get("lifecycle_stage")) in self.POSITIVE]
        total = max(len(high_intent), 1)
        precision = len(converted) / total * 100.0
        return [
            AccuracyMetric(
                category="lead_quality",
                key="high_intent_conversion",
                sample_size=len(high_intent),
                accuracy_score=round(precision, 4),
                precision=round(precision, 4),
                recall=round(len(converted) / max(len(records), 1) * 100.0, 4),
                average_prediction_error=round(100.0 - precision, 4),
            )
        ]

    def revenue_recommendation_accuracy(self, records: list[dict[str, Any]]) -> list[AccuracyMetric]:
        evaluated = [row for row in records if row.get("recommended_service")]
        if not evaluated:
            return []
        won = [row for row in evaluated if str(row.get("lifecycle_stage")) == OutcomeLifecycle.WON.value]
        positive = [row for row in evaluated if str(row.get("lifecycle_stage")) in self.POSITIVE]
        total = max(len(evaluated), 1)
        precision = len(positive) / total * 100.0
        win_rate = len(won) / total * 100.0
        return [
            AccuracyMetric(
                category="revenue_recommendation",
                key="recommended_service",
                sample_size=len(evaluated),
                accuracy_score=round((precision + win_rate) / 2.0, 4),
                precision=round(precision, 4),
                recall=round(win_rate, 4),
                average_prediction_error=round(100.0 - precision, 4),
                details={"won": len(won), "positive": len(positive)},
            )
        ]

    def technology_accuracy(self, records: list[dict[str, Any]]) -> list[AccuracyMetric]:
        return self.dimension_accuracy(records, category="technology", dimension="technology")
