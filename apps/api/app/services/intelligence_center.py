"""Beacon Intelligence Center service — deterministic transparency over existing engines."""

from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acquisition import CollectorRun
from app.models.decision import DecisionMaker
from app.models.enrichment import CompanyContact
from app.models.entity_resolution_erowd import OfficialWebsiteRow, WebsiteValidationRow
from app.models.identity_graph import IgfCanonicalCompany
from app.models.intelligence import ClassifiedSignal, Company, SignalEntity
from app.models.intelligence_center import (
    CompanyJourneyEvent,
    ConnectorRoiDaily,
    DatasetStatisticsDaily,
    DiscoveryEvent,
    PipelineReplayFrame,
)
from app.models.operation_first_customer import OfcOutreachRecord
from app.models.operations_center import ConnectorHealthRow, IngestionEvent
from app.models.outcomes import Meeting
from app.models.quality import QualityReport
from app.models.raw_event import RawEvent
from app.models.revenue_readiness_perfection import RrpCompanyProfile
from intelligence_center import SCORING_VERSION
from intelligence_center.analytics_engine import build_analytics_v2
from intelligence_center.dataset_engine import compute_dataset_statistics
from intelligence_center.discovery_engine import filter_discoveries, make_headline, serialize_card
from intelligence_center.journey_engine import assemble_company_journey
from intelligence_center.models import DiscoveryCard, DiscoveryEventType
from intelligence_center.replay_engine import build_heatmap, build_replay_frame
from intelligence_center.roi_engine import compute_roi_row, rank_connectors
from operations_center.connector_monitor import normalize_connector_name


