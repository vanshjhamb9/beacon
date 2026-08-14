"""Dynamic connector registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from opportunity_connector_platform.connector import Connector
from opportunity_connector_platform.connector_capabilities import ConnectorCapability, category_for
from opportunity_connector_platform.connector_config import ConnectorConfig
from opportunity_connector_platform.connector import ConnectorHealth


@dataclass(frozen=True, slots=True)
class ConnectorRegistryEntry:
    connector_id: str
    name: str
    enabled: bool
    configured: bool
    healthy: bool
    version: str
    category: str
    capabilities: tuple[ConnectorCapability, ...]
    last_sync: datetime | None = None
    events_today: int = 0
    events_accepted: int = 0
    events_rejected: int = 0
    average_latency: float = 0.0
    failure_rate: float = 0.0
    rate_limit_remaining: int | None = None


class ConnectorRegistry:
    """Dynamic registry — connectors register at startup."""

    def __init__(self) -> None:
        self._connectors: dict[str, Connector] = {}
        self._configs: dict[str, ConnectorConfig] = {}
        self._stats: dict[str, dict[str, int]] = {}

    def register(self, connector: Connector, config: ConnectorConfig | None = None) -> None:
        self._connectors[connector.id()] = connector
        if config:
            self._configs[connector.id()] = config

    def configure(self, config: ConnectorConfig) -> None:
        self._configs[config.connector_id] = config

    def get(self, connector_id: str) -> Connector | None:
        return self._connectors.get(connector_id)

    def has(self, connector_id: str) -> bool:
        return connector_id in self._connectors

    def all(self) -> list[ConnectorRegistryEntry]:
        return [self.entry(connector_id) for connector_id in sorted(self._connectors)]

    def enabled(self) -> list[ConnectorRegistryEntry]:
        return [
            self.entry(cid)
            for cid in sorted(self._connectors)
            if self._configs.get(cid, ConnectorConfig(connector_id=cid)).enabled
        ]

    def entry(self, connector_id: str) -> ConnectorRegistryEntry:
        connector = self._connectors[connector_id]
        config = self._configs.get(connector_id)
        health = connector.health()
        stats = self._stats.get(connector_id, {})
        return ConnectorRegistryEntry(
            connector_id=connector.id(),
            name=connector.name(),
            enabled=bool(config.enabled) if config else False,
            configured=config is not None,
            healthy=health.status == "healthy",
            version=connector.version(),
            category=category_for(connector.name()),
            capabilities=connector.capabilities(),
            average_latency=health.latency_ms,
            failure_rate=health.failure_rate,
            rate_limit_remaining=health.rate_limit_remaining,
            events_today=stats.get("events_today", 0),
            events_accepted=stats.get("events_accepted", 0),
            events_rejected=stats.get("events_rejected", 0),
        )

    def update_stats(self, connector_id: str, **kwargs: int | float) -> None:
        self._stats.setdefault(connector_id, {})
        self._stats[connector_id].update(kwargs)

    def ids(self) -> list[str]:
        return sorted(self._connectors.keys())

    def count(self) -> int:
        return len(self._connectors)

    def config(self, connector_id: str) -> ConnectorConfig | None:
        return self._configs.get(connector_id)
