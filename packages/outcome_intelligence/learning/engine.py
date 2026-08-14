from __future__ import annotations

from outcome_intelligence.models.types import AccuracyMetric, DimensionRevenue, LearningRecommendation, RateMetrics


class OutcomeLearningEngine:
    """Generate improvement recommendations only. Never overwrite rules automatically."""

    def recommendations(
        self,
        *,
        rates: RateMetrics,
        collector_accuracy: list[AccuracyMetric],
        service_accuracy: list[AccuracyMetric],
        industry_accuracy: list[AccuracyMetric],
        persona_accuracy: list[AccuracyMetric],
        prediction_accuracy: list[AccuracyMetric],
        revenue_by_service: list[DimensionRevenue],
    ) -> list[LearningRecommendation]:
        recs: list[LearningRecommendation] = []

        if rates.contacted_count >= 5 and rates.reply_rate < 20.0:
            recs.append(
                LearningRecommendation(
                    area="opportunity",
                    target_key="reply_rate",
                    recommendation="Review contact timing and persona targeting — reply rate is below 20%.",
                    reason=f"Observed reply rate {rates.reply_rate:.1f}% across {rates.contacted_count} contacted opportunities.",
                    expected_impact=12.0,
                    confidence=min(90.0, 50.0 + rates.contacted_count),
                    evidence={"reply_rate": rates.reply_rate, "contacted_count": rates.contacted_count},
                )
            )

        if rates.meeting_count >= 3 and rates.close_rate < 10.0:
            recs.append(
                LearningRecommendation(
                    area="recommendation",
                    target_key="close_rate",
                    recommendation="Inspect proposal-to-close handoff and qualification criteria.",
                    reason=f"Close rate {rates.close_rate:.1f}% after {rates.meeting_count} meetings.",
                    expected_impact=15.0,
                    confidence=70.0,
                    evidence={"close_rate": rates.close_rate, "meeting_count": rates.meeting_count},
                )
            )

        for metric in collector_accuracy[:3]:
            if metric.sample_size >= 5 and metric.accuracy_score < 45.0:
                recs.append(
                    LearningRecommendation(
                        area="collector",
                        target_key=metric.key,
                        recommendation=f"Deprioritize or retune collector '{metric.key}' — low outcome accuracy.",
                        reason=f"Collector accuracy {metric.accuracy_score:.1f}% on {metric.sample_size} samples.",
                        expected_impact=10.0,
                        confidence=min(85.0, 40.0 + metric.sample_size),
                        evidence=metric.details | {"accuracy_score": metric.accuracy_score},
                    )
                )

        for metric in service_accuracy[:3]:
            if metric.sample_size >= 5 and metric.precision < 35.0:
                recs.append(
                    LearningRecommendation(
                        area="recommendation",
                        target_key=metric.key,
                        recommendation=f"Review service matching for '{metric.key}'.",
                        reason=f"Service precision {metric.precision:.1f}% on {metric.sample_size} outcomes.",
                        expected_impact=11.0,
                        confidence=65.0,
                        evidence={"precision": metric.precision, "sample_size": metric.sample_size},
                    )
                )

        for metric in industry_accuracy[:2]:
            if metric.sample_size >= 5 and metric.accuracy_score < 40.0:
                recs.append(
                    LearningRecommendation(
                        area="context",
                        target_key=metric.key,
                        recommendation=f"Add industry-specific evidence checks for '{metric.key}'.",
                        reason=f"Industry accuracy {metric.accuracy_score:.1f}%.",
                        expected_impact=8.0,
                        confidence=60.0,
                        evidence={"accuracy_score": metric.accuracy_score},
                    )
                )

        for metric in persona_accuracy[:2]:
            if metric.sample_size >= 5 and metric.accuracy_score < 40.0:
                recs.append(
                    LearningRecommendation(
                        area="opportunity",
                        target_key=metric.key,
                        recommendation=f"Validate buyer persona mapping for '{metric.key}'.",
                        reason=f"Persona accuracy {metric.accuracy_score:.1f}%.",
                        expected_impact=9.0,
                        confidence=62.0,
                        evidence={"accuracy_score": metric.accuracy_score},
                    )
                )

        for metric in prediction_accuracy:
            if metric.sample_size >= 8 and metric.average_prediction_error > 35.0:
                recs.append(
                    LearningRecommendation(
                        area="opportunity",
                        target_key="opportunity_score_calibration",
                        recommendation="Calibrate opportunity score thresholds against realized outcomes.",
                        reason=f"Average prediction error {metric.average_prediction_error:.1f} across {metric.sample_size} outcomes.",
                        expected_impact=14.0,
                        confidence=75.0,
                        evidence={"average_prediction_error": metric.average_prediction_error},
                    )
                )

        if revenue_by_service:
            top = revenue_by_service[0]
            if top.revenue > 0 and top.win_rate >= 40.0:
                recs.append(
                    LearningRecommendation(
                        area="recommendation",
                        target_key=top.key,
                        recommendation=f"Increase coverage for high-ROI service '{top.key}'.",
                        reason=f"Service generated {top.revenue:.0f} revenue with {top.win_rate:.1f}% win rate.",
                        expected_impact=13.0,
                        confidence=80.0,
                        evidence={"revenue": top.revenue, "win_rate": top.win_rate, "deals": top.deals},
                    )
                )

        # Always require approval — never auto-apply.
        return [item.model_copy(update={"requires_approval": True}) for item in recs]
