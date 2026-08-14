from collections.abc import Sequence

from app.models.improvement import (
    CollectorPerformance,
    ExperimentRun,
    OpportunityAccuracy,
    QualityRulePerformance,
    WeightAdjustment,
)
from app.repositories.improvement import ImprovementRepository
from intelligence_improvement import ImprovementPipeline


class ImprovementService:
    def __init__(
        self,
        repository: ImprovementRepository,
        pipeline: ImprovementPipeline | None = None,
    ) -> None:
        self.repository = repository
        self.pipeline = pipeline or ImprovementPipeline()

    async def run_evaluation(self, *, limit: int = 1000) -> dict[str, int]:
        feedback = await self.repository.feedback_signals(limit=limit)
        quality_feedback = await self.repository.quality_rule_feedback(limit=limit)
        classifier_feedback = await self.repository.classifier_feedback(limit=limit)
        predictions = await self.repository.prediction_evaluations(limit=limit)
        report = self.pipeline.process(
            feedback=feedback,
            quality_rule_feedback=quality_feedback,
            classifier_feedback=classifier_feedback,
            predictions=predictions,
        )
        await self.repository.store_report(report)
        await self.repository.store_prediction_evaluations(predictions)
        return {
            "feedback_events": int(report.overview["feedback_events"]),
            "recommendations": len(report.recommendations),
            "predictions": len(predictions),
        }

    async def overview(self) -> dict[str, float | int | str]:
        return await self.repository.overview()

    async def collectors(self) -> Sequence[CollectorPerformance]:
        return await self.repository.collectors()

    async def rules(self) -> Sequence[QualityRulePerformance]:
        return await self.repository.rules()

    async def opportunities(self) -> Sequence[OpportunityAccuracy]:
        return await self.repository.opportunities()

    async def experiments(self) -> Sequence[ExperimentRun]:
        return await self.repository.experiments()

    async def recommendations(self) -> Sequence[WeightAdjustment]:
        return await self.repository.recommendations()
