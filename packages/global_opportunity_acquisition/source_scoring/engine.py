from __future__ import annotations

from global_opportunity_acquisition.connectors.registry import ConnectorHealthEngine, ConnectorRegistry
from global_opportunity_acquisition.models.types import ConnectorMetrics


class SourceScoringEngine:
    def score_all(self, outcomes: dict[str, dict] | None = None) -> list[ConnectorMetrics]:
        registry = ConnectorRegistry()
        health = ConnectorHealthEngine()
        outcomes = outcomes or {}
        out = []
        for definition in registry.all():
            o = outcomes.get(definition.connector_id, {})
            out.append(
                health.score(
                    definition,
                    signals=int(o.get("signals", 0)),
                    companies=int(o.get("companies", 0)),
                    opportunities=int(o.get("opportunities", 0)),
                    duplicates=int(o.get("duplicates", 0)),
                    latency_ms=float(o.get("latency_ms", 0)),
                    errors=int(o.get("errors", 0)),
                    outcomes=o,
                )
            )
        out.sort(key=lambda m: (-m.roi_score, -m.quality_score, m.connector_id))
        return out
