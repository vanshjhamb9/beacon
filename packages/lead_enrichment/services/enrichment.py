from lead_enrichment.models.types import EnrichmentOpportunityInput, SalesReadyLeadProfile
from lead_enrichment.pipelines.enrichment_pipeline import EnrichmentPipeline


class EnrichmentService:
    """Pure-domain enrichment service used by the API application service."""

    def __init__(self, pipeline: EnrichmentPipeline | None = None) -> None:
        self.pipeline = pipeline or EnrichmentPipeline()

    def enrich(self, item: EnrichmentOpportunityInput) -> SalesReadyLeadProfile:
        return self.pipeline.process(item)
