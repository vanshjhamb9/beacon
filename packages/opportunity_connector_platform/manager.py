"""Connector manager — orchestrates the full connector lifecycle."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from opportunity_connector_platform.connector import Connector, ConnectorHealth
from opportunity_connector_platform.connector_events import EvidenceEvent, EventBatch
from opportunity_connector_platform.connector_metrics import ConnectorMetrics
from opportunity_connector_platform.registry import ConnectorRegistry
from opportunity_connector_platform.signal_normalizer import SignalNormalizer
from opportunity_connector_platform.signal_router import SignalRouter
from opportunity_connector_platform.signal_validator import SignalValidator

logger = logging.getLogger(__name__)


class ConnectorManager:
    """Orchestrates connector lifecycle: authenticate → discover → normalize → validate → emit."""

    def __init__(
        self,
        registry: ConnectorRegistry | None = None,
        router: SignalRouter | None = None,
    ) -> None:
        self.registry = registry or ConnectorRegistry()
        self.router = router or SignalRouter()
        self.metrics = ConnectorMetrics()
        self._history: dict[str, list[dict[str, Any]]] = {}

    async def run_connector(self, connector_id: str) -> dict[str, Any]:
        connector = self.registry.get(connector_id)
        if connector is None:
            return {"error": f"connector_not_found: {connector_id}"}

        config = self.registry.config(connector_id)
        if config and not config.enabled:
            return {"connector_id": connector_id, "status": "disabled"}

        started = datetime.now(UTC)
        try:
            authenticated = await connector.authenticate()
            if not authenticated:
                return {"connector_id": connector_id, "status": "authentication_failed"}

            raw_payloads = await connector.discover()
            batch_events: list[EvidenceEvent] = []
            for payload in raw_payloads:
                event = connector.normalize(payload)
                batch_events.append(event)

            routed = self.router.route_batch(batch_events)
            accepted = [r for r in routed if r.accepted]
            rejected = [r for r in routed if not r.accepted]

            elapsed = (datetime.now(UTC) - started).total_seconds() * 1000
            self.registry.update_stats(
                connector_id,
                events_today=len(batch_events),
                events_accepted=len(accepted),
                events_rejected=len(rejected),
                average_latency=elapsed,
            )
            self._record_history(connector_id, {
                "connector_id": connector_id,
                "total_collected": len(raw_payloads),
                "total_accepted": len(accepted),
                "total_rejected": len(rejected),
                "latency_ms": elapsed,
                "status": "completed",
            })

            return {
                "connector_id": connector_id,
                "status": "completed",
                "total_collected": len(raw_payloads),
                "total_accepted": len(accepted),
                "total_rejected": len(rejected),
                "latency_ms": elapsed,
            }
        except Exception as exc:
            elapsed = (datetime.now(UTC) - started).total_seconds() * 1000
            self._record_history(connector_id, {
                "connector_id": connector_id,
                "status": "error",
                "error": str(exc),
                "latency_ms": elapsed,
            })
            logger.exception("Connector %s failed", connector_id)
            return {"connector_id": connector_id, "status": "error", "error": str(exc)}

    async def run_all(self) -> list[dict[str, Any]]:
        results = []
        for entry in self.registry.enabled():
            result = await self.run_connector(entry.connector_id)
            results.append(result)
        return results

    async def retry_connector(self, connector_id: str) -> dict[str, Any]:
        return await self.run_connector(connector_id)

    def get_history(self, connector_id: str) -> list[dict[str, Any]]:
        return self._history.get(connector_id, [])

    def all_history(self) -> dict[str, list[dict[str, Any]]]:
        return dict(self._history)

    def _record_history(self, connector_id: str, record: dict[str, Any]) -> None:
        self._history.setdefault(connector_id, []).append(record)
        if len(self._history[connector_id]) > 1000:
            self._history[connector_id] = self._history[connector_id][-1000:]
