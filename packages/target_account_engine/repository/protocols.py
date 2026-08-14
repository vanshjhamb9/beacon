from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from target_account_engine.models.types import ICPProfile, TargetAccountDecision, TargetAccountInput


class TargetAccountRepositoryProtocol(Protocol):
    async def list_icps(self) -> list[ICPProfile]: ...

    async def upsert_icp(self, profile: ICPProfile) -> Any: ...

    async def delete_icp(self, icp_id: UUID) -> bool: ...

    async def pending_inputs(self, *, limit: int) -> list[TargetAccountInput]: ...

    async def store_decision(self, decision: TargetAccountDecision) -> Any: ...
