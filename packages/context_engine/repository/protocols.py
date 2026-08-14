from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from context_engine.models.types import BusinessContextInput


class ContextInputRepository(Protocol):
    async def pending_context_inputs(self, *, limit: int) -> Sequence[BusinessContextInput]:
        ...

    async def has_context_for_signal(self, classified_signal_id: UUID) -> bool:
        ...
