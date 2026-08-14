from __future__ import annotations

from typing import Protocol
from uuid import UUID

from revenue_hunter.models.types import RevenueHunterDecision, RevenueHunterInput


class RevenueHunterRepositoryProtocol(Protocol):
    async def pending_inputs(self, *, limit: int) -> list[RevenueHunterInput]: ...

    async def store_decision(self, decision: RevenueHunterDecision) -> object: ...

    async def list_dossiers(
        self, *, grade: str | None, limit: int, offset: int
    ) -> list[object]: ...

    async def get_dossier(self, dossier_id: UUID) -> object | None: ...
