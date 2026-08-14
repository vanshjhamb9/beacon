from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from global_opportunity_acquisition.connectors.catalog import connector_catalog
from global_opportunity_acquisition.models.types import (
    ConnectorDefinition,
    ConnectorMetrics,
    ConnectorStatus,
    RawSignal,
)


class BaseGOAPConnector(ABC):
    """Compliant connector contract — no private scraping, no ToS-violating crawlers."""

    definition: ConnectorDefinition

    @abstractmethod
    def collect(self, *, context: dict[str, Any] | None = None) -> list[RawSignal]:
        raise NotImplementedError

    def is_enabled(self) -> bool:
        return self.definition.status == ConnectorStatus.ACTIVE


class CatalogConnector(BaseGOAPConnector):
    """Deterministic stub connector that emits no network I/O; used for scoring/bench."""

    def __init__(self, definition: ConnectorDefinition) -> None:
        self.definition = definition

    def collect(self, *, context: dict[str, Any] | None = None) -> list[RawSignal]:
        if not self.is_enabled():
            return []
        ctx = context or {}
        preset = list(ctx.get("signals", {}).get(self.definition.connector_id, []))
        return [RawSignal.model_validate(s) if isinstance(s, dict) else s for s in preset]


class ConnectorRegistry:
    def __init__(self) -> None:
        self._defs = {c.connector_id: c for c in connector_catalog()}

    def all(self) -> list[ConnectorDefinition]:
        return list(self._defs.values())

    def get(self, connector_id: str) -> ConnectorDefinition | None:
        return self._defs.get(connector_id)

    def active(self) -> list[ConnectorDefinition]:
        return [c for c in self._defs.values() if c.status == ConnectorStatus.ACTIVE]

    def build(self, connector_id: str) -> BaseGOAPConnector | None:
        d = self.get(connector_id)
        if d is None:
            return None
        return CatalogConnector(d)


class ConnectorHealthEngine:
    def score(
        self,
        definition: ConnectorDefinition,
        *,
        signals: int = 0,
        companies: int = 0,
        opportunities: int = 0,
        duplicates: int = 0,
        latency_ms: float = 0.0,
        errors: int = 0,
        outcomes: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> ConnectorMetrics:
        outcomes = outcomes or {}
        if definition.status != ConnectorStatus.ACTIVE:
            return ConnectorMetrics(
                connector_id=definition.connector_id,
                connector_name=definition.connector_name,
                health="disabled" if definition.status == ConnectorStatus.DISABLED else "pending",
                availability=0.0,
                last_run=now or datetime.now(UTC),
                evidence=[f"status:{definition.status.value}", definition.notes],
            )
        quality = min(100.0, 40.0 + opportunities * 8.0 + companies * 2.0 - duplicates * 3.0 - errors * 10.0)
        trust = 85.0 if definition.public_information_only else 60.0
        if definition.requires_license:
            trust = 95.0
        coverage = min(100.0, float(outcomes.get("coverage", 50.0 + min(40.0, signals * 2.0))))
        freshness = min(100.0, float(outcomes.get("freshness", 70.0)))
        roi = min(
            100.0,
            float(outcomes.get("revenue", 0.0)) * 0.01
            + opportunities * 5.0
            + float(outcomes.get("meetings", 0)) * 8.0
            - errors * 5.0,
        )
        availability = max(0.0, 100.0 - errors * 15.0)
        health = "healthy"
        if errors >= 3 or availability < 50:
            health = "degraded"
        if errors >= 8:
            health = "unhealthy"
        return ConnectorMetrics(
            connector_id=definition.connector_id,
            connector_name=definition.connector_name,
            health=health,
            availability=round(availability, 2),
            last_run=now or datetime.now(UTC),
            signals_found=signals,
            companies_found=companies,
            opportunities_found=opportunities,
            duplicates=duplicates,
            latency_ms=float(latency_ms),
            errors=errors,
            quality_score=round(max(0.0, quality), 2),
            trust_score=round(trust, 2),
            coverage_score=round(coverage, 2),
            freshness_score=round(freshness, 2),
            roi_score=round(max(0.0, min(100.0, roi)), 2),
            evidence=[
                f"signals:{signals}",
                f"opportunities:{opportunities}",
                f"access:{definition.access_mode.value}",
            ],
        )
