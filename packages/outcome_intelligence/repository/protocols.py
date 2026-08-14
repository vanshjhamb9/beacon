from collections.abc import Sequence
from typing import Any, Protocol
from uuid import UUID

from outcome_intelligence.models.types import OutcomeUpdateInput


class OutcomeRepositoryProtocol(Protocol):
    async def update_outcome(self, payload: OutcomeUpdateInput) -> dict[str, Any]:
        ...

    async def outcome_records(self, *, limit: int = 5000) -> Sequence[dict[str, Any]]:
        ...

    async def company_outcomes(self, company_id: UUID) -> dict[str, Any]:
        ...
