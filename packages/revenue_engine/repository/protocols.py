from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from revenue_engine.models.types import RevenueOpportunityInput, RevenueRecommendationResult, ServiceDefinition


class RevenueInputRepository(Protocol):
    async def pending_opportunity_inputs(self, *, limit: int) -> Sequence[RevenueOpportunityInput]:
        ...

    async def list_enabled_services(self) -> Sequence[ServiceDefinition]:
        ...

    async def store_recommendation(self, result: RevenueRecommendationResult) -> UUID:
        ...
