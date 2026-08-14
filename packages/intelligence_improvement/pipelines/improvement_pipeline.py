from datetime import UTC, datetime

from intelligence_improvement.evaluation.engine import EvaluationEngine
from intelligence_improvement.models.types import FeedbackSignal, ImprovementReport, PredictionEvaluation
from intelligence_improvement.optimization.engine import OptimizationEngine


class ImprovementPipeline:
    def __init__(
        self,
        *,
        evaluator: EvaluationEngine | None = None,
        optimizer: OptimizationEngine | None = None,
    ) -> None:
        self.evaluator = evaluator or EvaluationEngine()
        self.optimizer = optimizer or OptimizationEngine()

    def process(
        self,
        *,
        feedback: list[FeedbackSignal],
        quality_rule_feedback: list[FeedbackSignal],
        classifier_feedback: list[FeedbackSignal],
        predictions: list[PredictionEvaluation],
    ) -> ImprovementReport:
        collector_rankings = self.evaluator.collector_performance(feedback)
        quality_rules = self.evaluator.rule_performance(quality_rule_feedback, rule_type="quality")
        classifier_rules = self.evaluator.rule_performance(classifier_feedback, rule_type="classifier")
        rule_rankings = [*quality_rules, *classifier_rules]
        prediction_metrics = self.evaluator.prediction_errors(predictions)
        recommendations = [
            *self.optimizer.collector_recommendations(collector_rankings),
            *self.optimizer.rule_recommendations(rule_rankings),
        ]
        overview = {
            "feedback_events": len(feedback) + len(quality_rule_feedback) + len(classifier_feedback),
            "optimization_recommendations": len(recommendations),
            **prediction_metrics,
        }
        return ImprovementReport(
            generated_at=datetime.now(UTC),
            overview=overview,
            collector_rankings=collector_rankings,
            rule_rankings=rule_rankings,
            opportunity_accuracy=prediction_metrics,
            recommendations=recommendations,
        )
