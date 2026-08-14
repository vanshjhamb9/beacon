from __future__ import annotations

from global_opportunity_acquisition.models.types import GOAPDecision, GOAPInput
from global_opportunity_acquisition.pipelines.goap_pipeline import GlobalOpportunityAcquisitionPipeline


class GlobalOpportunityAcquisitionService:
    def __init__(self, pipeline: GlobalOpportunityAcquisitionPipeline | None = None) -> None:
        self.pipeline = pipeline or GlobalOpportunityAcquisitionPipeline()

    def evaluate(self, data: GOAPInput) -> GOAPDecision:
        return self.pipeline.process(data)

    def evaluate_many(self, items: list[GOAPInput]) -> list[GOAPDecision]:
        return [self.evaluate(item) for item in items]
