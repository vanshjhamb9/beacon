from __future__ import annotations

import uuid
from time import perf_counter
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decision import DecisionMaker
from app.models.enrichment import CompanyContact
from app.models.intelligence import Company, CompanyTimeline
from app.models.opportunity import Opportunity, OpportunityEvidence
from app.models.revenue_data_recovery import (
    RdiDossierRow,
    RdiMetricsSnapshotRow,
    RdiRecoveryQueueRow,
    RdiSnapshotRow,
)
from revenue_data_recovery.daily_worker.engine import DailyRecoveryWorker
from revenue_data_recovery.metrics.engine import RecoveryMetricsEngine
from revenue_data_recovery.pipelines.engine import RevenueDataRecoveryPipeline


class RevenueDataRecoveryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pipeline = RevenueDataRecoveryPipeline()
        self.metrics = RecoveryMetricsEngine()
        self.worker = DailyRecoveryWorker(self.pipeline)

    async def build_payload(self, company_id: UUID) -> dict[str, Any] | None:
        company = await self.session.get(Company, company_id)
        if company is None:
            return None
        attrs = company.attributes or {}
        timeline = list(
            (
                await self.session.scalars(
                    select(CompanyTimeline)
                    .where(CompanyTimeline.company_id == company_id, CompanyTimeline.deleted_at.is_(None))
                    .order_by(CompanyTimeline.timestamp.asc())
                    .limit(50)
                )
            ).all()
        )
        evidence_rows = list(
            (
                await self.session.scalars(
                    select(OpportunityEvidence)
                    .where(OpportunityEvidence.company_id == company_id, OpportunityEvidence.deleted_at.is_(None))
                    .limit(40)
                )
            ).all()
        )
        opportunity = await self.session.scalar(
            select(Opportunity)
            .where(Opportunity.company_id == company_id, Opportunity.deleted_at.is_(None))
            .order_by(Opportunity.opportunity_score.desc())
            .limit(1)
        )
        dms = list(
            (
                await self.session.scalars(
                    select(DecisionMaker)
                    .where(DecisionMaker.company_id == company_id, DecisionMaker.deleted_at.is_(None))
                    .limit(20)
                )
            ).all()
        )
        contacts = list(
            (
                await self.session.scalars(
                    select(CompanyContact)
                    .where(CompanyContact.company_id == company_id, CompanyContact.deleted_at.is_(None))
                    .limit(40)
                )
            ).all()
        )
        emails = [c.value for c in contacts if "email" in str(c.kind).lower()]
        phones = [c.value for c in contacts if "phone" in str(c.kind).lower()]
        for dm in dms:
            if dm.work_email:
                emails.append(dm.work_email)
            if dm.business_phone:
                phones.append(dm.business_phone)

        evidence_payload = []
        for e in evidence_rows:
            evidence_payload.append(
                {
                    "summary": getattr(e, "summary", None) or getattr(e, "snippet", None) or str(e.id),
                    "source": getattr(e, "source", None),
                    "url": getattr(e, "source_url", None) or getattr(e, "url", None),
                }
            )

        return {
            "company_id": str(company_id),
            "company_name": company.name,
            "legal_name": attrs.get("legal_name") or company.name,
            "website": company.primary_domain,
            "domain": company.primary_domain,
            "industry": company.industry,
            "country": attrs.get("country") or attrs.get("location"),
            "business_category": attrs.get("business_category") or attrs.get("category"),
            "description": company.memory_summary or attrs.get("description"),
            "employees": attrs.get("employees") or attrs.get("employee_estimate"),
            "linkedin_company_url": attrs.get("linkedin_url") or attrs.get("linkedin_company_url"),
            "source": timeline[0].source if timeline else attrs.get("source"),
            "source_url": attrs.get("source_url"),
            "entity_type": attrs.get("entity_type"),
            "evidence": evidence_payload,
            "narrative": opportunity.narrative if opportunity else company.memory_summary,
            "memory_summary": company.memory_summary,
            "technologies": attrs.get("technologies") or [],
            "signals": [t.signal_type for t in timeline],
            "timeline": [
                {
                    "signal_type": t.signal_type,
                    "summary": t.summary,
                    "source": t.source,
                    "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                    "confidence": t.confidence,
                }
                for t in timeline
            ],
            "decision_makers": [
                {
                    "name": d.name,
                    "role": d.role,
                    "title": d.role,
                    "email": d.work_email,
                    "phone": d.business_phone,
                    "linkedin_url": d.linkedin_url,
                    "source": d.source,
                    "source_url": d.source_url,
                    "confidence": d.confidence,
                }
                for d in dms
            ],
            "emails": list(dict.fromkeys(emails)),
            "phones": list(dict.fromkeys(phones)),
            "linkedin_url": attrs.get("linkedin_url"),
            "contact_form": attrs.get("contact_form") or attrs.get("has_contact_form"),
            "has_contact_form": attrs.get("has_contact_form"),
            "collected_urls": attrs.get("collected_urls") or attrs.get("urls") or [],
            "rss": attrs.get("rss"),
            "goap": attrs.get("goap"),
            "public_page": attrs.get("public_page"),
            "website_intelligence": attrs.get("website_intelligence"),
            "technology_profile": attrs.get("technology_profile"),
            "decision_discovery": attrs.get("decision_discovery"),
            "github": attrs.get("github"),
            "github_org": attrs.get("github_org"),
            "website_status": attrs.get("website_status"),
            "is_parked": attrs.get("is_parked"),
            "is_spam": attrs.get("is_spam"),
            "ssl": attrs.get("ssl", True),
            "last_seen_at": company.last_seen_at,
            "collected_at": company.created_at,
            "why_collected": attrs.get("why_collected"),
            "support_headcount": attrs.get("support_headcount"),
        }

    async def evaluate_company(self, company_id: UUID, *, persist: bool = True) -> dict[str, Any]:
        payload = await self.build_payload(company_id)
        if payload is None:
            return {"error": "not_found"}
        snap = self.pipeline.evaluate(payload)
        data = snap.model_dump(mode="json")
        if persist:
            await self._persist(company_id, snap, data)
        return data

    async def _persist(self, company_id: UUID, snap, data: dict[str, Any]) -> None:
        stars = snap.dossier.stars if snap.dossier else 0
        row = RdiSnapshotRow(
            id=uuid.uuid4(),
            company_id=company_id,
            status=snap.status.value,
            recovery_stage=snap.recovery_stage.value,
            trust_score=snap.trust_score,
            stars=stars,
            identity_complete=snap.identity.identity_complete,
            website_verified=snap.website.website_verified,
            is_fake=snap.fake.is_fake,
            eligible_for_revenue_hunter=snap.eligible_for_revenue_hunter,
            visible_in_founder_queue=snap.visible_in_founder_queue,
            payload=data,
            evidence=snap.evidence,
            scoring_version=snap.scoring_version,
        )
        self.session.add(row)
        await self.session.flush()

        if snap.queue_item:
            self.session.add(
                RdiRecoveryQueueRow(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    snapshot_id=row.id,
                    company_name=snap.queue_item.company_name,
                    stage=snap.queue_item.stage.value,
                    priority=snap.queue_item.priority,
                    progress_percent=snap.queue_item.progress_percent,
                    next_action=snap.queue_item.next_action,
                    blocked_reasons=snap.queue_item.blocked_reasons,
                    payload=snap.queue_item.model_dump(mode="json"),
                    evidence=snap.queue_item.evidence,
                )
            )

        if snap.dossier:
            primary = (
                snap.recommendations.primary_service
                if snap.recommendations.primary_service != "UNKNOWN"
                else None
            )
            self.session.add(
                RdiDossierRow(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    snapshot_id=row.id,
                    status=snap.dossier.status.value,
                    stars=snap.dossier.stars,
                    trust_score=snap.dossier.trust_score,
                    estimated_deal=snap.dossier.estimated_deal
                    if snap.dossier.estimated_deal != "UNKNOWN"
                    else None,
                    primary_service=primary,
                    payload=snap.dossier.model_dump(mode="json"),
                    evidence=snap.dossier.evidence,
                )
            )
        await self.session.commit()

    async def latest(self, company_id: UUID) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(RdiSnapshotRow)
            .where(RdiSnapshotRow.company_id == company_id, RdiSnapshotRow.deleted_at.is_(None))
            .order_by(RdiSnapshotRow.created_at.desc())
            .limit(1)
        )
        if row and row.payload:
            return dict(row.payload)
        return await self.evaluate_company(company_id, persist=False)

    async def dossier(self, company_id: UUID) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(RdiDossierRow)
            .where(RdiDossierRow.company_id == company_id, RdiDossierRow.deleted_at.is_(None))
            .order_by(RdiDossierRow.created_at.desc())
            .limit(1)
        )
        if row and row.payload:
            return dict(row.payload)
        data = await self.evaluate_company(company_id, persist=False)
        if data.get("error"):
            return None
        return data.get("dossier")

    async def recovery_queue(self, *, stage: str | None = None, limit: int = 50) -> dict[str, Any]:
        stmt = (
            select(RdiRecoveryQueueRow)
            .where(RdiRecoveryQueueRow.deleted_at.is_(None))
            .order_by(RdiRecoveryQueueRow.priority.desc())
            .limit(limit * 3)
        )
        if stage:
            stmt = stmt.where(RdiRecoveryQueueRow.stage == stage)
        rows = list((await self.session.scalars(stmt)).all())
        seen: set[str] = set()
        items: list[dict[str, Any]] = []
        for row in rows:
            cid = str(row.company_id)
            if cid in seen:
                continue
            seen.add(cid)
            items.append(dict(row.payload or {}))
            if len(items) >= limit:
                break
        return {"items": items, "total": len(items), "scoring_version": "rdi-v1"}

    async def founder_queue(self, *, limit: int = 60) -> dict[str, Any]:
        rows = list(
            (
                await self.session.scalars(
                    select(RdiSnapshotRow)
                    .where(
                        RdiSnapshotRow.deleted_at.is_(None),
                        RdiSnapshotRow.visible_in_founder_queue.is_(True),
                        RdiSnapshotRow.is_fake.is_(False),
                    )
                    .order_by(RdiSnapshotRow.trust_score.desc())
                    .limit(limit * 3)
                )
            ).all()
        )
        seen: set[str] = set()
        items: list[dict[str, Any]] = []
        for row in rows:
            cid = str(row.company_id)
            if cid in seen:
                continue
            seen.add(cid)
            payload = dict(row.payload or {})
            dossier = payload.get("dossier") or payload
            items.append(dossier if isinstance(dossier, dict) else payload)
            if len(items) >= limit:
                break
        return {"items": items, "total": len(items), "scoring_version": "rdi-v1"}

    async def qa_dashboard(self) -> dict[str, Any]:
        # Latest snapshot per company via scan + dedupe
        rows = list(
            (
                await self.session.scalars(
                    select(RdiSnapshotRow)
                    .where(RdiSnapshotRow.deleted_at.is_(None))
                    .order_by(RdiSnapshotRow.created_at.desc())
                    .limit(2000)
                )
            ).all()
        )
        seen: set[str] = set()
        latest: list[dict[str, Any]] = []
        for row in rows:
            cid = str(row.company_id)
            if cid in seen:
                continue
            seen.add(cid)
            latest.append(dict(row.payload or {}))

        metrics = self.metrics.aggregate(latest)
        data = metrics.model_dump(mode="json")
        self.session.add(
            RdiMetricsSnapshotRow(
                id=uuid.uuid4(),
                companies=metrics.companies,
                identity_complete=metrics.identity_complete,
                website_verified=metrics.website_verified,
                sales_ready=metrics.sales_ready,
                fake_companies=metrics.fake_companies,
                founder_queue=metrics.founder_queue,
                recovery_percent=metrics.recovery_percent,
                duplicate_percent=metrics.duplicate_percent,
                payload=data,
                scoring_version="rdi-v1",
            )
        )
        await self.session.commit()
        return data

    async def process_pending(self, *, limit: int = 80) -> dict[str, Any]:
        companies = list(
            (
                await self.session.scalars(
                    select(Company)
                    .where(Company.deleted_at.is_(None))
                    .order_by(Company.last_seen_at.desc().nulls_last())
                    .limit(limit)
                )
            ).all()
        )
        started = perf_counter()
        payloads: list[dict[str, Any]] = []
        for company in companies:
            payload = await self.build_payload(company.id)
            if payload:
                payloads.append(payload)

        recovered = 0
        fake_eliminated = 0
        sales_ready = 0
        stages: dict[str, int] = {}

        for payload in payloads:
            snap = self.pipeline.evaluate(payload)
            await self._persist(UUID(payload["company_id"]), snap, snap.model_dump(mode="json"))
            stage = snap.recovery_stage.value
            stages[stage] = stages.get(stage, 0) + 1
            if snap.fake.is_fake:
                fake_eliminated += 1
            if snap.identity.identity_complete or snap.website.website_verified:
                recovered += 1
            if snap.eligible_for_revenue_hunter:
                sales_ready += 1

        duration_ms = (perf_counter() - started) * 1000.0
        return {
            "processed": len(payloads),
            "recovered": recovered,
            "fake_eliminated": fake_eliminated,
            "sales_ready": sales_ready,
            "stages": stages,
            "duration_ms": round(duration_ms, 2),
            "scoring_version": "rdi-v1",
        }

    async def dashboard(self) -> dict[str, Any]:
        total = int(await self.session.scalar(select(func.count()).select_from(RdiSnapshotRow)) or 0)
        identity = int(
            await self.session.scalar(
                select(func.count()).select_from(RdiSnapshotRow).where(RdiSnapshotRow.identity_complete.is_(True))
            )
            or 0
        )
        website = int(
            await self.session.scalar(
                select(func.count()).select_from(RdiSnapshotRow).where(RdiSnapshotRow.website_verified.is_(True))
            )
            or 0
        )
        fake = int(
            await self.session.scalar(
                select(func.count()).select_from(RdiSnapshotRow).where(RdiSnapshotRow.is_fake.is_(True))
            )
            or 0
        )
        sales = int(
            await self.session.scalar(
                select(func.count())
                .select_from(RdiSnapshotRow)
                .where(RdiSnapshotRow.eligible_for_revenue_hunter.is_(True))
            )
            or 0
        )
        founder = int(
            await self.session.scalar(
                select(func.count())
                .select_from(RdiSnapshotRow)
                .where(RdiSnapshotRow.visible_in_founder_queue.is_(True))
            )
            or 0
        )
        return {
            "total_snapshots": total,
            "identity_complete": identity,
            "website_verified": website,
            "fake_companies": fake,
            "sales_ready": sales,
            "founder_queue": founder,
            "scoring_version": "rdi-v1",
        }
