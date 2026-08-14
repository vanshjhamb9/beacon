"""Standard connector interface for OCP v1.

Every connector must implement the full Connector ABC.
No connector may directly create companies, opportunities, decision makers,
or Revenue Ready records — connectors emit evidence only.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from opportunity_connector_platform.connector_capabilities import ConnectorCapability
from opportunity_connector_platform.connector_events import EvidenceEvent


@dataclass(frozen=True, slots=True)
class ConnectorHealth:
    """Health snapshot for a single connector."""
    status: str = "healthy"
    detail: str = ""
    latency_ms: float = 0.0
    failure_rate: float = 0.0
    rate_limit_remaining: int | None = None
    failures: int = 0
    retries: int = 0
    authenticated: bool = True
    queue_size: int = 0
    freshness_minutes: int = 0
    last_check: datetime = field(default_factory=lambda: datetime.now(UTC))


class Connector(ABC):
    """Every connector emits normalized evidence only.

    Lifecycle:
        1. ``id``, ``name``, ``version``, ``capabilities`` — static metadata
        2. ``authenticate`` — verify credentials / tokens
        3. ``discover`` — raw payloads from external source
        4. ``normalize`` — convert payload → EvidenceEvent
        5. ``validate`` — deterministic gatekeeping
        6. ``emit`` — push validated event into pipeline
        7. ``health`` — current health snapshot
        8. ``shutdown`` — graceful teardown
    """

    @abstractmethod
    def id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def version(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> tuple[ConnectorCapability, ...]:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> ConnectorHealth:
        raise NotImplementedError

    @abstractmethod
    async def authenticate(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def discover(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, payload: dict[str, Any]) -> EvidenceEvent:
        raise NotImplementedError

    @abstractmethod
    def validate(self, event: EvidenceEvent) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def emit(self, event: EvidenceEvent) -> EvidenceEvent:
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self) -> None:
        raise NotImplementedError


class NullConnector(Connector):
    """Deterministic no-op connector for testing the full pipeline."""

    def id(self) -> str:
        return "null"

    def name(self) -> str:
        return "Null"

    def version(self) -> str:
        return "0.0.1"

    def capabilities(self) -> tuple[ConnectorCapability, ...]:
        return ()

    def health(self) -> ConnectorHealth:
        return ConnectorHealth(status="healthy")

    async def authenticate(self) -> bool:
        return True

    async def discover(self) -> list[dict[str, Any]]:
        return []

    def normalize(self, payload: dict[str, Any]) -> EvidenceEvent:
        now = datetime.now(UTC)
        return EvidenceEvent(
            connector_id=self.id(),
            connector_version=self.version(),
            headline="test",
            event_type="Hiring",
            event_category="Identity",
            url="https://example.com",
            published_at=now,
            captured_at=now,
            evidence="test",
            collector=self.name(),
        )

    def validate(self, event: EvidenceEvent) -> bool:
        return True

    async def emit(self, event: EvidenceEvent) -> EvidenceEvent:
        return event

    async def shutdown(self) -> None:
        pass
