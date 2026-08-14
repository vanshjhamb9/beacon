from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.acquisition import CollectorRun
from app.models.context import BusinessContext
from app.models.enrichment import EnrichmentReport
from app.models.intelligence import ClassifiedSignal, Company, KnowledgeGraphNode
from app.models.opportunity import Opportunity
from app.models.quality import QualityReport
from app.models.raw_event import RawEvent
from app.models.revenue import SolutionMatch
from app.models.source_health import SourceHealth
from app.models.verification import VerificationReport
from app.schemas.diagnostics import (
    CollectorDiagnostic,
    DatabaseCounts,
    DiagnosticsResponse,
    QueueDiagnostic,
    StageFunnel,
    WorkerDiagnostic,
)


class DiagnosticsService:
    SOURCES = (
        "reddit",
        "rss",
        "hacker_news",
        "product_hunt",
        "github_trending",
        "indie_hackers",
        "sec_edgar",
        "devto",
    )

    def __init__(self, session: AsyncSession, redis: Redis, settings: Settings) -> None:
        self.session = session
        self.redis = redis
        self.settings = settings

    async def snapshot(self) -> DiagnosticsResponse:
        now = datetime.now(UTC)
        since_1h = now - timedelta(hours=1)
        since_24h = now - timedelta(hours=24)
        since_7d = now - timedelta(days=7)

        database = await self._database_counts(since_1h, since_24h, since_7d)
        collectors = await self._collectors(since_24h)
        queues, worker = await self._queues_and_worker()
        funnel = self._funnel(database)
        quality_reasons = await self._quality_reasons(since_24h)
        avg_quality_ms = await self._avg_quality_ms(since_24h)

        last_collection = max(
            (item.last_success_at for item in collectors if item.last_success_at),
            default=None,
        )
        last_opportunity = await self.session.scalar(select(func.max(Opportunity.updated_at)))
        last_error = next(
            (item.last_error for item in collectors if item.last_error),
            None,
        )
        top_failing = [
            item.source
            for item in sorted(
                collectors,
                key=lambda row: (row.consecutive_failures, row.health_status != "healthy"),
                reverse=True,
            )
            if item.consecutive_failures > 0 or item.health_status in {"degraded", "down", "unknown"}
        ][:5]

        return DiagnosticsResponse(
            generated_at=now,
            collectors=collectors,
            queues=queues,
            database=database,
            funnel=funnel,
            worker=worker,
            last_successful_collection=last_collection,
            last_processed_opportunity=last_opportunity,
            last_error=last_error,
            top_failing_connectors=top_failing,
            missing_env=self._missing_env(),
            quality_reason_breakdown=quality_reasons,
            average_quality_processing_ms=avg_quality_ms,
            extras={
                "collectors_enabled_flag": self.settings.feature_flags.collectors_enabled,
                "source_health_monitoring": self.settings.feature_flags.source_health_monitoring_enabled,
            },
        )

    def _enabled(self, source: str) -> bool:
        mapping = {
            "reddit": self.settings.reddit_collector.enabled,
            "rss": self.settings.rss_collector.enabled,
            "hacker_news": self.settings.hacker_news_collector.enabled,
            "product_hunt": self.settings.product_hunt_collector.enabled,
            "github_trending": self.settings.github_trending_collector.enabled,
            "indie_hackers": self.settings.indie_hackers_collector.enabled,
            "sec_edgar": self.settings.sec_edgar_collector.enabled,
            "devto": self.settings.devto_collector.enabled,
        }
        return bool(mapping.get(source, False))

    async def _collectors(self, since_24h: datetime) -> list[CollectorDiagnostic]:
        health_rows = {
            row.source: row
            for row in (
                await self.session.scalars(select(SourceHealth))
            ).all()
        }
        latest_created = (
            select(
                CollectorRun.source.label("source"),
                func.max(CollectorRun.created_at).label("max_created"),
            )
            .group_by(CollectorRun.source)
            .subquery()
        )
        run_rows = (
            await self.session.execute(
                select(CollectorRun).join(
                    latest_created,
                    (CollectorRun.source == latest_created.c.source)
                    & (CollectorRun.created_at == latest_created.c.max_created),
                )
            )
        ).scalars().all()
        latest_run = {row.source: row for row in run_rows}

        signal_counts = dict(
            (
                await self.session.execute(
                    select(RawEvent.source, func.count())
                    .where(RawEvent.created_at >= since_24h)
                    .group_by(RawEvent.source)
                )
            ).all()
        )

        result: list[CollectorDiagnostic] = []
        for source in self.SOURCES:
            health = health_rows.get(source)
            run = latest_run.get(source)
            result.append(
                CollectorDiagnostic(
                    source=source,
                    enabled=self._enabled(source),
                    health_status=(
                        (health.status.value if hasattr(health.status, "value") else str(health.status)).lower()
                        if health
                        else "unknown"
                    ),
                    consecutive_failures=int(health.consecutive_failures or 0) if health else 0,
                    average_latency_ms=health.average_latency_ms if health else None,
                    last_success_at=health.last_success_at if health else None,
                    last_failure_at=health.last_failure_at if health else None,
                    last_error=health.last_error if health else (run.error if run else None),
                    last_run_at=run.created_at if run else None,
                    last_run_success=run.success if run else None,
                    last_collected=run.collected if run else None,
                    last_emitted=run.emitted if run else None,
                    signals_24h=int(signal_counts.get(source, 0)),
                )
            )
        return result

    async def _database_counts(
        self,
        since_1h: datetime,
        since_24h: datetime,
        since_7d: datetime,
    ) -> DatabaseCounts:
        async def count(model: Any, *filters: Any) -> int:
            stmt = select(func.count()).select_from(model)
            for item in filters:
                stmt = stmt.where(item)
            return int(await self.session.scalar(stmt) or 0)

        return DatabaseCounts(
            raw_events=await count(RawEvent),
            raw_events_1h=await count(RawEvent, RawEvent.created_at >= since_1h),
            raw_events_24h=await count(RawEvent, RawEvent.created_at >= since_24h),
            raw_events_7d=await count(RawEvent, RawEvent.created_at >= since_7d),
            quality_reports=await count(QualityReport),
            quality_accepted=await count(QualityReport, QualityReport.decision == "accept"),
            quality_review=await count(QualityReport, QualityReport.decision == "review"),
            quality_rejected=await count(QualityReport, QualityReport.decision == "reject"),
            companies=await count(Company),
            classified_signals=await count(ClassifiedSignal),
            business_contexts=await count(BusinessContext),
            opportunities=await count(Opportunity),
            solution_matches=await count(SolutionMatch),
            enrichment_reports=await count(EnrichmentReport),
            verification_reports=await count(VerificationReport),
            collector_runs=await count(CollectorRun),
            knowledge_graph_nodes=await count(KnowledgeGraphNode),
        )

    async def _queues_and_worker(self) -> tuple[list[QueueDiagnostic], WorkerDiagnostic]:
        queues: list[QueueDiagnostic] = []
        redis_ok = False
        celery_len = 0
        stream_len = 0
        try:
            await self.redis.ping()
            redis_ok = True
            celery_len = int(await self.redis.llen("celery") or 0)
            stream_len = int(await self.redis.xlen(self.settings.collector_stream_name) or 0)
            queues.append(QueueDiagnostic(name="celery", length=celery_len, detail="broker default queue"))
            queues.append(
                QueueDiagnostic(
                    name=self.settings.collector_stream_name,
                    length=stream_len,
                    detail="raw event redis stream",
                )
            )
        except Exception as exc:
            queues.append(QueueDiagnostic(name="redis", length=-1, detail=str(exc)))

        worker_status = "unknown"
        scheduler_status = "unknown"
        detail = None
        if redis_ok:
            worker_status = "healthy" if celery_len < 500 else "backlogged"
            # Beat does not expose a durable heartbeat; infer from recent collector activity.
            recent_run = await self.session.scalar(
                select(func.max(CollectorRun.created_at))
            )
            if recent_run and recent_run >= datetime.now(UTC) - timedelta(minutes=15):
                scheduler_status = "healthy"
            elif recent_run:
                scheduler_status = "stale"
                detail = f"Last collector run at {recent_run.isoformat()}"
            else:
                scheduler_status = "unknown"
                detail = "No collector runs recorded yet"

        return queues, WorkerDiagnostic(
            redis_reachable=redis_ok,
            celery_queue_length=celery_len,
            raw_event_stream_length=stream_len,
            scheduler_status=scheduler_status,
            worker_status=worker_status,
            detail=detail,
        )

    def _funnel(self, database: DatabaseCounts) -> list[StageFunnel]:
        stages = [
            ("collectors→raw_events", database.collector_runs, database.raw_events_24h, "24h raw events vs run history"),
            ("raw_events→quality", database.raw_events, database.quality_reports, "quality coverage of raw events"),
            ("quality→signals", database.quality_accepted + database.quality_review, database.classified_signals, "accepted/review into classified signals"),
            ("signals→context", database.classified_signals, database.business_contexts, "context coverage"),
            ("context→opportunity", database.business_contexts, database.opportunities, "opportunity coverage"),
            ("opportunity→revenue", database.opportunities, database.solution_matches, "solution match coverage"),
            ("revenue→enrichment", database.solution_matches, database.enrichment_reports, "enrichment coverage"),
            ("enrichment→verification", database.enrichment_reports, database.verification_reports, "verification coverage"),
        ]
        funnel: list[StageFunnel] = []
        for name, entering, leaving, notes in stages:
            drop = 0.0 if entering <= 0 else round(max(0.0, (1 - (leaving / entering)) * 100), 2)
            funnel.append(
                StageFunnel(
                    stage=name,
                    entering=entering,
                    leaving=leaving,
                    drop_off_percent=drop,
                    notes=notes,
                )
            )
        return funnel

    async def _quality_reasons(self, since_24h: datetime) -> dict[str, int]:
        rows = (
            await self.session.execute(
                select(QualityReport.reason_codes).where(QualityReport.created_at >= since_24h)
            )
        ).scalars().all()
        counts: dict[str, int] = {}
        for reason_codes in rows:
            if not isinstance(reason_codes, list):
                continue
            for code in reason_codes:
                key = str(code)
                counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:20])

    async def _avg_quality_ms(self, since_24h: datetime) -> float | None:
        value = await self.session.scalar(
            select(func.avg(QualityReport.processing_time_ms)).where(
                QualityReport.created_at >= since_24h
            )
        )
        return round(float(value), 4) if value is not None else None

    def _missing_env(self) -> list[str]:
        missing: list[str] = []
        if not self.settings.builtwith_api_key:
            missing.append("BUILTWITH_API_KEY")
        if not self.settings.wappalyzer_api_key:
            missing.append("WAPPALYZER_API_KEY")
        if not self.settings.crunchbase_api_key:
            missing.append("CRUNCHBASE_API_KEY")
        return missing
