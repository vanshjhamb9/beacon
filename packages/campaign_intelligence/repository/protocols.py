from __future__ import annotations

from typing import Protocol
from uuid import UUID

from campaign_intelligence.models.types import CampaignInput, CampaignPlan


class CampaignRepositoryProtocol(Protocol):
    async def build_input_for_company(self, company_id: UUID, *, force_refresh: bool = False) -> CampaignInput | None:
        ...

    async def store_plan(self, plan: CampaignPlan):
        ...

    async def get_campaign(self, campaign_id: UUID):
        ...
