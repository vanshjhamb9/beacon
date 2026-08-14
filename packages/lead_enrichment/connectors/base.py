from typing import Protocol

from lead_enrichment.models.types import EnrichmentOpportunityInput


class EnrichmentConnector(Protocol):
    name: str

    def collect(self, item: EnrichmentOpportunityInput) -> object:
        ...