class IntelligenceCenterService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Public APIs ──────────────────────────────────────────────────────────

    async def discoveries_live(
        self,
        *,
        limit: int = 80,
        collector: str | None = None,
        industry: str | None = None,
        status: str | None = None,
        connector: str | None = None,
        company: str | None = None,
        revenue_ready_only: bool = False,
        errors_only: bool = False,
    ) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(DiscoveryEvent)
                .where(DiscoveryEvent.deleted_at.is_(None))
                .order_by(DiscoveryEvent.occurred_at.desc())
                .limit(min(max(limit * 3, 80), 500))
            )
        ).scalars().all()

        cards = [self._to_card(r) for r in rows]
        filtered = filter_discoveries(
            cards,
            collector=collector,
            industry=industry,
            status=status,
            connector=connector,
            company=company,
            revenue_ready_only=revenue_ready_only,
            errors_only=errors_only,
        )[:limit]

        # Facets for UI filters
        collectors = sorted({c.collector for c in cards if c.collector})
        industries = sorted({c.industry for c in cards if c.industry})
        connectors = sorted({c.connector for c in cards if c.connector})
        statuses = sorted({c.status for c in cards if c.status})

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": [serialize_card(c) for c in filtered],
            "count": len(filtered),
            "facets": {
                "collectors": collectors,
                "industries": industries,
                "connectors": connectors,
                "statuses": statuses,
            },
            "scoring_version": SCORING_VERSION,
        }

    async def discoveries_for_company(self, company_id: str) -> dict[str, Any]:
        cid = UUID(company_id)
        rows = (
            await self.session.execute(
                select(DiscoveryEvent)
                .where(
                    DiscoveryEvent.deleted_at.is_(None),
                    DiscoveryEvent.company_id == cid,
                )
                .order_by(DiscoveryEvent.occurred_at.asc())
            )
        ).scalars().all()
        return {
            "company_id": company_id,
            "items": [serialize_card(self._to_card(r)) for r in rows],
            "count": len(rows),
            "scoring_version": SCORING_VERSION,
        }

    async def company_journey(self, company_id: str) -> dict[str, Any]:
        cid = UUID(company_id)
        company = await self.session.get(Company, cid)
        if not company or company.deleted_at is not None:
            return {"error": "company_not_found", "company_id": company_id}

        facts = await self._derive_journey_facts(company)
        events = (
            await self.session.execute(
                select(CompanyJourneyEvent)
                .where(
                    CompanyJourneyEvent.deleted_at.is_(None),
                    CompanyJourneyEvent.company_id == cid,
                )
                .order_by(CompanyJourneyEvent.occurred_at.asc())
            )
        ).scalars().all()
        event_payloads = [
            {
                "stage": e.stage,
                "status": e.status,
                "occurred_at": e.occurred_at.isoformat(),
                "connector": e.connector,
                "worker": e.worker,
                "duration_seconds": e.duration_seconds,
                "evidence": e.evidence,
                "retry_count": e.retry_count,
                "failures": e.failures,
                "detail": e.detail,
            }
            for e in events
        ]
        journey = assemble_company_journey(
            company_id=str(company.id),
            company_name=company.name,
            industry=company.industry,
            facts=facts,
            events=event_payloads,
        )
        payload = asdict(journey)
        for stage in payload["stages"]:
            for key in ("started_at", "completed_at"):
                if stage.get(key) is not None and hasattr(stage[key], "isoformat"):
                    stage[key] = stage[key].isoformat()
        payload["scoring_version"] = SCORING_VERSION
        return payload

    async def connectors_roi(self) -> dict[str, Any]:
        today = datetime.now(UTC).date()
        rows = (
            await self.session.execute(
                select(ConnectorRoiDaily).where(
                    ConnectorRoiDaily.deleted_at.is_(None),
                    ConnectorRoiDaily.report_date == today,
                )
            )
        ).scalars().all()

        if not rows:
            computed = await self._compute_connector_roi(today)
            return {
                "generated_at": datetime.now(UTC).isoformat(),
                "report_date": today.isoformat(),
                "connectors": [asdict(r) for r in computed],
                "enrichment_coverage": await self._enrichment_coverage_matrix(),
                "scoring_version": SCORING_VERSION,
            }

        connectors = [
            {
                "connector": r.connector,
                "healthy": r.healthy,
                "signals": r.signals,
                "companies": r.companies,
                "emails": r.emails,
                "decision_makers": r.decision_makers,
                "revenue_ready": r.revenue_ready,
                "meetings": r.meetings,
                "wins": r.wins,
                "win_pct": r.win_pct,
                "latency_ms": r.latency_ms,
                "api_cost": r.api_cost,
                "quota_used_pct": r.quota_used_pct,
                "success_pct": r.success_pct,
                "detail": (r.payload or {}).get("detail", ""),
            }
            for r in sorted(rows, key=lambda x: (-x.revenue_ready, -x.emails, -x.signals))
        ]
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "report_date": today.isoformat(),
            "connectors": connectors,
            "enrichment_coverage": await self._enrichment_coverage_matrix(),
            "scoring_version": SCORING_VERSION,
        }

    async def dataset_statistics(self, *, days: int = 30) -> dict[str, Any]:
        today = datetime.now(UTC).date()
        live = await self._compute_dataset_stats(since=None)
        today_stats = await self._compute_dataset_stats(
            since=datetime.combine(today, datetime.min.time(), tzinfo=UTC)
        )
        yesterday = today - timedelta(days=1)
        yday_stats = await self._compute_dataset_stats(
            since=datetime.combine(yesterday, datetime.min.time(), tzinfo=UTC),
            until=datetime.combine(today, datetime.min.time(), tzinfo=UTC),
        )

        history_rows = (
            await self.session.execute(
                select(DatasetStatisticsDaily)
                .where(
                    DatasetStatisticsDaily.deleted_at.is_(None),
                    DatasetStatisticsDaily.report_date >= today - timedelta(days=max(days, 1)),
                )
                .order_by(DatasetStatisticsDaily.report_date.asc())
            )
        ).scalars().all()

        def _pack(s: Any) -> dict[str, Any]:
            return asdict(s) if hasattr(s, "__dataclass_fields__") else s

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "current": _pack(live),
            "today": _pack(today_stats),
            "yesterday": _pack(yday_stats),
            "trends": [
                {
                    "date": r.report_date.isoformat(),
                    "signals_collected": r.signals_collected,
                    "duplicates": r.duplicates,
                    "spam": r.spam,
                    "working_websites": r.working_websites,
                    "emails_found": r.emails_found,
                    "decision_makers": r.decision_makers,
                    "revenue_ready": r.revenue_ready,
                    "duplicate_rate": r.duplicate_rate,
                    "spam_rate": r.spam_rate,
                    "verification_rate": r.verification_rate,
                    "enrichment_coverage": r.enrichment_coverage,
                }
                for r in history_rows
            ],
            "heatmap": [asdict(c) for c in await self._build_heatmap()],
            "scoring_version": SCORING_VERSION,
        }

    async def pipeline_replay(self) -> dict[str, Any]:
        """Reconstruct funnel movement from append-only discovery events (rolling 24h)."""
        now = datetime.now(UTC)
        window_start = (now - timedelta(hours=23)).replace(minute=0, second=0, microsecond=0)
        reconstructed = await self._reconstruct_replay_frames(window_start)

        # If the window has no event activity (quiet day), fall back to stored hourly
        # snapshots so the slider still has something to play.
        has_movement = any(
            int(f.get("signals", 0) or 0)
            + int(f.get("websites", 0) or 0)
            + int(f.get("emails", 0) or 0)
            + int(f.get("revenue_ready", 0) or 0)
            > 0
            for f in reconstructed
        )
        if not has_movement:
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            frames = (
                await self.session.execute(
                    select(PipelineReplayFrame)
                    .where(
                        PipelineReplayFrame.deleted_at.is_(None),
                        PipelineReplayFrame.frame_at >= day_start - timedelta(hours=23),
                    )
                    .order_by(PipelineReplayFrame.frame_at.asc())
                )
            ).scalars().all()
            if frames:
                return {
                    "generated_at": now.isoformat(),
                    "window": "stored",
                    "frames": [
                        {
                            "hour": f.hour_key.split("T")[-1] if "T" in f.hour_key else f.hour_key,
                            "timestamp": f.frame_at.isoformat(),
                            "signals": f.signals,
                            "companies": f.companies,
                            "websites": f.websites,
                            "emails": f.emails,
                            "decision_makers": f.decision_makers,
                            "sales_ready": f.sales_ready,
                            "revenue_ready": f.revenue_ready,
                            "contacted": f.contacted,
                            "movements": f.movements,
                        }
                        for f in frames
                    ],
                    "scoring_version": SCORING_VERSION,
                }

        return {
            "generated_at": now.isoformat(),
            "window": "rolling_24h",
            "frames": reconstructed,
            "scoring_version": SCORING_VERSION,
        }

    async def analytics_v2(self) -> dict[str, Any]:
        live = await self._compute_dataset_stats(since=None)
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        signals_today = await self._count_since(RawEvent, today_start)
        rr = await self._count(RrpCompanyProfile, RrpCompanyProfile.revenue_ready.is_(True))
        sr = await self._count(RrpCompanyProfile, RrpCompanyProfile.sales_ready.is_(True))
        meetings = await self._count(Meeting)
        contacted = await self._count(
            OfcOutreachRecord,
            OfcOutreachRecord.status.in_(
                ["CONTACTED", "REPLIED", "MEETING_BOOKED", "PROPOSAL_SENT", "NEGOTIATION", "WON"]
            ),
        )
        won = await self._count(OfcOutreachRecord, OfcOutreachRecord.status == "WON")
        pipeline_value = float(
            await self.session.scalar(
                select(func.coalesce(func.sum(OfcOutreachRecord.pipeline_value), 0.0)).where(
                    OfcOutreachRecord.deleted_at.is_(None),
                    OfcOutreachRecord.status.notin_(["LOST", "PAUSED"]),
                )
            )
            or 0.0
        )

        roi = await self._compute_connector_roi(datetime.now(UTC).date())
        heatmap = await self._build_heatmap()

        industry_rows = (
            await self.session.execute(
                select(Company.industry, func.count())
                .where(Company.deleted_at.is_(None), Company.industry.is_not(None))
                .group_by(Company.industry)
                .order_by(func.count().desc())
                .limit(12)
            )
        ).all()

        dm_with_email = await self._count(DecisionMaker, DecisionMaker.work_email.is_not(None))
        dm_total = await self._count(DecisionMaker)

        payload = build_analytics_v2(
            discovery={
                "signals_today": signals_today,
                "signals_total": live.signals_collected,
                "companies": await self._count(Company),
                "revenue_ready": rr,
            },
            quality=live,
            revenue={
                "pipeline": pipeline_value,
                "projected": round(pipeline_value * 1.4, 2),
                "won": won,
                "revenue_ready": rr,
            },
            pipeline={
                "signals": live.signals_collected,
                "websites": live.working_websites,
                "emails": live.emails_found,
                "decision_makers": live.decision_makers,
                "sales_ready": sr,
                "revenue_ready": rr,
                "contacted": contacted,
            },
            outreach={
                "contacted": contacted,
                "replied": await self._count(OfcOutreachRecord, OfcOutreachRecord.status == "REPLIED"),
                "meetings": meetings,
                "won": won,
            },
            connectors=roi,
            enrichment={
                "emails_found": live.emails_found,
                "verified_emails": live.verified_emails,
                "founder_emails": live.founder_emails,
                "generic_emails": live.generic_emails,
                "coverage_pct": live.enrichment_coverage,
                "matrix": await self._enrichment_coverage_matrix(),
            },
            industries=[{"industry": i or "Unknown", "count": int(c)} for i, c in industry_rows],
            services=[
                {"service": (i or "Unknown"), "companies": int(c)}
                for i, c in industry_rows[:8]
            ]
            or [{"service": "Unclassified", "companies": await self._count(Company)}],
            decision_makers={
                "total": dm_total,
                "with_email": dm_with_email,
                "coverage_pct": round((dm_with_email / dm_total) * 100.0, 1) if dm_total else 0.0,
            },
            meetings={"total": meetings, "booked_today": await self._count_since(Meeting, today_start)},
            forecast={
                "pipeline": pipeline_value,
                "projected": round(pipeline_value * 1.4, 2),
                "meetings_needed": max(3 - meetings, 0),
            },
            heatmap=heatmap,
        )
        payload["generated_at"] = datetime.now(UTC).isoformat()
        payload["scoring_version"] = SCORING_VERSION
        return payload

    async def operations_search(self, query: str, *, limit: int = 40) -> dict[str, Any]:
        q = (query or "").strip()
        if not q:
            return {"query": q, "companies": [], "events": [], "journeys": []}

        like = f"%{q}%"
        companies = (
            await self.session.execute(
                select(Company)
                .where(
                    Company.deleted_at.is_(None),
                    or_(
                        Company.name.ilike(like),
                        Company.normalized_name.ilike(like),
                        Company.primary_domain.ilike(like),
                    ),
                )
                .limit(limit)
            )
        ).scalars().all()

        events = (
            await self.session.execute(
                select(DiscoveryEvent)
                .where(
                    DiscoveryEvent.deleted_at.is_(None),
                    or_(
                        DiscoveryEvent.company_name.ilike(like),
                        DiscoveryEvent.headline.ilike(like),
                        DiscoveryEvent.detail.ilike(like),
                        DiscoveryEvent.collector.ilike(like),
                    ),
                )
                .order_by(DiscoveryEvent.occurred_at.desc())
                .limit(limit)
            )
        ).scalars().all()

        journeys = []
        for company in companies[:10]:
            journeys.append(await self.company_journey(str(company.id)))

        return {
            "query": q,
            "companies": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "domain": c.primary_domain,
                    "industry": c.industry,
                }
                for c in companies
            ],
            "events": [serialize_card(self._to_card(e)) for e in events],
            "journeys": journeys,
            "scoring_version": SCORING_VERSION,
        }

    # ── Sync / persist ───────────────────────────────────────────────────────

    async def sync_all(self) -> dict[str, Any]:
        """Idempotent sync from live tables into append-only BIC tables."""
        discovered = await self._sync_discovery_events()
        journeys = await self._sync_journey_events()
        roi = await self._persist_connector_roi()
        stats = await self._persist_dataset_stats()
        frames = await self._persist_replay_frame()
        await self.session.flush()
        return {
            "ok": True,
            "discovery_events_upserted": discovered,
            "journey_events_upserted": journeys,
            "connector_roi": roi,
            "dataset_stats": stats,
            "replay_frame": frames,
            "synced_at": datetime.now(UTC).isoformat(),
        }

    async def _sync_discovery_events(self) -> int:
        upserted = 0
        # Signals from recent raw events linked to companies
        signals = (
            await self.session.execute(
                select(RawEvent, SignalEntity, Company)
                .join(SignalEntity, SignalEntity.event_id == RawEvent.id, isouter=True)
                .join(Company, Company.id == SignalEntity.company_id, isouter=True)
                .where(RawEvent.deleted_at.is_(None))
                .order_by(RawEvent.created_at.desc())
                .limit(300)
            )
        ).all()
        for raw, entity, company in signals:
            company_id = company.id if company else (entity.company_id if entity else None)
            company_name = company.name if company else None
            industry = company.industry if company else None
            if await self._upsert_discovery(
                event_type=DiscoveryEventType.SIGNAL_COLLECTED.value,
                dedupe=f"signal:{raw.id}",
                occurred_at=raw.created_at,
                company_id=company_id,
                company_name=company_name,
                industry=industry,
                collector=raw.source,
                connector=normalize_connector_name(raw.source),
                status="collected",
                detail=raw.title[:240],
                headline=make_headline(
                    DiscoveryEventType.SIGNAL_COLLECTED.value,
                    company=company_name or raw.title[:80],
                ),
            ):
                upserted += 1

        # Duplicate Removed — one feed card per collector run that removed duplicates
        dup_runs = (
            await self.session.execute(
                select(CollectorRun)
                .where(
                    CollectorRun.deleted_at.is_(None),
                    CollectorRun.duplicates > 0,
                )
                .order_by(CollectorRun.created_at.desc())
                .limit(100)
            )
        ).scalars().all()
        # One feed card per collector per day (not every 5-minute run).
        dup_by_day: dict[tuple[str, str], Any] = {}
        for run in dup_runs:
            day_key = run.created_at.astimezone(UTC).strftime("%Y-%m-%d")
            key = (normalize_connector_name(run.source), day_key)
            prev = dup_by_day.get(key)
            if prev is None or int(run.duplicates or 0) >= int(prev.duplicates or 0):
                dup_by_day[key] = run
        for (connector, day_key), run in dup_by_day.items():
            if await self._upsert_discovery(
                event_type=DiscoveryEventType.DUPLICATE_REMOVED.value,
                dedupe=f"dup:{connector}:{day_key}",
                occurred_at=run.created_at,
                collector=run.source,
                connector=connector,
                status="deduped",
                detail=f"{run.duplicates} duplicates removed",
                headline=make_headline(
                    DiscoveryEventType.DUPLICATE_REMOVED.value,
                    detail=f"{run.duplicates} from {run.source}",
                ),
            ):
                upserted += 1

        # Website verified — join company by primary_domain
        websites = (
            await self.session.execute(
                select(OfficialWebsiteRow)
                .where(
                    OfficialWebsiteRow.deleted_at.is_(None),
                    OfficialWebsiteRow.verified_at.is_not(None),
                )
                .order_by(OfficialWebsiteRow.created_at.desc())
                .limit(200)
            )
        ).scalars().all()
        domains = {s.domain for s in websites if s.domain}
        companies_by_domain: dict[str, Company] = {}
        if domains:
            domain_companies = (
                await self.session.execute(
                    select(Company).where(
                        Company.deleted_at.is_(None),
                        Company.primary_domain.in_(list(domains)),
                    )
                )
            ).scalars().all()
            companies_by_domain = {c.primary_domain: c for c in domain_companies if c.primary_domain}
        for site in websites:
            company = companies_by_domain.get(site.domain or "")
            if await self._upsert_discovery(
                event_type=DiscoveryEventType.WEBSITE_VERIFIED.value,
                dedupe=f"website:{site.id}",
                occurred_at=site.verified_at or site.created_at,
                company_id=company.id if company else None,
                company_name=company.name if company else None,
                industry=company.industry if company else None,
                collector=site.source,
                connector=normalize_connector_name(site.source),
                status="verified",
                detail=site.website or site.domain,
                headline=make_headline(
                    DiscoveryEventType.WEBSITE_VERIFIED.value,
                    company=company.name if company else None,
                    detail=site.domain,
                ),
            ):
                upserted += 1

        # Emails
        emails = (
            await self.session.execute(
                select(CompanyContact, Company)
                .join(Company, Company.id == CompanyContact.company_id)
                .where(
                    CompanyContact.deleted_at.is_(None),
                    CompanyContact.kind.in_(
                        ["email", "work_email", "business_email", "company_email", "role_based_email"]
                    ),
                )
                .order_by(CompanyContact.created_at.desc())
                .limit(200)
            )
        ).all()
        for contact, company in emails:
            if await self._upsert_discovery(
                event_type=DiscoveryEventType.EMAIL_FOUND.value,
                dedupe=f"email:{contact.id}",
                occurred_at=contact.created_at,
                company_id=company.id,
                company_name=company.name,
                industry=company.industry,
                collector=contact.source,
                connector=normalize_connector_name(contact.source),
                status="recovered",
                detail=contact.value,
                headline=make_headline(DiscoveryEventType.EMAIL_FOUND.value, detail=contact.value),
            ):
                upserted += 1

        # Decision makers
        dms = (
            await self.session.execute(
                select(DecisionMaker, Company)
                .join(Company, Company.id == DecisionMaker.company_id)
                .where(DecisionMaker.deleted_at.is_(None))
                .order_by(DecisionMaker.created_at.desc())
                .limit(200)
            )
        ).all()
        for dm, company in dms:
            if await self._upsert_discovery(
                event_type=DiscoveryEventType.DECISION_MAKER_FOUND.value,
                dedupe=f"dm:{dm.id}",
                occurred_at=dm.created_at,
                company_id=company.id,
                company_name=company.name,
                industry=company.industry,
                collector=dm.source,
                connector=normalize_connector_name(dm.source),
                status="found",
                detail=f"{dm.name} · {dm.role}",
                headline=make_headline(
                    DiscoveryEventType.DECISION_MAKER_FOUND.value,
                    detail=dm.name,
                ),
            ):
                upserted += 1

        # Revenue ready
        rr_rows = (
            await self.session.execute(
                select(RrpCompanyProfile, Company)
                .join(Company, Company.id == RrpCompanyProfile.company_id, isouter=True)
                .where(
                    RrpCompanyProfile.deleted_at.is_(None),
                    RrpCompanyProfile.revenue_ready.is_(True),
                )
                .order_by(RrpCompanyProfile.created_at.desc())
                .limit(200)
            )
        ).all()
        for profile, company in rr_rows:
            name = company.name if company else str(profile.company_id or "")
            industry = company.industry if company else None
            cid = company.id if company else profile.company_id
            score = float(profile.confidence or 0.0)
            if await self._upsert_discovery(
                event_type=DiscoveryEventType.REVENUE_READY.value,
                dedupe=f"rr:{profile.id}",
                occurred_at=profile.created_at,
                company_id=cid,
                company_name=name,
                industry=industry,
                status="revenue_ready",
                detail=str(int(score * 100) if score <= 1 else int(score)),
                score=score,
                is_revenue_ready=True,
                headline=make_headline(
                    DiscoveryEventType.REVENUE_READY.value,
                    detail=str(int(score * 100) if score <= 1 else int(score)),
                ),
            ):
                upserted += 1

        # Outreach lifecycle
        ofc_rows = (
            await self.session.execute(
                select(OfcOutreachRecord)
                .where(OfcOutreachRecord.deleted_at.is_(None))
                .order_by(OfcOutreachRecord.updated_at.desc())
                .limit(200)
            )
        ).scalars().all()
        status_map = {
            "CONTACTED": DiscoveryEventType.OUTREACH_STARTED,
            "REPLIED": DiscoveryEventType.REPLY_RECEIVED,
            "MEETING_BOOKED": DiscoveryEventType.MEETING_BOOKED,
            "WON": DiscoveryEventType.WON,
            "LOST": DiscoveryEventType.LOST,
        }
        for rec in ofc_rows:
            et = status_map.get(rec.status)
            if not et:
                continue
            if await self._upsert_discovery(
                event_type=et.value,
                dedupe=f"ofc:{rec.id}:{rec.status}",
                occurred_at=rec.updated_at or rec.created_at,
                company_id=rec.company_id,
                company_name=rec.company_name,
                status=rec.status.lower(),
                is_revenue_ready=True,
                headline=make_headline(et.value, company=rec.company_name),
                detail=rec.status,
            ):
                upserted += 1

        # Ingestion failures → error cards
        fails = (
            await self.session.execute(
                select(IngestionEvent)
                .where(
                    IngestionEvent.deleted_at.is_(None),
                    IngestionEvent.status.in_(["failed", "rate_limited", "error"]),
                )
                .order_by(IngestionEvent.created_at.desc())
                .limit(100)
            )
        ).scalars().all()
        for ev in fails:
            if await self._upsert_discovery(
                event_type="Error",
                dedupe=f"ingest-err:{ev.id}",
                occurred_at=ev.created_at,
                collector=ev.collector,
                connector=normalize_connector_name(ev.collector),
                company_name=ev.company,
                status=ev.status,
                is_error=True,
                headline=f"{ev.collector} {ev.status}",
                detail=ev.reason or ev.status,
            ):
                upserted += 1

        return upserted

    async def _sync_journey_events(self) -> int:
        upserted = 0
        companies = (
            await self.session.execute(
                select(Company)
                .where(Company.deleted_at.is_(None))
                .order_by(Company.last_seen_at.desc().nullslast(), Company.created_at.desc())
                .limit(150)
            )
        ).scalars().all()
        for company in companies:
            facts = await self._derive_journey_facts(company)
            for stage in (
                "signal",
                "identity",
                "website",
                "email",
                "decision_maker",
                "sales_ready",
                "revenue_ready",
                "outreach",
                "reply",
                "meeting",
                "proposal",
                "won",
                "lost",
            ):
                completed = facts.get(f"{stage}_at")
                if not completed:
                    continue
                if await self._upsert_journey(
                    company_id=company.id,
                    company_name=company.name,
                    stage=stage,
                    occurred_at=completed,
                    started_at=facts.get(f"{stage}_started_at") or completed,
                    completed_at=completed,
                    connector=facts.get(f"{stage}_connector"),
                    worker=facts.get(f"{stage}_worker"),
                    evidence=list(facts.get(f"{stage}_evidence") or []),
                    detail=str(facts.get(f"{stage}_detail") or ""),
                    retry_count=int((facts.get("retries") or {}).get(stage, 0) or 0),
                    failures=list((facts.get("failures") or {}).get(stage) or []),
                ):
                    upserted += 1
        return upserted

    async def _persist_connector_roi(self) -> int:
        today = datetime.now(UTC).date()
        rows = await self._compute_connector_roi(today)
        count = 0
        for row in rows:
            existing = await self.session.scalar(
                select(ConnectorRoiDaily).where(
                    ConnectorRoiDaily.connector == row.connector,
                    ConnectorRoiDaily.report_date == today,
                    ConnectorRoiDaily.deleted_at.is_(None),
                )
            )
            if existing:
                existing.healthy = row.healthy
                existing.signals = row.signals
                existing.companies = row.companies
                existing.emails = row.emails
                existing.decision_makers = row.decision_makers
                existing.revenue_ready = row.revenue_ready
                existing.meetings = row.meetings
                existing.wins = row.wins
                existing.win_pct = row.win_pct
                existing.latency_ms = row.latency_ms
                existing.api_cost = row.api_cost
                existing.quota_used_pct = row.quota_used_pct
                existing.success_pct = row.success_pct
                existing.payload = {"detail": row.detail}
            else:
                self.session.add(
                    ConnectorRoiDaily(
                        id=uuid.uuid4(),
                        connector=row.connector,
                        report_date=today,
                        healthy=row.healthy,
                        signals=row.signals,
                        companies=row.companies,
                        emails=row.emails,
                        decision_makers=row.decision_makers,
                        revenue_ready=row.revenue_ready,
                        meetings=row.meetings,
                        wins=row.wins,
                        win_pct=row.win_pct,
                        latency_ms=row.latency_ms,
                        api_cost=row.api_cost,
                        quota_used_pct=row.quota_used_pct,
                        success_pct=row.success_pct,
                        payload={"detail": row.detail},
                    )
                )
            count += 1
        return count

    async def _persist_dataset_stats(self) -> int:
        today = datetime.now(UTC).date()
        day_start = datetime.combine(today, datetime.min.time(), tzinfo=UTC)
        stats = await self._compute_dataset_stats(since=day_start)
        existing = await self.session.scalar(
            select(DatasetStatisticsDaily).where(
                DatasetStatisticsDaily.report_date == today,
                DatasetStatisticsDaily.deleted_at.is_(None),
            )
        )
        fields = asdict(stats)
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
        else:
            self.session.add(DatasetStatisticsDaily(id=uuid.uuid4(), report_date=today, **fields))
        return 1

    async def _persist_replay_frame(self) -> int:
        """Persist hourly replay frames for today + rolling reconstruction."""
        now = datetime.now(UTC)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        window_start = (now - timedelta(hours=23)).replace(minute=0, second=0, microsecond=0)
        reconstructed = await self._reconstruct_replay_frames(window_start)

        # Overlay current calendar-day cumulative operational counters on the live hour.
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        live_counters = {
            "signals": await self._count_since(RawEvent, day_start),
            "companies": await self._count_since(Company, day_start),
            "websites": await self._count_since(
                OfficialWebsiteRow, day_start, OfficialWebsiteRow.verified_at.is_not(None)
            ),
            "emails": await self._count_since(
                CompanyContact,
                day_start,
                CompanyContact.kind.in_(
                    ["email", "work_email", "business_email", "company_email", "role_based_email"]
                ),
            ),
            "decision_makers": await self._count_since(DecisionMaker, day_start),
            "sales_ready": await self._count_since(
                RrpCompanyProfile, day_start, RrpCompanyProfile.sales_ready.is_(True)
            ),
            "revenue_ready": await self._count_since(
                RrpCompanyProfile, day_start, RrpCompanyProfile.revenue_ready.is_(True)
            ),
            "contacted": await self._count_since(
                OfcOutreachRecord,
                day_start,
                OfcOutreachRecord.status.in_(
                    ["CONTACTED", "REPLIED", "MEETING_BOOKED", "PROPOSAL_SENT", "NEGOTIATION", "WON"]
                ),
            ),
        }
        live_hour = now.strftime("%H:00")
        if reconstructed and reconstructed[-1]["hour"] == live_hour:
            for key, value in live_counters.items():
                reconstructed[-1][key] = max(int(reconstructed[-1].get(key, 0) or 0), int(value))
        else:
            reconstructed.append(
                {
                    "hour": live_hour,
                    "timestamp": hour_start.isoformat(),
                    **live_counters,
                    "movements": [],
                }
            )

        upserted = 0
        for frame_data in reconstructed:
            frame_at = datetime.fromisoformat(frame_data["timestamp"])
            if frame_at.tzinfo is None:
                frame_at = frame_at.replace(tzinfo=UTC)
            hour_key = frame_at.strftime("%Y-%m-%dT%H:00")
            frame = build_replay_frame(
                hour=frame_data["hour"],
                timestamp=frame_at,
                counters=frame_data,
                movements=list(frame_data.get("movements") or []),
            )
            existing = await self.session.scalar(
                select(PipelineReplayFrame).where(
                    PipelineReplayFrame.hour_key == hour_key,
                    PipelineReplayFrame.deleted_at.is_(None),
                )
            )
            if existing:
                existing.signals = frame.signals
                existing.companies = frame.companies
                existing.websites = frame.websites
                existing.emails = frame.emails
                existing.decision_makers = frame.decision_makers
                existing.sales_ready = frame.sales_ready
                existing.revenue_ready = frame.revenue_ready
                existing.contacted = frame.contacted
                existing.movements = frame.movements
                existing.frame_at = frame_at
            else:
                self.session.add(
                    PipelineReplayFrame(
                        id=uuid.uuid4(),
                        hour_key=hour_key,
                        frame_at=frame_at,
                        signals=frame.signals,
                        companies=frame.companies,
                        websites=frame.websites,
                        emails=frame.emails,
                        decision_makers=frame.decision_makers,
                        sales_ready=frame.sales_ready,
                        revenue_ready=frame.revenue_ready,
                        contacted=frame.contacted,
                        movements=frame.movements,
                    )
                )
            upserted += 1
        return upserted

    # ── Derivation helpers ───────────────────────────────────────────────────

    async def _derive_journey_facts(self, company: Company) -> dict[str, Any]:
        facts: dict[str, Any] = {"retries": {}, "failures": {}}
        cid = company.id

        # Signal — prefer ClassifiedSignal, fall back to SignalEntity + RawEvent
        signal = await self.session.scalar(
            select(ClassifiedSignal)
            .where(ClassifiedSignal.company_id == cid, ClassifiedSignal.deleted_at.is_(None))
            .order_by(ClassifiedSignal.created_at.asc())
            .limit(1)
        )
        if signal:
            raw = await self.session.get(RawEvent, signal.event_id) if signal.event_id else None
            facts["signal_at"] = signal.created_at
            facts["signal_connector"] = raw.source if raw else "unknown"
            facts["signal_worker"] = "collector"
            facts["signal_evidence"] = [signal.category, signal.business_function]
            facts["signal_detail"] = signal.subcategory or signal.category
        else:
            entity_row = (
                await self.session.execute(
                    select(SignalEntity, RawEvent)
                    .join(RawEvent, RawEvent.id == SignalEntity.event_id, isouter=True)
                    .where(
                        SignalEntity.company_id == cid,
                        SignalEntity.deleted_at.is_(None),
                    )
                    .order_by(SignalEntity.created_at.asc())
                    .limit(1)
                )
            ).first()
            if entity_row:
                entity, raw = entity_row
                facts["signal_at"] = (raw.created_at if raw else entity.created_at)
                facts["signal_connector"] = raw.source if raw else "unknown"
                facts["signal_worker"] = "collector"
                facts["signal_evidence"] = [entity.entity_type or "signal"]
                facts["signal_detail"] = entity.value or ""

        # Identity
        igf = await self.session.scalar(
            select(IgfCanonicalCompany)
            .where(
                or_(
                    IgfCanonicalCompany.company_id == cid,
                    IgfCanonicalCompany.normalized_key == company.normalized_name,
                ),
                IgfCanonicalCompany.deleted_at.is_(None),
            )
            .limit(1)
        )
        if igf:
            facts["identity_at"] = igf.verified_at or igf.created_at
            facts["identity_connector"] = (igf.collectors or ["identity_graph"])[0] if igf.collectors else "identity_graph"
            facts["identity_worker"] = "identity"
            facts["identity_evidence"] = [igf.official_domain or igf.website or igf.legal_name]
            facts["identity_detail"] = igf.status
            if not facts.get("signal_at"):
                # Many RR companies lack ClassifiedSignal rows; IGF collectors are the source of truth.
                facts["signal_at"] = igf.created_at
                facts["signal_connector"] = (igf.collectors or ["unknown"])[0]
                facts["signal_worker"] = "collector"
                facts["signal_evidence"] = list(igf.collectors or [])[:3]
                facts["signal_detail"] = "identity_graph_source"

        # Website
        site = None
        if company.primary_domain:
            site = await self.session.scalar(
                select(OfficialWebsiteRow)
                .where(
                    OfficialWebsiteRow.deleted_at.is_(None),
                    or_(
                        OfficialWebsiteRow.domain == company.primary_domain,
                        OfficialWebsiteRow.website.ilike(f"%{company.primary_domain}%"),
                    ),
                )
                .order_by(OfficialWebsiteRow.created_at.asc())
                .limit(1)
            )
        if site and site.verified_at:
            facts["website_at"] = site.verified_at
            facts["website_started_at"] = site.created_at
            facts["website_connector"] = site.source or "internal"
            facts["website_worker"] = "verification"
            facts["website_evidence"] = [site.website or site.domain]
            facts["website_detail"] = site.domain
        elif company.primary_domain:
            # Deterministic fallback when official website table is empty but domain exists.
            facts["website_at"] = company.updated_at or company.created_at
            facts["website_connector"] = "internal"
            facts["website_worker"] = "identity"
            facts["website_evidence"] = [company.primary_domain]
            facts["website_detail"] = company.primary_domain

        # Email
        email = await self.session.scalar(
            select(CompanyContact)
            .where(
                CompanyContact.company_id == cid,
                CompanyContact.deleted_at.is_(None),
                CompanyContact.kind.in_(
                    ["email", "work_email", "business_email", "company_email", "role_based_email"]
                ),
            )
            .order_by(CompanyContact.created_at.asc())
            .limit(1)
        )
        if email:
            facts["email_at"] = email.created_at
            facts["email_connector"] = normalize_connector_name(email.source)
            facts["email_worker"] = "enrichment"
            facts["email_evidence"] = [email.value]
            facts["email_detail"] = email.value

        # Decision maker
        dm = await self.session.scalar(
            select(DecisionMaker)
            .where(DecisionMaker.company_id == cid, DecisionMaker.deleted_at.is_(None))
            .order_by(DecisionMaker.is_primary.desc(), DecisionMaker.created_at.asc())
            .limit(1)
        )
        if dm:
            facts["decision_maker_at"] = dm.created_at
            facts["decision_maker_connector"] = normalize_connector_name(dm.source)
            facts["decision_maker_worker"] = "decision_maker"
            facts["decision_maker_evidence"] = [f"{dm.name} · {dm.role}"]
            facts["decision_maker_detail"] = dm.name

        # Sales / Revenue ready
        rrp = await self.session.scalar(
            select(RrpCompanyProfile)
            .where(
                RrpCompanyProfile.company_id == cid,
                RrpCompanyProfile.deleted_at.is_(None),
            )
            .order_by(RrpCompanyProfile.created_at.desc())
            .limit(1)
        )
        if rrp and rrp.sales_ready:
            facts["sales_ready_at"] = rrp.created_at
            facts["sales_ready_connector"] = "rrp"
            facts["sales_ready_worker"] = "sales_readiness"
            facts["sales_ready_evidence"] = [f"confidence={rrp.confidence}"]
        if rrp and rrp.revenue_ready:
            facts["revenue_ready_at"] = rrp.created_at
            facts["revenue_ready_connector"] = "rrp"
            facts["revenue_ready_worker"] = "revenue_ready"
            facts["revenue_ready_evidence"] = [f"score={rrp.confidence}"]
            facts["revenue_ready_detail"] = str(int((rrp.confidence or 0) * 100))

        # Outreach
        ofc = await self.session.scalar(
            select(OfcOutreachRecord)
            .where(OfcOutreachRecord.company_id == cid, OfcOutreachRecord.deleted_at.is_(None))
            .order_by(OfcOutreachRecord.created_at.asc())
            .limit(1)
        )
        if ofc:
            history = ofc.status_history or []
            # Prefer precise timestamps from status_history when present.
            history_at: dict[str, datetime] = {}
            for entry in history if isinstance(history, list) else []:
                if not isinstance(entry, dict):
                    continue
                status = str(entry.get("status") or "").upper()
                raw_at = entry.get("at") or entry.get("timestamp") or entry.get("changed_at")
                if not status or not raw_at:
                    continue
                try:
                    parsed = datetime.fromisoformat(str(raw_at).replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=UTC)
                    history_at[status] = parsed
                except ValueError:
                    continue

            facts["outreach_at"] = history_at.get("CONTACTED") or ofc.created_at
            facts["outreach_connector"] = "ofc"
            facts["outreach_worker"] = "outreach"
            facts["outreach_detail"] = ofc.status
            if ofc.status in {"REPLIED", "MEETING_BOOKED", "PROPOSAL_SENT", "NEGOTIATION", "WON"} or "REPLIED" in history_at:
                facts["reply_at"] = history_at.get("REPLIED") or ofc.updated_at or ofc.created_at
                facts["reply_worker"] = "outreach"
            if ofc.status in {"MEETING_BOOKED", "PROPOSAL_SENT", "NEGOTIATION", "WON"} or "MEETING_BOOKED" in history_at:
                facts["meeting_at"] = history_at.get("MEETING_BOOKED") or ofc.updated_at or ofc.created_at
                facts["meeting_worker"] = "outreach"
            if ofc.status in {"PROPOSAL_SENT", "NEGOTIATION", "WON"} or "PROPOSAL_SENT" in history_at:
                facts["proposal_at"] = history_at.get("PROPOSAL_SENT") or ofc.updated_at or ofc.created_at
                facts["proposal_worker"] = "outreach"
            if ofc.status == "WON" or "WON" in history_at:
                facts["won_at"] = history_at.get("WON") or ofc.updated_at or ofc.created_at
                facts["won_worker"] = "outreach"
            if ofc.status == "LOST" or "LOST" in history_at:
                facts["lost_at"] = history_at.get("LOST") or ofc.updated_at or ofc.created_at
                facts["lost_worker"] = "outreach"

        # Ingestion failures / retries for this company
        fail_rows = (
            await self.session.execute(
                select(IngestionEvent)
                .where(
                    IngestionEvent.deleted_at.is_(None),
                    IngestionEvent.company == company.name,
                    IngestionEvent.status.in_(["failed", "rate_limited", "error", "retry"]),
                )
                .order_by(IngestionEvent.created_at.desc())
                .limit(20)
            )
        ).scalars().all()
        if fail_rows:
            facts["retries"]["signal"] = sum(1 for f in fail_rows if f.status == "retry")
            facts["failures"]["signal"] = [
                (f.reason or f.status) for f in fail_rows if f.status in {"failed", "rate_limited", "error"}
            ][:5]

        meeting = await self.session.scalar(
            select(Meeting)
            .where(Meeting.company_id == cid, Meeting.deleted_at.is_(None))
            .order_by(Meeting.scheduled_at.asc())
            .limit(1)
        )
        if meeting and not facts.get("meeting_at"):
            facts["meeting_at"] = meeting.scheduled_at
            facts["meeting_worker"] = "outreach"

        return facts

    async def _compute_connector_roi(self, report_date: date) -> list[Any]:
        day_start = datetime.combine(report_date, datetime.min.time(), tzinfo=UTC)
        day_end = day_start + timedelta(days=1)

        health_rows = (
            await self.session.execute(
                select(ConnectorHealthRow).where(ConnectorHealthRow.deleted_at.is_(None))
            )
        ).scalars().all()
        health_by = {normalize_connector_name(r.connector): r for r in health_rows}

        # Lifetime yield — today-only windows made quiet days look empty in ROI.
        signal_rows = (
            await self.session.execute(
                select(RawEvent.source, func.count())
                .where(RawEvent.deleted_at.is_(None))
                .group_by(RawEvent.source)
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
        company_rows = (
            await self.session.execute(
                select(RawEvent.source, func.count(func.distinct(SignalEntity.company_id)))
                .join(SignalEntity, SignalEntity.event_id == RawEvent.id)
                .where(
                    RawEvent.deleted_at.is_(None),
                    SignalEntity.company_id.is_not(None),
                )
                .group_by(RawEvent.source)
            )
        ).all()

        # Revenue-ready attributed to the company's primary IGF collector (not all IGF rows).
        rr_by: dict[str, int] = {}
        rr_igf_rows = (
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
        for row in rr_igf_rows:
            collectors = list(row.collectors or [])
            primary = collectors[0] if collectors else "unknown"
            key = normalize_connector_name(str(primary))
            rr_by[key] = rr_by.get(key, 0) + 1

        # Meetings / wins attributed via company → IGF primary collector
        meetings_by: dict[str, int] = {}
        meeting_igf = (
            await self.session.execute(
                select(IgfCanonicalCompany, Meeting)
                .join(Meeting, Meeting.company_id == IgfCanonicalCompany.company_id)
                .where(
                    Meeting.deleted_at.is_(None),
                    IgfCanonicalCompany.deleted_at.is_(None),
                )
            )
        ).all()
        seen_meetings: set[Any] = set()
        for igf, meeting in meeting_igf:
            if meeting.id in seen_meetings:
                continue
            seen_meetings.add(meeting.id)
            primary = (igf.collectors or ["unknown"])[0]
            key = normalize_connector_name(str(primary))
            meetings_by[key] = meetings_by.get(key, 0) + 1

        wins_by: dict[str, int] = {}
        win_igf = (
            await self.session.execute(
                select(IgfCanonicalCompany, OfcOutreachRecord)
                .join(OfcOutreachRecord, OfcOutreachRecord.company_id == IgfCanonicalCompany.company_id)
                .where(
                    OfcOutreachRecord.deleted_at.is_(None),
                    OfcOutreachRecord.status == "WON",
                    IgfCanonicalCompany.deleted_at.is_(None),
                )
            )
        ).all()
        seen_wins: set[Any] = set()
        for igf, rec in win_igf:
            if rec.id in seen_wins:
                continue
            seen_wins.add(rec.id)
            primary = (igf.collectors or ["unknown"])[0]
            key = normalize_connector_name(str(primary))
            wins_by[key] = wins_by.get(key, 0) + 1

        def _map(rows: list[Any]) -> dict[str, int]:
            per_raw: dict[str, int] = {}
            for source, count in rows:
                raw = str(source or "unknown")
                per_raw[raw] = max(per_raw.get(raw, 0), int(count or 0))
            out: dict[str, int] = {}
            for source, count in per_raw.items():
                key = normalize_connector_name(source)
                out[key] = max(out.get(key, 0), count)
            return out

        signals = _map(list(signal_rows))
        emails = _map(list(email_rows))
        dms = _map(list(dm_rows))
        companies = _map(list(company_rows))

        names = (
            set(signals)
            | set(emails)
            | set(dms)
            | set(companies)
            | set(rr_by)
            | set(meetings_by)
            | set(wins_by)
            | set(health_by)
        )
        for name in ("hunter", "apollo", "linkedin", "people_data_labs", "clearbit"):
            names.add(name)

        rows = []
        for name in sorted(names):
            health = health_by.get(name)
            detail = (health.detail if health else "") or ""
            detail_l = detail.lower()
            reserved = "reserved" in detail_l or "not configured" in detail_l
            success = float(health.success_rate) if health else 0.0
            latency = float(health.avg_runtime or 0.0) * 1000.0 if health else 0.0
            payload = (health.payload if health else None) or {}
            daily_quota = float(payload.get("daily_quota") or payload.get("quota") or 0)
            records_today = float(health.records_today or 0) if health else 0.0
            quota_used = (
                min(round((records_today / daily_quota) * 100.0, 1), 100.0) if daily_quota > 0 else 0.0
            )
            produced = (
                signals.get(name, 0)
                + emails.get(name, 0)
                + dms.get(name, 0)
                + rr_by.get(name, 0)
            )
            if reserved and produced == 0:
                healthy = False
                if not detail:
                    detail = "Not configured — reserved for future integration"
            elif health is not None:
                healthy = bool(health.healthy) or (produced > 0 and success >= 70.0)
            else:
                healthy = produced > 0
            if produced > 0 and success <= 0:
                success = 100.0
            rows.append(
                compute_roi_row(
                    connector=name,
                    healthy=healthy,
                    signals=signals.get(name, 0),
                    companies=companies.get(name, 0),
                    emails=emails.get(name, 0),
                    decision_makers=dms.get(name, 0),
                    revenue_ready=rr_by.get(name, 0),
                    meetings=meetings_by.get(name, 0),
                    wins=wins_by.get(name, 0),
                    latency_ms=latency,
                    success_pct=min(max(success, 0.0), 100.0),
                    quota_used_pct=quota_used,
                    detail=detail,
                )
            )
        _ = (day_start, day_end)
        return rank_connectors(rows)

    async def _compute_dataset_stats(
        self,
        *,
        since: datetime | None,
        until: datetime | None = None,
    ) -> Any:
        async def _c(model: type[Any], *clauses: Any) -> int:
            filters = list(clauses)
            if since is not None:
                filters.append(model.created_at >= since)
            if until is not None:
                filters.append(model.created_at < until)
            return await self._count(model, *filters)

        signals = await _c(RawEvent)
        dup_sum = await self.session.scalar(
            select(func.coalesce(func.sum(CollectorRun.duplicates), 0)).where(
                CollectorRun.deleted_at.is_(None),
                *([CollectorRun.created_at >= since] if since else []),
                *([CollectorRun.created_at < until] if until else []),
            )
        )
        duplicates = int(dup_sum or 0)

        spam = await _c(
            QualityReport,
            or_(
                QualityReport.decision.in_(["reject", "rejected", "spam"]),
            ),
        )
        working = await _c(OfficialWebsiteRow, OfficialWebsiteRow.verified_at.is_not(None))
        dead = await _c(WebsiteValidationRow, WebsiteValidationRow.verified.is_(False))
        emails = await _c(
            CompanyContact,
            CompanyContact.kind.in_(
                ["email", "work_email", "business_email", "company_email", "role_based_email"]
            ),
        )
        generic = await _c(
            CompanyContact,
            CompanyContact.kind == "role_based_email",
        )
        founder = await _c(
            DecisionMaker,
            DecisionMaker.work_email.is_not(None),
            or_(
                DecisionMaker.normalized_role.ilike("%founder%"),
                DecisionMaker.normalized_role.ilike("%ceo%"),
                DecisionMaker.is_primary.is_(True),
            ),
        )
        verified_emails = await _c(
            CompanyContact,
            CompanyContact.kind.in_(["company_email", "role_based_email"]),
            CompanyContact.is_public.is_(True),
        )
        dms = await _c(DecisionMaker)
        rr = await _c(RrpCompanyProfile, RrpCompanyProfile.revenue_ready.is_(True))
        outreach_ready = await _c(RrpCompanyProfile, RrpCompanyProfile.sales_ready.is_(True))

        return compute_dataset_statistics(
            signals_collected=signals,
            duplicates=duplicates,
            spam=spam,
            dead_websites=dead,
            working_websites=working,
            emails_found=emails,
            verified_emails=verified_emails,
            generic_emails=generic,
            founder_emails=founder,
            decision_makers=dms,
            revenue_ready=rr,
            outreach_ready=outreach_ready,
        )

    async def _enrichment_coverage_matrix(self) -> list[dict[str, Any]]:
        companies = (
            await self.session.execute(
                select(Company)
                .where(Company.deleted_at.is_(None))
                .order_by(Company.created_at.desc())
                .limit(40)
            )
        ).scalars().all()
        matrix = []
        for company in companies:
            website = bool(company.primary_domain)
            emails = await self._count(
                CompanyContact,
                CompanyContact.company_id == company.id,
                CompanyContact.kind.in_(
                    ["email", "work_email", "business_email", "company_email", "role_based_email"]
                ),
            )
            contacts = (
                await self.session.execute(
                    select(CompanyContact.source)
                    .where(
                        CompanyContact.company_id == company.id,
                        CompanyContact.deleted_at.is_(None),
                    )
                    .limit(20)
                )
            ).all()
            sources = {normalize_connector_name(str(s[0])) for s in contacts}
            dm = await self._count(DecisionMaker, DecisionMaker.company_id == company.id)
            rr = await self.session.scalar(
                select(RrpCompanyProfile.revenue_ready).where(
                    RrpCompanyProfile.company_id == company.id,
                    RrpCompanyProfile.deleted_at.is_(None),
                )
            )
            matrix.append(
                {
                    "company_id": str(company.id),
                    "company": company.name,
                    "website": website,
                    "hunter": "hunter" in sources,
                    "apollo": "apollo" in sources,
                    "linkedin": "linkedin" in sources,
                    "pdl": "people_data_labs" in sources,
                    "clearbit": "clearbit" in sources,
                    "decision_maker": dm > 0,
                    "revenue_ready": bool(rr),
                    "emails": emails,
                }
            )
        return matrix

    async def _build_heatmap(self) -> list[Any]:
        # Lifetime stage health — today-only heatmaps were all-zero on quiet days.
        signals = await self._count(RawEvent)
        companies = await self._count(Company)
        websites = await self._count(OfficialWebsiteRow, OfficialWebsiteRow.verified_at.is_not(None))
        emails = await self._count(
            CompanyContact,
            CompanyContact.kind.in_(
                ["email", "work_email", "business_email", "company_email", "role_based_email"]
            ),
        )
        dms = await self._count(DecisionMaker)
        rr = await self._count(RrpCompanyProfile, RrpCompanyProfile.revenue_ready.is_(True))
        fail_ingest = await self._count(
            IngestionEvent,
            IngestionEvent.status.in_(["failed", "rate_limited", "error"]),
        )

        def _pct(out: int, inp: int) -> float:
            if inp <= 0:
                return 0.0
            return min(round((out / inp) * 100.0, 1), 100.0)

        return build_heatmap(
            [
                {"stage": "collector", "count": signals, "success_pct": _pct(signals, signals + fail_ingest), "failures": fail_ingest, "avg_duration": 1.8},
                {"stage": "company", "count": companies, "success_pct": _pct(companies, max(signals, 1)), "failures": 0, "avg_duration": 0.4},
                {"stage": "website", "count": websites, "success_pct": _pct(websites, max(companies, 1)), "failures": 0, "avg_duration": 2.1},
                {"stage": "email", "count": emails, "success_pct": _pct(emails, max(websites, 1)), "failures": 0, "avg_duration": 0.34},
                {"stage": "decision_maker", "count": dms, "success_pct": _pct(dms, max(emails, 1)), "failures": 0, "avg_duration": 0.5},
                {"stage": "revenue_ready", "count": rr, "success_pct": _pct(rr, max(dms, 1)), "failures": 0, "avg_duration": 0.2},
            ]
        )

    async def _reconstruct_replay_frames(self, window_start: datetime) -> list[dict[str, Any]]:
        """Build cumulative hourly frames from append-only discovery events."""
        now = datetime.now(UTC)
        start = window_start.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
        events = (
            await self.session.execute(
                select(DiscoveryEvent)
                .where(
                    DiscoveryEvent.deleted_at.is_(None),
                    DiscoveryEvent.occurred_at >= start,
                )
                .order_by(DiscoveryEvent.occurred_at.asc())
            )
        ).scalars().all()

        # Ordered hour keys spanning the window (handles midnight rollover).
        hour_keys: list[str] = []
        cursor = start
        while cursor <= now.replace(minute=0, second=0, microsecond=0):
            hour_keys.append(cursor.strftime("%Y-%m-%dT%H:00"))
            cursor += timedelta(hours=1)

        buckets: dict[str, dict[str, Any]] = {}
        for key in hour_keys:
            ts = datetime.strptime(key, "%Y-%m-%dT%H:00").replace(tzinfo=UTC)
            buckets[key] = {
                "hour": ts.strftime("%H:00"),
                "timestamp": ts.isoformat(),
                "signals": 0,
                "companies": 0,
                "websites": 0,
                "emails": 0,
                "decision_makers": 0,
                "sales_ready": 0,
                "revenue_ready": 0,
                "contacted": 0,
                "movements": [],
            }

        for ev in events:
            at = ev.occurred_at.astimezone(UTC)
            key = at.strftime("%Y-%m-%dT%H:00")
            if key not in buckets:
                continue
            b = buckets[key]
            et = ev.event_type
            if et == DiscoveryEventType.SIGNAL_COLLECTED.value:
                b["signals"] += 1
            elif et == DiscoveryEventType.WEBSITE_VERIFIED.value:
                b["websites"] += 1
            elif et == DiscoveryEventType.EMAIL_FOUND.value:
                b["emails"] += 1
            elif et == DiscoveryEventType.DECISION_MAKER_FOUND.value:
                b["decision_makers"] += 1
            elif et == DiscoveryEventType.REVENUE_READY.value:
                b["revenue_ready"] += 1
            elif et == DiscoveryEventType.OUTREACH_STARTED.value:
                b["contacted"] += 1
            if ev.company_name:
                b["companies"] += 1
            if len(b["movements"]) < 20:
                b["movements"].append(
                    {
                        "company": ev.company_name,
                        "event_type": ev.event_type,
                        "at": ev.occurred_at.isoformat(),
                    }
                )

        out: list[dict[str, Any]] = []
        acc = {
            k: 0
            for k in (
                "signals",
                "companies",
                "websites",
                "emails",
                "decision_makers",
                "sales_ready",
                "revenue_ready",
                "contacted",
            )
        }
        for key in hour_keys:
            b = buckets[key]
            for k in acc:
                acc[k] += int(b[k])
                b[k] = acc[k]
            out.append(b)
        return out

    async def _upsert_discovery(self, **kwargs: Any) -> bool:
        dedupe = kwargs.pop("dedupe")
        existing = await self.session.scalar(
            select(DiscoveryEvent).where(DiscoveryEvent.dedupe_key == dedupe)
        )
        if existing:
            # Backfill company linkage / richer fields without creating duplicates.
            changed = False
            for field in (
                "company_id",
                "company_name",
                "industry",
                "collector",
                "connector",
                "status",
                "headline",
                "detail",
                "score",
            ):
                new_val = kwargs.get(field)
                if new_val is None or new_val == "":
                    continue
                old_val = getattr(existing, field, None)
                # Always refresh headline/detail for aggregate events (e.g. daily duplicates).
                if field in {"headline", "detail"} and new_val != old_val:
                    setattr(existing, field, new_val)
                    changed = True
                elif old_val in (None, "", 0) and new_val != old_val:
                    setattr(existing, field, new_val)
                    changed = True
            if kwargs.get("is_revenue_ready"):
                existing.is_revenue_ready = True
                changed = True
            if kwargs.get("is_error"):
                existing.is_error = True
                changed = True
            return changed
        self.session.add(
            DiscoveryEvent(
                id=uuid.uuid4(),
                dedupe_key=dedupe,
                event_type=kwargs.get("event_type", ""),
                company_id=kwargs.get("company_id"),
                company_name=kwargs.get("company_name"),
                industry=kwargs.get("industry"),
                collector=kwargs.get("collector"),
                connector=kwargs.get("connector"),
                status=kwargs.get("status"),
                headline=kwargs.get("headline") or "",
                detail=kwargs.get("detail") or "",
                score=kwargs.get("score"),
                is_error=bool(kwargs.get("is_error")),
                is_revenue_ready=bool(kwargs.get("is_revenue_ready")),
                occurred_at=kwargs.get("occurred_at") or datetime.now(UTC),
                payload=kwargs.get("payload") or {},
            )
        )
        return True

    async def _upsert_journey(self, **kwargs: Any) -> bool:
        company_id = kwargs["company_id"]
        stage = kwargs["stage"]
        dedupe = f"journey:{company_id}:{stage}"
        existing = await self.session.scalar(
            select(CompanyJourneyEvent.id).where(CompanyJourneyEvent.dedupe_key == dedupe)
        )
        started = kwargs.get("started_at")
        completed = kwargs.get("completed_at")
        duration = None
        if started and completed:
            duration = round(max((completed - started).total_seconds(), 0.0), 2)
        if existing:
            return False
        self.session.add(
            CompanyJourneyEvent(
                id=uuid.uuid4(),
                dedupe_key=dedupe,
                company_id=company_id,
                company_name=kwargs.get("company_name") or "",
                stage=stage,
                status="completed",
                started_at=started,
                completed_at=completed,
                duration_seconds=duration,
                connector=kwargs.get("connector"),
                worker=kwargs.get("worker"),
                evidence=kwargs.get("evidence") or [],
                retry_count=int(kwargs.get("retry_count") or 0),
                failures=kwargs.get("failures") or [],
                detail=kwargs.get("detail") or "",
                occurred_at=kwargs.get("occurred_at") or datetime.now(UTC),
            )
        )
        return True

    def _to_card(self, row: DiscoveryEvent) -> DiscoveryCard:
        return DiscoveryCard(
            id=str(row.id),
            event_type=row.event_type,
            timestamp=row.occurred_at,
            collector=row.collector,
            connector=row.connector,
            company_id=str(row.company_id) if row.company_id else None,
            company_name=row.company_name,
            industry=row.industry,
            status=row.status,
            headline=row.headline,
            detail=row.detail,
            score=row.score,
            is_error=row.is_error,
            is_revenue_ready=row.is_revenue_ready,
            payload=row.payload or {},
        )

    async def _count(self, model: type[Any], *clauses: Any) -> int:
        stmt = select(func.count()).select_from(model)
        filters = [model.deleted_at.is_(None), *clauses]
        stmt = stmt.where(and_(*filters))
        return int(await self.session.scalar(stmt) or 0)

    async def _count_since(self, model: type[Any], since: datetime, *clauses: Any) -> int:
        return await self._count(model, model.created_at >= since, *clauses)
