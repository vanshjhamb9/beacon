from outcome_intelligence.models.types import OutcomeAnalytics, OutcomeDashboard
from outcome_intelligence.pipelines.outcome_pipeline import OutcomeIntelligencePipeline


class OutcomeIntelligenceService:
    def __init__(self, pipeline: OutcomeIntelligencePipeline | None = None) -> None:
        self.pipeline = pipeline or OutcomeIntelligencePipeline()

    def dashboard(self, records: list[dict]) -> OutcomeDashboard:
        return self.pipeline.build_dashboard(records)

    def analytics(self, records: list[dict]) -> OutcomeAnalytics:
        return self.pipeline.build_analytics(records)
