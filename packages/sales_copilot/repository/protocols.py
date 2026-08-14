from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sales_copilot.models.types import SalesCopilotInput, SalesIntelligencePackage


class SalesCopilotRepositoryProtocol(Protocol):
    async def build_input_for_company(self, company_id: UUID, *, force_refresh: bool = False) -> SalesCopilotInput | None:
        ...

    async def build_input_for_opportunity(
        self, opportunity_id: UUID, *, force_refresh: bool = False
    ) -> SalesCopilotInput | None:
        ...

    async def store_package(self, package: SalesIntelligencePackage) -> UUID:
        ...

    async def latest_for_company(self, company_id: UUID):
        ...

    async def latest_for_opportunity(self, opportunity_id: UUID):
        ...

    async def history(self, entity_id: UUID):
        ...
