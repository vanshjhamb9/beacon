from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from opportunity_engine.models import CompanyOpportunityInput


class OpportunityInputRepository(Protocol):
    async def pending_company_inputs(self, *, limit: int) -> Sequence[CompanyOpportunityInput]:
        ...

    async def has_recent_opportunity_for_company(self, company_id: UUID) -> bool:
        ...
