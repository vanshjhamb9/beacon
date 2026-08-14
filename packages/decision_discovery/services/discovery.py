from decision_discovery.models.types import DecisionDiscoveryInput, DecisionMakerReport
from decision_discovery.pipelines.discovery_pipeline import DecisionDiscoveryPipeline


class DecisionDiscoveryService:
    def __init__(self, pipeline: DecisionDiscoveryPipeline | None = None) -> None:
        self.pipeline = pipeline or DecisionDiscoveryPipeline()

    def discover(self, item: DecisionDiscoveryInput) -> DecisionMakerReport:
        return self.pipeline.process(item)
