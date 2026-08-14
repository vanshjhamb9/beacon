from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.acquisition import (
    AcquisitionDailyReport,
    CollectorRun,
    ConnectorAlertRecord,
    ConnectorBenchmarkSnapshot,
)
from app.models.context import BusinessContext
from app.models.enrichment import EnrichmentReport
from app.models.intelligence import ClassifiedSignal, Company
from app.models.opportunity import Opportunity
from app.models.raw_event import RawEvent
from app.models.source_health import SourceHealth
from app.models.verification import VerificationReport
from data_acquisition.models.types import (
    AcquisitionSnapshotInput,
    ConnectorAlert,
    DailyAcquisitionReport,
)


class AcquisitionRepository:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

    def configured_sources(self) -> list[tuple[str, bool]]:
        return [
            ("reddit", self.settings.reddit_collector.enabled),
            ("rss", self.settings.rss_collector.enabled),
            ("hacker_news", self.settings.hacker_news_collector.enabled),
            ("product_hunt", self.settings.product_hunt_collector.enabled),
            ("github_trending", self.settings.github_trending_collector.enabled),
            ("indie_hackers", self.settings.indie_hackers_collector.enabled),
            ("sec_edgar", self.settings.sec_edgar_collector.enabled),
            ("devto", self.settings.devto_collector.enabled),
        ]

    async def record_run(
        self,
        *,
        source: str,
        collected: int,
        emitted: int,
        duplicates: int,
        rate_limited: bool,
        success: bool,
        latency_ms: float,
        error: str | None = None,
        trace_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> UUID:
        row = CollectorRun(
            source=source,
            collected=collected,
            emitted=emitted,
            duplicates=duplicates,
            rate_limited=rate_limited,
            success=success,
            latency_ms=latency_ms,
            error=error,
            trace_id=trace_id,
            details=details or {},
        )
        self.session.add(row)
        await self.session.flush()
        return row.id

    async def store_alerts(self, alerts: Sequence[ConnectorAlert]) -> int:
        stored = 0
        for alert in alerts:
            existing = await self.session.execute(
                select(ConnectorAlertRecord)
                .where(
                    ConnectorAlertRecord.source == alert.source,
                    ConnectorAlertRecord.code == alert.code,
                    ConnectorAlertRecord.resolved_at.is_(None),
                )
                .limit(1)
            )
            if existing.scalar_one_or_none() is not None:
                continue
            self.session.add(
                ConnectorAlertRecord(
                    source=alert.source,
                    severity=alert.severity.value,
                    code=alert.code,
                    message=alert.message,
                    consecutive_failures=alert.consecutive_failures,
                    details=alert.details,
                )
            )
            stored += 1
        await self.session.flush()
        return stored

    async def resolve_alerts_for_healthy_sources(self, healthy_sources: Sequence[str]) -> int:
        if not healthy_sources:
            return 0
        result = await self.session.execute(
            select(ConnectorAlertRecord).where(
                ConnectorAlertRecord.source.in_(list(healthy_sources)),
                ConnectorAlertRecord.resolved_at.is_(None),
            )
        )
        now = datetime.now(UTC)
        count = 0
        for row in result.scalars().all():
            row.resolved_at = now
            count += 1
        await self.session.flush()
        return count

    async def open_alerts(self) -> Sequence[ConnectorAlertRecord]:
        result = await self.session.execute(
            select(ConnectorAlertRecord)
            .where(ConnectorAlertRecord.resolved_at.is_(None))
            .order_by(ConnectorAlertRecord.created_at.desc())
            .limit(200)
        )
        return result.scalars().all()

    async def store_daily_report(self, report: DailyAcquisitionReport) -> UUID:
        row = AcquisitionDailyReport(
            report_date=date.fromisoformat(report.report_date),
            new_companies=report.new_companies,
            new_opportunities=report.new_opportunities,
            high_value_opportunities=report.high_value_opportunities,
            signals_collected=report.signals_collected,
            signals_persisted=report.signals_persisted,
            duplicate_rate=report.duplicate_rate,
            coverage_growth=report.coverage_growth,
            missing_data_trends=report.missing_data_trends,
            collector_performance=[item.model_dump(mode="json") for item in report.collector_performance],
            benchmarks=[item.model_dump(mode="json") for item in report.benchmarks],
            alerts=[item.model_dump(mode="json") for item in report.alerts],
            summary=report.summary,
            payload=report.model_dump(mode="json"),
        )
        self.session.add(row)
        await self.session.flush()
        for benchmark in report.benchmarks:
            self.session.add(
                ConnectorBenchmarkSnapshot(
                    source=benchmark.source,
                    report_id=row.id,
                    quality_score=benchmark.quality_score,
                    opportunity_yield=benchmark.opportunity_yield,
                    high_value_yield=benchmark.high_value_yield,
                    company_discovery_rate=benchmark.company_discovery_rate,
                    duplicate_rate=benchmark.duplicate_rate,
                    failure_rate=benchmark.failure_rate,
                    average_latency_ms=benchmark.average_latency_ms,
                    rank=benchmark.rank,
                    explanation=benchmark.explanation,
                )
            )
        await self.session.flush()
        return row.id

    async def latest_daily_report(self) -> AcquisitionDailyReport | None:
        result = await self.session.execute(
            select(AcquisitionDailyReport).order_by(AcquisitionDailyReport.report_date.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def build_snapshots(self, *, since: datetime | None = None) -> list[AcquisitionSnapshotInput]:
        window_start = since or (datetime.now(UTC) - timedelta(hours=24))
        health_rows = {
            row.source: row
            for row in (
                await self.session.execute(select(SourceHealth))
            ).scalars().all()
        }
        runs = (
            await self.session.execute(select(CollectorRun).where(CollectorRun.created_at >= window_start))
        ).scalars().all()

        by_source: dict[str, list[CollectorRun]] = defaultdict(list)
        for run in runs:
            by_source[run.source].append(run)

        company_counts = await self._companies_by_source(window_start)
        opportunity_counts, high_value_counts = await self._opportunities_by_source(window_start)
        extraction_quality = await self._extraction_quality_by_source(window_start)

        snapshots: list[AcquisitionSnapshotInput] = []
        for source, enabled in self.configured_sources():
            source_runs = by_source.get(source, [])
            health = health_rows.get(source)
            collected = sum(run.collected for run in source_runs)
            emitted = sum(run.emitted for run in source_runs)
            duplicates = sum(run.duplicates for run in source_runs)
            snapshots.append(
                AcquisitionSnapshotInput(
                    source=source,
                    enabled=enabled,
                    health_status=(
                        health.status.value if health is not None and hasattr(health.status, "value") else (
                            str(health.status) if health is not None else "unknown"
                        )
                    ),
                    consecutive_failures=health.consecutive_failures if health else 0,
                    average_latency_ms=health.average_latency_ms if health else None,
                    last_success_at=health.last_success_at if health else None,
                    last_failure_at=health.last_failure_at if health else None,
                    last_error=health.last_error if health else None,
                    runs_24h=len(source_runs),
                    successful_runs_24h=sum(1 for run in source_runs if run.success),
                    failed_runs_24h=sum(1 for run in source_runs if not run.success),
                    collected_24h=collected,
                    emitted_24h=emitted,
                    duplicates_24h=duplicates,
                    rate_limited_runs_24h=sum(1 for run in source_runs if run.rate_limited),
                    companies_discovered_24h=company_counts.get(source, 0),
                    opportunities_produced_24h=opportunity_counts.get(source, 0),
                    high_value_opportunities_24h=high_value_counts.get(source, 0),
                    extraction_quality_avg=extraction_quality.get(source, 0.0),
                )
            )
        return snapshots

    async def platform_counts(self, *, since: datetime) -> dict[str, int | float]:
        companies = await self.session.execute(
            select(func.count(Company.id)).where(Company.created_at >= since)
        )
        opportunities = await self.session.execute(
            select(func.count(Opportunity.id)).where(Opportunity.created_at >= since)
        )
        high_value = await self.session.execute(
            select(func.count(Opportunity.id)).where(
                Opportunity.created_at >= since,
                Opportunity.opportunity_score >= self.settings.acquisition_high_value_opportunity_score,
            )
        )
        raw_total = await self.session.execute(
            select(func.count(RawEvent.id)).where(RawEvent.created_at >= since)
        )
        previous_companies = await self.session.execute(
            select(func.count(Company.id)).where(Company.created_at < since)
        )
        runs = (
            await self.session.execute(select(CollectorRun).where(CollectorRun.created_at >= since))
        ).scalars().all()
        collected = sum(run.collected for run in runs)
        emitted = sum(run.emitted for run in runs)
        duplicates = sum(run.duplicates for run in runs)
        processed = emitted + duplicates
        duplicate_rate = (duplicates / processed) * 100.0 if processed else 0.0
        return {
            "new_companies": int(companies.scalar_one() or 0),
            "new_opportunities": int(opportunities.scalar_one() or 0),
            "high_value_opportunities": int(high_value.scalar_one() or 0),
            "signals_collected": collected,
            "signals_persisted": int(raw_total.scalar_one() or 0),
            "duplicate_rate": duplicate_rate,
            "previous_companies": int(previous_companies.scalar_one() or 0),
        }

    async def missing_data_trends(self) -> dict[str, int]:
        trends: dict[str, int] = {}
        companies_without_domain = await self.session.execute(
            select(func.count(Company.id)).where(
                and_(Company.primary_domain.is_(None), Company.deleted_at.is_(None))
            )
        )
        trends["companies_missing_domain"] = int(companies_without_domain.scalar_one() or 0)

        enrichment_missing = await self.session.execute(
            select(func.count(Opportunity.id)).where(
                ~Opportunity.id.in_(select(EnrichmentReport.opportunity_id))
            )
        )
        trends["opportunities_missing_enrichment"] = int(enrichment_missing.scalar_one() or 0)

        verification_missing = await self.session.execute(
            select(func.count(EnrichmentReport.id)).where(
                ~EnrichmentReport.id.in_(select(VerificationReport.enrichment_report_id))
            )
        )
        trends["enrichments_missing_verification"] = int(verification_missing.scalar_one() or 0)
        return trends

    async def _companies_by_source(self, since: datetime) -> dict[str, int]:
        result = await self.session.execute(
            select(RawEvent.source, func.count(func.distinct(ClassifiedSignal.company_id)))
            .join(ClassifiedSignal, ClassifiedSignal.event_id == RawEvent.id)
            .where(RawEvent.created_at >= since, ClassifiedSignal.company_id.is_not(None))
            .group_by(RawEvent.source)
        )
        return {str(source): int(count) for source, count in result.all()}

    async def _opportunities_by_source(self, since: datetime) -> tuple[dict[str, int], dict[str, int]]:
        result = await self.session.execute(
            select(
                RawEvent.source,
                Opportunity.id,
                Opportunity.opportunity_score,
            )
            .join(BusinessContext, BusinessContext.raw_event_id == RawEvent.id)
            .join(Opportunity, Opportunity.company_id == BusinessContext.company_id)
            .where(
                RawEvent.created_at >= since,
                Opportunity.created_at >= since,
            )
        )
        opportunity_sets: dict[str, set[UUID]] = defaultdict(set)
        high_value_sets: dict[str, set[UUID]] = defaultdict(set)
        threshold = self.settings.acquisition_high_value_opportunity_score
        for source, opportunity_id, score in result.all():
            opportunity_sets[str(source)].add(opportunity_id)
            if float(score) >= threshold:
                high_value_sets[str(source)].add(opportunity_id)
        return (
            {source: len(ids) for source, ids in opportunity_sets.items()},
            {source: len(ids) for source, ids in high_value_sets.items()},
        )

    async def _extraction_quality_by_source(self, since: datetime) -> dict[str, float]:
        result = await self.session.execute(
            select(RawEvent.source, RawEvent.event_metadata).where(RawEvent.created_at >= since).limit(5_000)
        )
        buckets: dict[str, list[float]] = defaultdict(list)
        for source, metadata in result.all():
            if isinstance(metadata, dict):
                value = metadata.get("extraction_quality")
                if isinstance(value, (int, float)):
                    buckets[str(source)].append(float(value))
        return {
            source: round(sum(values) / len(values), 2) if values else 0.0
            for source, values in buckets.items()
        }
