from __future__ import annotations

from datetime import UTC, datetime

from global_opportunity_acquisition.models.types import (
    CompanyIntelligencePack,
    ConnectorBenchmark,
    ConnectorMetrics,
    DailyGOAPReport,
    GOAPAnalytics,
)
from global_opportunity_acquisition.models.types import ConnectorStatus
from global_opportunity_acquisition.connectors.catalog import connector_catalog


class AnalyticsEngine:
    def build(
        self,
        *,
        connectors: list[ConnectorMetrics],
        companies: list[CompanyIntelligencePack],
        benchmarks: list[ConnectorBenchmark],
    ) -> GOAPAnalytics:
        catalog = connector_catalog()
        active = sum(1 for c in catalog if c.status == ConnectorStatus.ACTIVE)
        pending = sum(1 for c in catalog if c.status == ConnectorStatus.PENDING_CREDENTIALS)
        intents: dict[str, int] = {}
        for pack in companies:
            for intent in pack.intents:
                intents[intent.intent.value] = intents.get(intent.intent.value, 0) + 1
        freshness_vals = [p.freshness.score for p in companies if p.freshness]
        top = [b.connector_name for b in benchmarks[:5]]
        return GOAPAnalytics(
            total_connectors=len(catalog),
            active_connectors=active,
            pending_credentials=pending,
            total_signals=sum(c.signals_found for c in connectors),
            unique_companies=len(companies),
            intents_detected=intents,
            top_sources=top,
            average_freshness=round(sum(freshness_vals) / len(freshness_vals), 2) if freshness_vals else 0.0,
            evidence=[f"companies:{len(companies)}", f"connectors:{len(catalog)}"],
        )

    def daily_report(
        self,
        analytics: GOAPAnalytics,
        benchmarks: list[ConnectorBenchmark],
        *,
        now: datetime | None = None,
    ) -> DailyGOAPReport:
        now = now or datetime.now(UTC)
        alerts = []
        for b in benchmarks:
            if b.recommendation.value == "disable_connector":
                alerts.append(f"Recommend disable: {b.connector_name}")
            if b.false_positives >= 5:
                alerts.append(f"High false positives: {b.connector_name}")
        summary = (
            f"GOAP daily: {analytics.unique_companies} companies, "
            f"{analytics.active_connectors}/{analytics.total_connectors} active connectors, "
            f"avg freshness {analytics.average_freshness}."
        )
        return DailyGOAPReport(
            generated_at=now,
            summary=summary,
            analytics=analytics,
            top_benchmarks=benchmarks[:10],
            alerts=alerts[:20],
            evidence=["report:daily", "deterministic:true"],
        )
