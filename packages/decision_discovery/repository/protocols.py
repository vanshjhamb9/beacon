from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from decision_discovery.models.types import DecisionDiscoveryInput, DecisionMakerReport


class DecisionDiscoveryInputRepository(Protocol):
    async def pending_discovery_inputs(self, *, limit: int) -> Sequence[DecisionDiscoveryInput]:
        ...

    async def discovery_input_for_company(self, company_id: UUID, *, force_refresh: bool = False) -> DecisionDiscoveryInput | None:
        ...

    async def store_discovery(self, result: DecisionMakerReport) -> UUID:
        ...
