from statistics import mean

from intelligence_improvement.models.types import (
    FeedbackSignal,
    ImprovementArea,
    PerformanceMetric,
    PredictionEvaluation,
    RulePerformanceMetric,
)


class EvaluationEngine:
    POSITIVE_OUTCOMES = {"accepted", "correct", "won", "meeting_booked", "proposal_sent", "true_positive"}
    NEGATIVE_OUTCOMES = {"rejected", "incorrect", "lost", "false_positive"}

    def collector_performance(self, signals: list[FeedbackSignal]) -> list[PerformanceMetric]:
        return self._grouped_performance(signals, ImprovementArea.COLLECTOR)

    def recommendation_accuracy(self, signals: list[FeedbackSignal]) -> PerformanceMetric:
        matching = [signal for signal in signals if signal.area == ImprovementArea.RECOMMENDATION]
        return self._metric(ImprovementArea.RECOMMENDATION, "recommendations", matching)

    def rule_performance(self, signals: list[FeedbackSignal], *, rule_type: str) -> list[RulePerformanceMetric]:
        grouped: dict[str, list[FeedbackSignal]] = {}
        for signal in signals:
            grouped.setdefault(signal.entity_key, []).append(signal)
        metrics: list[RulePerformanceMetric] = []
        for rule_key, rows in grouped.items():
            correct = sum(1 for row in rows if row.outcome in self.POSITIVE_OUTCOMES)
            incorrect = sum(1 for row in rows if row.outcome in self.NEGATIVE_OUTCOMES)
            overrides = sum(1 for row in rows if row.details.get("overridden") is True)
            total = max(len(rows), 1)
            metrics.append(
                RulePerformanceMetric(
                    rule_key=rule_key,
                    rule_type=rule_type,
                    times_fired=len(rows),
                    correct_decisions=correct,
                    incorrect_decisions=incorrect,
                    override_rate=round(overrides / total * 100.0, 4),
                    confidence=round(correct / total * 100.0, 4),
                    historical_trend=[{"outcome": row.outcome, "score": row.score} for row in rows[-20:]],
                )
            )
        return sorted(metrics, key=lambda metric: metric.confidence, reverse=True)

    def prediction_errors(self, predictions: list[PredictionEvaluation]) -> dict[str, float | int]:
        if not predictions:
            return {"evaluated_predictions": 0, "average_prediction_error": 0.0}
        return {
            "evaluated_predictions": len(predictions),
            "average_prediction_error": round(mean(abs(item.prediction_error) for item in predictions), 4),
        }

    def _grouped_performance(self, signals: list[FeedbackSignal], area: ImprovementArea) -> list[PerformanceMetric]:
        grouped: dict[str, list[FeedbackSignal]] = {}
        for signal in signals:
            if signal.area == area:
                grouped.setdefault(signal.entity_key, []).append(signal)
        return sorted(
            [self._metric(area, key, rows) for key, rows in grouped.items()],
            key=lambda metric: (metric.conversion_rate, metric.precision),
            reverse=True,
        )

    def _metric(self, area: ImprovementArea, key: str, rows: list[FeedbackSignal]) -> PerformanceMetric:
        total = max(len(rows), 1)
        positives = sum(1 for row in rows if row.outcome in self.POSITIVE_OUTCOMES)
        negatives = sum(1 for row in rows if row.outcome in self.NEGATIVE_OUTCOMES)
        precision = positives / total * 100.0
        recall = positives / max(positives + negatives, 1) * 100.0
        return PerformanceMetric(
            area=area,
            entity_key=key,
            precision=round(precision, 4),
            recall=round(recall, 4),
            conversion_rate=round(positives / total * 100.0, 4),
            average_confidence=round(mean([row.score for row in rows] or [0.0]), 4),
            average_latency_ms=round(mean([float(row.details.get("latency_ms", 0.0)) for row in rows] or [0.0]), 4),
            sample_size=len(rows),
            trend=[{"outcome": row.outcome, "score": row.score} for row in rows[-20:]],
        )
