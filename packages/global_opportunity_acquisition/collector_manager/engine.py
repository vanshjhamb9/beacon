from __future__ import annotations

from global_opportunity_acquisition.connectors.registry import ConnectorHealthEngine, ConnectorRegistry
from global_opportunity_acquisition.models.types import ConnectorMetrics, RawSignal
import time


class CollectorManagerEngine:
    def __init__(self, registry: ConnectorRegistry | None = None) -> None:
        self.registry = registry or ConnectorRegistry()
        self.health = ConnectorHealthEngine()

    def refresh(
        self,
        *,
        context: dict | None = None,
        outcomes: dict[str, dict] | None = None,
    ) -> tuple[list[RawSignal], list[ConnectorMetrics]]:
        context = context or {}
        outcomes = outcomes or {}
        signals: list[RawSignal] = []
        metrics: list[ConnectorMetrics] = []
        for definition in self.registry.all():
            connector = self.registry.build(definition.connector_id)
            if connector is None:
                continue
            started = time.perf_counter()
            errors = 0
            collected: list[RawSignal] = []
            try:
                collected = connector.collect(context=context)
            except Exception:  # noqa: BLE001
                errors = 1
            latency = (time.perf_counter() - started) * 1000.0
            companies = len({s.company_name.lower() for s in collected if s.company_name})
            signals.extend(collected)
            metrics.append(
                self.health.score(
                    definition,
                    signals=len(collected),
                    companies=companies,
                    opportunities=int(outcomes.get(definition.connector_id, {}).get("opportunities", len(collected))),
                    duplicates=int(outcomes.get(definition.connector_id, {}).get("duplicates", 0)),
                    latency_ms=latency,
                    errors=errors + int(outcomes.get(definition.connector_id, {}).get("errors", 0)),
                    outcomes=outcomes.get(definition.connector_id),
                )
            )
        return signals, metrics
