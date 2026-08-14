from intelligence_improvement.models.types import (
    ImprovementArea,
    OptimizationRecommendation,
    PerformanceMetric,
    RulePerformanceMetric,
)


class OptimizationEngine:
    def collector_recommendations(self, metrics: list[PerformanceMetric]) -> list[OptimizationRecommendation]:
        recommendations: list[OptimizationRecommendation] = []
        for metric in metrics:
            if metric.precision < 60.0 or metric.conversion_rate < 20.0:
                recommendations.append(
                    OptimizationRecommendation(
                        area=ImprovementArea.COLLECTOR,
                        target_key=metric.entity_key,
                        recommendation="Reduce collection priority or tighten collector filters.",
                        reason="Collector precision or conversion rate is below the approval threshold.",
                        expected_impact=round(70.0 - min(metric.precision, metric.conversion_rate), 4),
                        confidence=max(40.0, 100.0 - metric.precision),
                        evidence={"metric": metric.model_dump(mode="json")},
                    )
                )
        return recommendations

    def rule_recommendations(self, metrics: list[RulePerformanceMetric]) -> list[OptimizationRecommendation]:
        recommendations: list[OptimizationRecommendation] = []
        for metric in metrics:
            if metric.confidence < 65.0 and metric.times_fired >= 3:
                recommendations.append(
                    OptimizationRecommendation(
                        area=ImprovementArea.QUALITY_RULE if metric.rule_type == "quality" else ImprovementArea.CLASSIFIER,
                        target_key=metric.rule_key,
                        recommendation="Reduce rule weight or raise confidence threshold.",
                        reason="Rule has low precision against accepted ground-truth outcomes.",
                        expected_impact=round(65.0 - metric.confidence, 4),
                        confidence=round(100.0 - metric.confidence, 4),
                        evidence={"metric": metric.model_dump(mode="json")},
                    )
                )
            elif metric.confidence >= 85.0 and metric.times_fired >= 5:
                recommendations.append(
                    OptimizationRecommendation(
                        area=ImprovementArea.QUALITY_RULE if metric.rule_type == "quality" else ImprovementArea.CLASSIFIER,
                        target_key=metric.rule_key,
                        recommendation="Consider increasing rule weight after human approval.",
                        reason="Rule is consistently predictive across enough samples.",
                        expected_impact=round(metric.confidence - 80.0, 4),
                        confidence=metric.confidence,
                        evidence={"metric": metric.model_dump(mode="json")},
                    )
                )
        return recommendations
