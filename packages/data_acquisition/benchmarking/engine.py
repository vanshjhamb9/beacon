from __future__ import annotations

from data_acquisition.models.types import ConnectorAuditItem, ConnectorBenchmark


class ConnectorBenchmarkEngine:
    def rank(self, audits: list[ConnectorAuditItem]) -> list[ConnectorBenchmark]:
        scored: list[tuple[float, ConnectorAuditItem, str]] = []
        for item in audits:
            if not item.enabled:
                continue
            opportunity_yield = float(item.opportunities_produced_24h)
            high_value_yield = float(item.high_value_opportunities_24h)
            company_rate = float(item.companies_discovered_24h)
            quality = round(
                min(
                    100.0,
                    high_value_yield * 18.0
                    + opportunity_yield * 8.0
                    + company_rate * 4.0
                    + item.extraction_quality_avg * 0.25
                    + item.coverage_score * 0.2
                    - item.duplicate_rate_24h * 0.15
                    - item.failure_rate_24h * 0.25,
                ),
                2,
            )
            explanation = (
                f"{item.source} produced {item.high_value_opportunities_24h} high-value opportunities "
                f"and {item.companies_discovered_24h} companies with extraction quality "
                f"{item.extraction_quality_avg:.1f}."
            )
            scored.append((quality, item, explanation))

        scored.sort(key=lambda row: row[0], reverse=True)
        benchmarks: list[ConnectorBenchmark] = []
        for index, (quality, item, explanation) in enumerate(scored, start=1):
            latency = float(item.average_latency_ms or 0.0)
            benchmarks.append(
                ConnectorBenchmark(
                    source=item.source,
                    quality_score=max(0.0, quality),
                    opportunity_yield=float(item.opportunities_produced_24h),
                    high_value_yield=float(item.high_value_opportunities_24h),
                    company_discovery_rate=float(item.companies_discovered_24h),
                    duplicate_rate=item.duplicate_rate_24h,
                    failure_rate=item.failure_rate_24h,
                    average_latency_ms=latency,
                    rank=index,
                    explanation=explanation,
                )
            )
        return benchmarks
