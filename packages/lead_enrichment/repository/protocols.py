from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from lead_enrichment.models.types import EnrichmentOpportunityInput, SalesReadyLeadProfile


class EnrichmentInputRepository(Protocol):
    async def pending_opportunity_inputs(self, *, limit: int) -> Sequence[EnrichmentOpportunityInput]:
        ...

    async def opportunity_input(
        self,
        opportunity_id: UUID,
        *,
        force_refresh: bool = False,
    ) -> EnrichmentOpportunityInput | None:
        ...

    async def store_enrichment(self, result: SalesReadyLeadProfile) -> UUID:
        ...
