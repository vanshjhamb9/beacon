from __future__ import annotations

from global_opportunity_acquisition.connectors.catalog import connector_catalog
from global_opportunity_acquisition.models.types import BenchmarkAction, ConnectorBenchmark


class BenchmarkingEngine:
    """Every source competes — weekly ranking with frequency recommendations."""

    def rank(self, outcomes: dict[str, dict] | None = None) -> list[ConnectorBenchmark]:
        outcomes = outcomes or {}
        rows: list[ConnectorBenchmark] = []
        for definition in connector_catalog():
            o = outcomes.get(definition.connector_id, {})
            qualified = int(o.get("qualified_opportunities", o.get("opportunities", 0)))
            meetings = int(o.get("meetings_booked", o.get("meetings", 0)))
            reply_rate = float(o.get("reply_rate", 0.0))
            proposal_rate = float(o.get("proposal_rate", 0.0))
            close_rate = float(o.get("close_rate", 0.0))
            revenue = float(o.get("revenue_generated", o.get("revenue", 0.0)))
            avg_quality = float(o.get("average_quality", o.get("quality", 50.0)))
            false_positives = int(o.get("false_positives", 0))
            latency = float(o.get("latency_ms", 0.0))
            coverage = float(o.get("coverage", 0.0))
            composite = (
                qualified * 3.0
                + meetings * 8.0
                + reply_rate
                + proposal_rate * 1.5
                + close_rate * 2.0
                + revenue * 0.01
                + avg_quality
                - false_positives * 5.0
                - latency * 0.01
                + coverage * 0.2
            )
            rows.append(
                (
                    composite,
                    ConnectorBenchmark(
                        connector_id=definition.connector_id,
                        connector_name=definition.connector_name,
                        qualified_opportunities=qualified,
                        meetings_booked=meetings,
                        reply_rate=reply_rate,
                        proposal_rate=proposal_rate,
                        close_rate=close_rate,
                        revenue_generated=revenue,
                        average_quality=avg_quality,
                        false_positives=false_positives,
                        latency_ms=latency,
                        coverage=coverage,
                        rank=0,
                        recommendation=BenchmarkAction.MAINTAIN,
                        evidence=[f"composite:{round(composite, 2)}"],
                    ),
                )
            )
        rows.sort(key=lambda x: (-x[0], x[1].connector_id))
        ranked: list[ConnectorBenchmark] = []
        for i, (composite, bench) in enumerate(rows, start=1):
            action = BenchmarkAction.MAINTAIN
            if definition_disabled(bench.connector_id):
                action = BenchmarkAction.DISABLE_CONNECTOR
            elif composite >= 80 and bench.qualified_opportunities >= 3:
                action = BenchmarkAction.INCREASE_FREQUENCY
            elif composite < 15 and bench.false_positives >= 3:
                action = BenchmarkAction.REDUCE_FREQUENCY
            elif composite < 5 and bench.qualified_opportunities == 0 and bench.false_positives >= 5:
                action = BenchmarkAction.DISABLE_CONNECTOR
            ranked.append(bench.model_copy(update={"rank": i, "recommendation": action, "evidence": bench.evidence + [f"rank:{i}"]}))
        return ranked


def definition_disabled(connector_id: str) -> bool:
    from global_opportunity_acquisition.connectors.registry import ConnectorRegistry
    from global_opportunity_acquisition.models.types import ConnectorStatus

    d = ConnectorRegistry().get(connector_id)
    return d is not None and d.status in {ConnectorStatus.DISABLED, ConnectorStatus.PENDING_CREDENTIALS}
