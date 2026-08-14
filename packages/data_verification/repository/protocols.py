from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from data_verification.models.types import VerificationInput, VerificationResult


class VerificationInputRepository(Protocol):
    async def pending_verification_inputs(self, *, limit: int) -> Sequence[VerificationInput]:
        ...

    async def verification_input(
        self,
        enrichment_report_id: UUID,
        *,
        force_refresh: bool = False,
    ) -> VerificationInput | None:
        ...

    async def store_verification(self, result: VerificationResult) -> UUID:
        ...
