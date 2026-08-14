"""App service for Beacon Operations Center — queries live pipeline tables."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.acquisition import CollectorRun
from app.models.decision import DecisionMaker
from app.models.enrichment import CompanyContact
from app.models.entity_resolution_erowd import OfficialWebsiteRow
from app.models.identity_graph import IgfCanonicalCompany, IgfIdentityCandidate
from app.models.intelligence import Company
from app.models.operation_first_customer import OfcOutreachRecord
from app.models.operations_center import (
    ConnectorHealthRow,
    IngestionEvent,
    OperationSnapshot,
    PipelineStageMetric,
    WorkerHealthRow,
)
from app.models.outcomes import Deal, Meeting
from app.models.raw_event import RawEvent
from app.models.revenue_readiness_perfection import RrpCompanyProfile
from app.models.source_health import SourceHealth
from operations_center.collector_monitor import summarize_collector_activity, top_failure_reasons
from operations_center.connector_monitor import normalize_connector_name, score_connector
from operations_center.daily_snapshot import build_hourly_timeline, snapshot_payload
from operations_center.dashboard_service import DashboardService
from operations_center.models import FeedEvent, SourceMapNode
from operations_center.queue_monitor import estimate_queue_sizes_from_celery


class OperationsCenterService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        settings: Settings | None = None,
        inspect_payload: dict[str, Any] | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.inspect_payload = inspect_payload or {}
        self.dashboard = DashboardService()

    async def live(self) -> dict[str, Any]:
        dash = await self._build_dashboard()
        return self.dashboard.to_dict(dash)

    async def connectors(self) -> dict[str, Any]:
        dash = await self._build_dashboard()
        return {
            "generated_at": dash.generated_at.isoformat(),
            "connectors": self.dashboard.to_dict(dash)["connectors"],
            "scoring_version": dash.scoring_version,
        }

    async def workers(self) -> dict[str, Any]:
        dash = await self._build_dashboard()
        return {
            "generated_at": dash.generated_at.isoformat(),
            "workers": self.dashboard.to_dict(dash)["workers"],
            "scoring_version": dash.scoring_version,
        }

    async def pipeline(self) -> dict[str, Any]:
        dash = await self._build_dashboard()
        payload = self.dashboard.to_dict(dash)
        return {
            "generated_at": dash.generated_at.isoformat(),
            "pipeline": self.dashboard.serialize_pipeline(dash.pipeline),
            "conversions": payload["conversions"],
            "source_map": payload["source_map"],
            "scoring_version": dash.scoring_version,
        }

    async def feed(self, *, limit: int = 40) -> dict[str, Any]:
        events = await self._load_feed(limit=limit)
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "kind": e.kind,
                    "message": e.message,
                    "collector": e.collector,
                    "company": e.company,
                    "status": e.status,
                    "count": e.count,
                }
                for e in events
            ],
        }

    async def queues(self) -> dict[str, Any]:
        sizes = estimate_queue_sizes_from_celery(self.inspect_payload)
        dash = await self._build_dashboard()
        return {
            "generated_at": dash.generated_at.isoformat(),
            "queues": self.dashboard.to_dict(dash)["queues"],
            "raw_sizes": sizes,
        }

    async def health(self) -> dict[str, Any]:
        dash = await self._build_dashboard()
        return {
            "generated_at": dash.generated_at.isoformat(),
            "health": self.dashboard.to_dict(dash)["health"],
            "scoring_version": dash.scoring_version,
        }

    async def daily(self) -> dict[str, Any]:
        dash = await self._build_dashboard()
        payload = self.dashboard.to_dict(dash)
        return {
            "generated_at": dash.generated_at.isoformat(),
            "timeline": payload["timeline"],
            "progress": payload["progress"],
            "revenue": payload["revenue"],
            "cards": payload["cards"],
            "scoring_version": dash.scoring_version,
        }

    async def refresh_metrics(self) -> dict[str, Any]:
        """Persist live stage counters + connector/worker health (append-only metrics)."""
        current, today, yesterday, hour = await self._stage_counts()
        now = datetime.now(UTC)
        for stage, count in current.items():
            self.session.add(
                PipelineStageMetric(
                    id=uuid.uuid4(),
                    stage=stage,
                    count=int(count),
                    today=int(today.get(stage, 0)),
                    hour=int(hour.get(stage, 0)),
                    payload={"yesterday": int(yesterday.get(stage, 0))},
                )
            )

        connectors = await self._build_connectors()
        for view in connectors:
            existing = await self.session.scalar(
                select(ConnectorHealthRow).where(
                    ConnectorHealthRow.connector == view.connector,
                    ConnectorHealthRow.deleted_at.is_(None),
                )
            )
            if existing:
                existing.enabled = view.enabled
                existing.healthy = view.healthy
                existing.last_run = view.last_run
                existing.last_success = view.last_success
                existing.last_failure = view.last_failure
                existing.success_rate = view.success_rate
                existing.error_count = view.error_count
                existing.records_today = view.records_today
                existing.records_total = view.records_total
                existing.avg_runtime = view.avg_runtime
                existing.rate_limited = view.rate_limited
                existing.detail = view.detail
                existing.payload = {"status": view.status}
            else:
                self.session.add(
                    ConnectorHealthRow(
                        id=uuid.uuid4(),
                        connector=view.connector,
                        enabled=view.enabled,
                        healthy=view.healthy,
                        last_run=view.last_run,
                        last_success=view.last_success,
                        last_failure=view.last_failure,
                        success_rate=view.success_rate,
                        error_count=view.error_count,
                        records_today=view.records_today,
                        records_total=view.records_total,
                        avg_runtime=view.avg_runtime,
                        rate_limited=view.rate_limited,
                        detail=view.detail,
                        payload={"status": view.status},
                    )
                )

        queue_sizes = estimate_queue_sizes_from_celery(self.inspect_payload)
        from operations_center.worker_monitor import build_worker_views

        for view in build_worker_views(
            inspect_payload=self.inspect_payload,
            queue_sizes=queue_sizes,
        ):
            existing = await self.session.scalar(
                select(WorkerHealthRow).where(
                    WorkerHealthRow.worker_name == view.worker_name,
                    WorkerHealthRow.deleted_at.is_(None),
                )
            )
            if existing:
                existing.running = view.running
                existing.queue_size = view.queue_size
                existing.jobs_completed = view.jobs_completed
                existing.jobs_failed = view.jobs_failed
                existing.avg_duration = view.avg_duration
                existing.last_execution = view.last_execution or now
                existing.payload = {"status": view.status}
            else:
                self.session.add(
                    WorkerHealthRow(
                        id=uuid.uuid4(),
                        worker_name=view.worker_name,
                        running=view.running,
                        queue_size=view.queue_size,
                        jobs_completed=view.jobs_completed,
                        jobs_failed=view.jobs_failed,
                        avg_duration=view.avg_duration,
                        last_execution=view.last_execution or now,
                        payload={"status": view.status},
                    )
                )

        await self.session.flush()
        return {
            "ok": True,
            "stages": current,
            "connectors": len(connectors),
            "refreshed_at": now.isoformat(),
        }

    async def take_hourly_snapshot(self) -> dict[str, Any]:
        current, _, _, _ = await self._stage_counts()
        payload = snapshot_payload(
            signals=current.get("signals", 0),
            verified_companies=current.get("verified_websites", 0),
            emails=current.get("emails", 0),
            decision_makers=current.get("decision_makers", 0),
            sales_ready=current.get("sales_ready", 0),
            revenue_ready=current.get("revenue_ready", 0),
        )
        row = OperationSnapshot(id=uuid.uuid4(), **payload, payload={"kind": "hourly"})
        self.session.add(row)
        await self.session.flush()
        return {"ok": True, "snapshot": payload, "id": str(row.id)}

    async def emit_ingestion_event(
        self,
        *,
        collector: str,
        status: str,
        company: str | None = None,
        reason: str | None = None,
        duration: float | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = IngestionEvent(
            id=uuid.uuid4(),
            collector=normalize_connector_name(collector),
            company=company,
            status=status,
            reason=reason,
            duration=duration,
            payload=payload or {},
        )
        self.session.add(row)
        await self.session.flush()
        return {"ok": True, "id": str(row.id)}

    async def _build_dashboard(self) -> Any:
        current, today, yesterday, hour = await self._stage_counts()
        trends = await self._seven_day_trends()
        connectors = await self._build_connectors()
        queue_sizes = estimate_queue_sizes_from_celery(self.inspect_payload)
        feed = await self._load_feed(limit=40)
        timeline = await self._load_timeline()
        source_map = await self._source_map()
        started_rr = await self._started_day_revenue_ready()
        pipeline_value, meetings, won = await self._revenue_numbers()
        events = await self._recent_ingestion_dicts(limit=500)
        failures = top_failure_reasons(events, limit=10)

        return self.dashboard.build(
            current=current,
            today=today,
            yesterday=yesterday,
            hour=hour,
            trends=trends,
            connectors=connectors,
            workers_inspect=self.inspect_payload,
            queue_sizes=queue_sizes,
            failures=failures,
            feed=feed,
            timeline=timeline,
            started_revenue_ready=started_rr,
            pipeline_value=pipeline_value,
            meetings=meetings,
            won=won,
            source_map=source_map,
            ingestion_events=events,
        )

    async def _stage_counts(
        self,
    ) -> tuple[dict[str, int], dict[str, int], dict[str, int], dict[str, int]]:
        now = datetime.now(UTC)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = day_start - timedelta(days=1)
        hour_start = now.replace(minute=0, second=0, microsecond=0)

        current = await self._pipeline_totals()
        today = await self._pipeline_totals(since=day_start)
        yesterday = await self._pipeline_totals(since=yesterday_start, until=day_start)
        hour = await self._pipeline_totals(since=hour_start)
        return current, today, yesterday, hour

    async def _pipeline_totals(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> dict[str, int]:
        async def _c(model: type[Any], *clauses: Any) -> int:
            filters = list(clauses)
            if since is not None:
                filters.append(model.created_at >= since)
            if until is not None:
                filters.append(model.created_at < until)
            return await self._count(model, *filters)

        email_kinds = CompanyContact.kind.in_(
            ["email", "work_email", "business_email", "company_email", "role_based_email"]
        )
        contacted_statuses = OfcOutreachRecord.status.in_(
            ["CONTACTED", "REPLIED", "MEETING_BOOKED", "PROPOSAL_SENT", "NEGOTIATION", "WON"]
        )

        totals = {
            "signals": await _c(RawEvent),
            "identity_candidates": await _c(IgfIdentityCandidate),
            "verified_websites": await _c(
                OfficialWebsiteRow,
                OfficialWebsiteRow.verified_at.is_not(None),
            ),
            "companies": await _c(Company),
            "emails": await _c(CompanyContact, email_kinds),
            "decision_makers": await _c(DecisionMaker),
            "sales_ready": await _c(RrpCompanyProfile, RrpCompanyProfile.sales_ready.is_(True)),
            "revenue_ready": await _c(
                RrpCompanyProfile,
                RrpCompanyProfile.revenue_ready.is_(True),
            ),
            "contacted": await _c(OfcOutreachRecord, contacted_statuses),
            "meetings": await _c(Meeting),
            "won": await _c(OfcOutreachRecord, OfcOutreachRecord.status == "WON"),
        }
        if since is None and until is None:
            deals_won = await self._count(
                Deal,
                or_(
                    Deal.status.in_(["won", "WON", "closed_won", "CLOSED_WON"]),
                    Deal.closed_at.is_not(None),
                ),
            )
            if deals_won:
                totals["won"] = deals_won
        return totals

    async def _seven_day_trends(self) -> dict[str, list[int]]:
        """Prefer hourly/daily snapshots; avoid ~40 COUNT queries on the hot path."""
        now = datetime.now(UTC)
        week_start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        snaps = (
            await self.session.execute(
                select(OperationSnapshot)
                .where(
                    OperationSnapshot.deleted_at.is_(None),
                    OperationSnapshot.created_at >= week_start,
                )
                .order_by(OperationSnapshot.created_at.asc())
            )
        ).scalars().all()

        day_buckets: dict[str, dict[str, int]] = {
            (week_start + timedelta(days=i)).date().isoformat(): {
                "signals": 0,
                "verified_websites": 0,
                "emails": 0,
                "decision_makers": 0,
                "sales_ready": 0,
                "revenue_ready": 0,
            }
            for i in range(7)
        }
        for snap in snaps:
            key = snap.created_at.astimezone(UTC).date().isoformat()
            if key not in day_buckets:
                continue
            # Keep the latest snapshot values for that calendar day.
            day_buckets[key] = {
                "signals": int(snap.signals or 0),
                "verified_websites": int(snap.verified_companies or 0),
                "emails": int(snap.emails or 0),
                "decision_makers": int(snap.decision_makers or 0),
                "sales_ready": int(snap.sales_ready or 0),
                "revenue_ready": int(snap.revenue_ready or 0),
            }

        trends: dict[str, list[int]] = {
            "signals": [],
            "verified_websites": [],
            "emails": [],
            "decision_makers": [],
            "sales_ready": [],
            "revenue_ready": [],
        }
        for i in range(7):
            key = (week_start + timedelta(days=i)).date().isoformat()
            bucket = day_buckets[key]
            for stage, values in trends.items():
                values.append(int(bucket.get(stage, 0)))
        return trends

    async def _build_connectors(self) -> list[Any]:
        settings = self.settings
        enabled_map = {
            "reddit": settings.reddit_collector.enabled,
            "rss": settings.rss_collector.enabled,
            "hacker_news": settings.hacker_news_collector.enabled,
            "product_hunt": settings.product_hunt_collector.enabled,
            "github_trending": settings.github_trending_collector.enabled,
            "indie_hackers": settings.indie_hackers_collector.enabled,
            "sec_edgar": settings.sec_edgar_collector.enabled,
            "devto": settings.devto_collector.enabled,
            "hunter": False,
            "linkedin": False,
            "apollo": bool(getattr(settings, "apollo_api_key", None)),
            "people_data_labs": bool(getattr(settings, "people_data_labs_api_key", None)),
            "crunchbase": bool(getattr(settings, "crunchbase_api_key", None)),
            "builtwith": bool(getattr(settings, "builtwith_api_key", None)),
            "wappalyzer": bool(getattr(settings, "wappalyzer_api_key", None)),
            "clearbit": False,
            "google_maps": False,
            "yc": True,
            "app_store": True,
            "google_play": True,
        }
        if not settings.feature_flags.collectors_enabled:
            for key in list(enabled_map):
                if key in {
                    "reddit",
                    "rss",
                    "hacker_news",
                    "product_hunt",
                    "github_trending",
                    "indie_hackers",
                    "sec_edgar",
                    "devto",
                }:
                    enabled_map[key] = False

        day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        runs = (
            await self.session.execute(
                select(CollectorRun)
                .where(CollectorRun.deleted_at.is_(None))
                .order_by(CollectorRun.created_at.desc())
                .limit(200)
            )
        ).scalars().all()

        by_source: dict[str, list[CollectorRun]] = {}
        for run in runs:
            by_source.setdefault(normalize_connector_name(run.source), []).append(run)

        health_rows = (
            await self.session.execute(
                select(SourceHealth).where(SourceHealth.deleted_at.is_(None))
            )
        ).scalars().all()
        health_by_source = {normalize_connector_name(r.source): r for r in health_rows}

        events = await self._recent_ingestion_dicts(limit=1000)
        event_summary = summarize_collector_activity(events)

        views = []
        all_names = set(enabled_map) | set(by_source) | set(health_by_source) | set(event_summary)
        for name in sorted(all_names):
            source_runs = by_source.get(name, [])
            today_runs = [r for r in source_runs if r.created_at and r.created_at >= day_start]
            success_runs = [r for r in source_runs if r.success]
            fail_runs = [r for r in source_runs if not r.success]
            total = len(source_runs) or 1
            success_rate = (len(success_runs) / total) * 100.0 if source_runs else 0.0
            avg_runtime = 0.0
            if source_runs:
                avg_runtime = sum(float(r.latency_ms or 0.0) for r in source_runs[:50]) / min(len(source_runs), 50) / 1000.0
            rate_limited = any(r.rate_limited for r in today_runs)
            last_run = source_runs[0].created_at if source_runs else None
            last_success = next((r.created_at for r in source_runs if r.success), None)
            last_failure = next((r.created_at for r in source_runs if not r.success), None)
            health = health_by_source.get(name)
            if health:
                last_success = health.last_success_at or last_success
                last_failure = health.last_failure_at or last_failure
            records_today = sum(int(r.emitted or 0) for r in today_runs)
            records_total = sum(int(r.emitted or 0) for r in source_runs)
            detail = ""
            if rate_limited:
                detail = "Rate limited"
            elif fail_runs and fail_runs[0].error:
                detail = str(fail_runs[0].error)[:240]
            elif not enabled_map.get(name, False):
                detail = "Not configured — reserved for future integration"
            ev = event_summary.get(name)
            if ev and not source_runs:
                success_rate = float(ev.get("success_rate") or 0.0)
                avg_runtime = float(ev.get("avg_runtime") or 0.0)
                records_today = int(ev.get("success") or 0)
                last_run = ev.get("last_run") or last_run
                last_success = ev.get("last_success") or last_success
                last_failure = ev.get("last_failure") or last_failure

            views.append(
                score_connector(
                    connector=name,
                    enabled=bool(enabled_map.get(name, False) or source_runs),
                    records_today=records_today,
                    records_total=records_total,
                    success_rate=success_rate,
                    error_count=len(fail_runs),
                    avg_runtime=avg_runtime,
                    rate_limited=rate_limited,
                    last_run=last_run,
                    last_success=last_success,
                    last_failure=last_failure,
                    detail=detail,
                )
            )
        return views

    async def _load_feed(self, *, limit: int = 40) -> list[FeedEvent]:
        rows = (
            await self.session.execute(
                select(IngestionEvent)
                .where(IngestionEvent.deleted_at.is_(None))
                .order_by(IngestionEvent.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        out: list[FeedEvent] = []
        for row in rows:
            company = row.company or ""
            msg = f"{row.collector} {row.status}"
            if company:
                msg = f"{row.collector} {row.status} — {company}"
            if row.reason:
                msg = f"{msg} ({row.reason})"
            out.append(
                FeedEvent(
                    timestamp=row.created_at,
                    kind=row.status,
                    message=msg,
                    collector=row.collector,
                    company=row.company,
                    status=row.status,
                    count=(row.payload or {}).get("count"),
                )
            )
        if out:
            return out

        # Fallback: recent collector runs when ingestion_events is empty.
        runs = (
            await self.session.execute(
                select(CollectorRun)
                .where(CollectorRun.deleted_at.is_(None))
                .order_by(CollectorRun.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        for run in runs:
            status = "collected" if run.success else "failed"
            out.append(
                FeedEvent(
                    timestamp=run.created_at,
                    kind=status,
                    message=f"{run.source} {status} {run.emitted} signals",
                    collector=run.source,
                    status=status,
                    count=run.emitted,
                )
            )
        return out

    async def _load_timeline(self) -> list[Any]:
        day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        snaps = (
            await self.session.execute(
                select(OperationSnapshot)
                .where(
                    OperationSnapshot.deleted_at.is_(None),
                    OperationSnapshot.created_at >= day_start,
                )
                .order_by(OperationSnapshot.created_at.asc())
            )
        ).scalars().all()
        points = [
            {
                "created_at": s.created_at,
                "signals": s.signals,
                "verified_companies": s.verified_companies,
                "emails": s.emails,
                "decision_makers": s.decision_makers,
                "sales_ready": s.sales_ready,
                "revenue_ready": s.revenue_ready,
            }
            for s in snaps
        ]
        if not points:
            # Derive coarse hourly buckets from live today counters per hour via stage metrics.
            metrics = (
                await self.session.execute(
                    select(PipelineStageMetric)
                    .where(
                        PipelineStageMetric.deleted_at.is_(None),
                        PipelineStageMetric.created_at >= day_start,
                    )
                    .order_by(PipelineStageMetric.created_at.asc())
                )
            ).scalars().all()
            for m in metrics:
                key = {
                    "signals": "signals",
                    "verified_websites": "verified_companies",
                    "emails": "emails",
                    "decision_makers": "decision_makers",
                    "sales_ready": "sales_ready",
                    "revenue_ready": "revenue_ready",
                }.get(m.stage)
                if not key:
                    continue
                points.append({"created_at": m.created_at, key: m.hour or m.today or m.count})
        return build_hourly_timeline(points, day_start=day_start)

    async def _source_map(self) -> list[SourceMapNode]:
        """All-time per-connector funnel so RR is never shown without matching history."""
        signal_rows = (
            await self.session.execute(
                select(RawEvent.source, func.count())
                .where(RawEvent.deleted_at.is_(None))
                .group_by(RawEvent.source)
            )
        ).all()
        verified_rows = (
            await self.session.execute(
                select(OfficialWebsiteRow.source, func.count())
                .where(
                    OfficialWebsiteRow.deleted_at.is_(None),
                    OfficialWebsiteRow.verified_at.is_not(None),
                )
                .group_by(OfficialWebsiteRow.source)
            )
        ).all()
        email_rows = (
            await self.session.execute(
                select(CompanyContact.source, func.count())
                .where(
                    CompanyContact.deleted_at.is_(None),
                    CompanyContact.kind.in_(
                        ["email", "work_email", "business_email", "company_email", "role_based_email"]
                    ),
                )
                .group_by(CompanyContact.source)
            )
        ).all()
        dm_rows = (
            await self.session.execute(
                select(DecisionMaker.source, func.count())
                .where(DecisionMaker.deleted_at.is_(None))
                .group_by(DecisionMaker.source)
            )
        ).all()

        # RR only for revenue-ready companies, attributed to primary IGF collector.
        rr_by_source: dict[str, int] = {}
        rr_igf = (
            await self.session.execute(
                select(IgfCanonicalCompany)
                .join(
                    RrpCompanyProfile,
                    RrpCompanyProfile.company_id == IgfCanonicalCompany.company_id,
                )
                .where(
                    RrpCompanyProfile.deleted_at.is_(None),
                    RrpCompanyProfile.revenue_ready.is_(True),
                    IgfCanonicalCompany.deleted_at.is_(None),
                )
            )
        ).scalars().all()
        for company in rr_igf:
            collectors = list(company.collectors or [])
            primary = collectors[0] if collectors else "unknown"
            key = normalize_connector_name(str(primary))
            rr_by_source[key] = rr_by_source.get(key, 0) + 1

        def _map(rows: list[Any]) -> dict[str, int]:
            out: dict[str, int] = {}
            for source, count in rows:
                key = normalize_connector_name(str(source))
                out[key] = out.get(key, 0) + int(count or 0)
            return out

        signals = _map(list(signal_rows))
        verified = _map(list(verified_rows))
        emails = _map(list(email_rows))
        dms = _map(list(dm_rows))

        names = set(signals) | set(verified) | set(emails) | set(dms) | set(rr_by_source)

        return [
            SourceMapNode(
                connector=name,
                signals=signals.get(name, 0),
                verified=verified.get(name, 0),
                emails=emails.get(name, 0),
                decision_makers=dms.get(name, 0),
                revenue_ready=rr_by_source.get(name, 0),
            )
            for name in sorted(names)
            if signals.get(name, 0)
            or verified.get(name, 0)
            or emails.get(name, 0)
            or dms.get(name, 0)
            or rr_by_source.get(name, 0)
        ]

    async def _started_day_revenue_ready(self) -> int:
        day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        snap = await self.session.scalar(
            select(OperationSnapshot)
            .where(
                OperationSnapshot.deleted_at.is_(None),
                OperationSnapshot.created_at >= day_start,
            )
            .order_by(OperationSnapshot.created_at.asc())
            .limit(1)
        )
        if snap:
            return int(snap.revenue_ready or 0)
        # Fallback: current minus today's additions approximates start-of-day.
        current = await self._count(
            RrpCompanyProfile,
            RrpCompanyProfile.revenue_ready.is_(True),
        )
        today = await self._count_since(
            RrpCompanyProfile,
            day_start,
            RrpCompanyProfile.revenue_ready.is_(True),
        )
        return max(current - today, 0)

    async def _revenue_numbers(self) -> tuple[float, int, int]:
        pipeline = await self.session.scalar(
            select(func.coalesce(func.sum(OfcOutreachRecord.pipeline_value), 0.0)).where(
                OfcOutreachRecord.deleted_at.is_(None),
                OfcOutreachRecord.status.notin_(["LOST", "PAUSED"]),
            )
        )
        meetings = await self._count(Meeting)
        ofc_meetings = await self._count(
            OfcOutreachRecord,
            OfcOutreachRecord.status == "MEETING_BOOKED",
        )
        won = await self._count(OfcOutreachRecord, OfcOutreachRecord.status == "WON")
        deals_won = await self._count(
            Deal,
            or_(Deal.status.in_(["won", "WON", "closed_won", "CLOSED_WON"]), Deal.closed_at.is_not(None)),
        )
        return float(pipeline or 0.0), max(int(meetings or 0), int(ofc_meetings or 0)), max(int(won or 0), int(deals_won or 0))

    async def _recent_ingestion_dicts(self, *, limit: int = 500) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(IngestionEvent)
                .where(IngestionEvent.deleted_at.is_(None))
                .order_by(IngestionEvent.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return [
            {
                "collector": r.collector,
                "company": r.company,
                "status": r.status,
                "reason": r.reason,
                "duration": r.duration,
                "created_at": r.created_at,
            }
            for r in rows
        ]

    async def _count(self, model: type[Any], *clauses: Any) -> int:
        stmt = select(func.count()).select_from(model)
        filters = [model.deleted_at.is_(None), *clauses]
        stmt = stmt.where(and_(*filters))
        return int(await self.session.scalar(stmt) or 0)

    async def _count_since(self, model: type[Any], since: datetime, *clauses: Any) -> int:
        return await self._count(model, model.created_at >= since, *clauses)

    async def _count_between(
        self,
        model: type[Any],
        start: datetime,
        end: datetime,
        *clauses: Any,
    ) -> int:
        return await self._count(
            model,
            model.created_at >= start,
            model.created_at < end,
            *clauses,
        )
