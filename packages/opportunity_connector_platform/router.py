"""Connector router — wires connectors to the live opportunity pipeline."""

from __future__ import annotations

from typing import Any

from opportunity_connector_platform.connector import Connector
from opportunity_connector_platform.connector_config import ConnectorConfig
from opportunity_connector_platform.connector_events import EvidenceEvent
from opportunity_connector_platform.manager import ConnectorManager
from opportunity_connector_platform.registry import ConnectorRegistry
from opportunity_connector_platform.signal_router import SignalRouter


class ConnectorRouter:
    """High-level router that manages registration, scheduling, and routing."""

    def __init__(self) -> None:
        self.registry = ConnectorRegistry()
        self.signal_router = SignalRouter()
        self.manager = ConnectorManager(registry=self.registry, router=self.signal_router)

    def register(
        self,
        connector: Connector,
        config: ConnectorConfig | None = None,
    ) -> None:
        self.registry.register(connector, config)

    def configure(self, config: ConnectorConfig) -> None:
        self.registry.configure(config)

    async def route_event(self, event: EvidenceEvent) -> dict[str, Any]:
        routed = self.signal_router.route(event)
        return {
            "accepted": routed.accepted,
            "rejection_reason": routed.rejection_reason,
            "event_id": str(routed.event.event_id),
            "connector_id": routed.event.connector_id,
        }

    async def route_batch(self, events: list[EvidenceEvent]) -> dict[str, Any]:
        routed = self.signal_router.route_batch(events)
        accepted = [r for r in routed if r.accepted]
        rejected = [r for r in routed if not r.accepted]
        return {
            "total": len(events),
            "accepted": len(accepted),
            "rejected": len(rejected),
            "rejection_reasons": self.signal_router.rejection_reasons(routed),
        }

    async def run_connector(self, connector_id: str) -> dict[str, Any]:
        return await self.manager.run_connector(connector_id)

    async def run_all(self) -> list[dict[str, Any]]:
        return await self.manager.run_all()

    def registry_entries(self) -> list[dict[str, Any]]:
        return [
            {
                "connector_id": e.connector_id,
                "name": e.name,
                "enabled": e.enabled,
                "configured": e.configured,
                "healthy": e.healthy,
                "version": e.version,
                "category": e.category,
                "events_today": e.events_today,
                "events_accepted": e.events_accepted,
                "events_rejected": e.events_rejected,
                "average_latency": e.average_latency,
                "failure_rate": e.failure_rate,
                "rate_limit_remaining": e.rate_limit_remaining,
            }
            for e in self.registry.all()
        ]
