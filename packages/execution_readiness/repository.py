"""Repository protocol — persistence for provider + execution status rows."""

from __future__ import annotations

from typing import Any, Protocol

from execution_readiness.enums import ExecutionMode
from execution_readiness.models import ProviderSnapshot


class ExecutionReadinessRepository(Protocol):
    async def load_providers(self, organization_id: str) -> list[ProviderSnapshot]:
        ...

    async def count_verified_deliveries(self, organization_id: str) -> int:
        ...

    async def count_messages_sent(self, organization_id: str) -> int:
        ...

    async def delivered_company_ids(self, organization_id: str) -> set[str]:
        ...

    async def upsert_provider_status(self, organization_id: str, providers: list[ProviderSnapshot]) -> None:
        ...

    async def upsert_execution_status(
        self,
        organization_id: str,
        *,
        mode: ExecutionMode,
        reason: str,
        flags: dict[str, Any],
    ) -> None:
        ...
