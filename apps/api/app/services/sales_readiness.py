from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decision import DecisionMaker
from app.models.enrichment import CompanyContact
from app.models.intelligence import Company, CompanyTimeline
from app.models.opportunity import Opportunity, OpportunityEvidence
from app.models.sales_readiness import (
    SalesContactReadinessRow,
    SalesIdentityScoreRow,
    SalesIntentScoreRow,
    SalesReadinessSnapshotRow,
    SalesRevenuePotentialRow,
    SalesServiceMatchV2Row,
    SalesTrustScoreRow,
)
from sales_readiness.pipelines.engine import SalesReadinessPipeline


class SalesReadinessService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pipeline = SalesReadinessPipeline()

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

        return {
            "company_id": str(company_id),
            "company_name": company.name,
            "website": company.primary_domain,
            "domain": company.primary_domain,
            "industry": company.industry,
            "country": attrs.get("country") or attrs.get("location"),
            "employees": attrs.get("employees") or attrs.get("employee_estimate"),
            "source": timeline[0].source if timeline else None,
            "evidence": evidence_rows,
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
            "last_seen_at": company.last_seen_at,
            "collected_at": company.created_at,
            "verification_score": attrs.get("verification_score"),
            "ssl": True,
            "seo_score": attrs.get("seo_score"),
            "pricing_page": attrs.get("pricing_page"),
            "has_careers": attrs.get("has_careers"),
            "has_chatbot": attrs.get("has_chatbot"),
            "is_saas": attrs.get("is_saas"),
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
        row = SalesReadinessSnapshotRow(
            id=uuid.uuid4(),
            company_id=company_id,
            status=snap.status.value,
            trust_score=snap.trust_score,
            stars=snap.stars,
            eligible_for_revenue_hunter=snap.eligible_for_revenue_hunter,
            visible_in_founder_queue=snap.visible_in_founder_queue,
            payload=data,
            evidence=snap.evidence,
            scoring_version=snap.scoring_version,
        )
        self.session.add(row)
        await self.session.flush()
        self.session.add(
            SalesIdentityScoreRow(
                id=uuid.uuid4(),
                company_id=company_id,
                snapshot_id=row.id,
                identity_complete=snap.identity.identity_complete,
                missing_fields=snap.identity.missing_fields,
                payload=snap.identity.model_dump(mode="json"),
            )
        )
        self.session.add(
            SalesContactReadinessRow(
                id=uuid.uuid4(),
                company_id=company_id,
                snapshot_id=row.id,
                coverage_percent=snap.contacts.coverage_percent,
                verified_email_count=snap.contacts.verified_email_count,
                verified_phone_count=snap.contacts.verified_phone_count,
                payload=snap.contacts.model_dump(mode="json"),
            )
        )
        self.session.add(
            SalesIntentScoreRow(
                id=uuid.uuid4(),
                company_id=company_id,
                snapshot_id=row.id,
                level=snap.intent.level.value,
                score=snap.intent.score,
                payload=snap.intent.model_dump(mode="json"),
            )
        )
        for svc in snap.services:
            self.session.add(
                SalesServiceMatchV2Row(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    snapshot_id=row.id,
                    recommended_service=svc.recommended_service,
                    estimated_value=svc.estimated_value,
                    confidence=svc.confidence,
                    reason=svc.reason,
                    evidence=svc.evidence,
                )
            )
        self.session.add(
            SalesRevenuePotentialRow(
                id=uuid.uuid4(),
                company_id=company_id,
                snapshot_id=row.id,
                deal_size=snap.revenue.deal_size.value,
                probability=snap.revenue.probability,
                sales_cycle=snap.revenue.sales_cycle,
                recommended_founder_time=snap.revenue.recommended_founder_time,
                payload=snap.revenue.model_dump(mode="json"),
            )
        )
        self.session.add(
            SalesTrustScoreRow(
                id=uuid.uuid4(),
                company_id=company_id,
                snapshot_id=row.id,
                overall=snap.trust.overall,
                breakdown=snap.trust.model_dump(mode="json"),
                evidence=snap.trust.evidence,
            )
        )
        await self.session.commit()

    async def latest(self, company_id: UUID) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(SalesReadinessSnapshotRow)
            .where(SalesReadinessSnapshotRow.company_id == company_id, SalesReadinessSnapshotRow.deleted_at.is_(None))
            .order_by(SalesReadinessSnapshotRow.created_at.desc())
            .limit(1)
        )
        if row and row.payload:
            return dict(row.payload)
        return await self.evaluate_company(company_id, persist=False)

    async def dashboard(self) -> dict[str, Any]:
        total = int(await self.session.scalar(select(func.count()).select_from(SalesReadinessSnapshotRow)) or 0)
        by_status = {}
        for status in ("NOT READY", "RESEARCH REQUIRED", "CONTACT READY", "SALES READY", "ENTERPRISE READY"):
            by_status[status] = int(
                await self.session.scalar(
                    select(func.count()).select_from(SalesReadinessSnapshotRow).where(SalesReadinessSnapshotRow.status == status)
                )
                or 0
            )
        rh = int(
            await self.session.scalar(
                select(func.count())
                .select_from(SalesReadinessSnapshotRow)
                .where(SalesReadinessSnapshotRow.eligible_for_revenue_hunter.is_(True))
            )
            or 0
        )
        fq = int(
            await self.session.scalar(
                select(func.count())
                .select_from(SalesReadinessSnapshotRow)
                .where(SalesReadinessSnapshotRow.visible_in_founder_queue.is_(True))
            )
            or 0
        )
        return {
            "total_snapshots": total,
            "by_status": by_status,
            "eligible_for_revenue_hunter": rh,
            "visible_in_founder_queue": fq,
            "scoring_version": "sre-v1",
        }

    async def search(self, *, q: str | None = None, status: str | None = None, limit: int = 50) -> dict[str, Any]:
        stmt = (
            select(SalesReadinessSnapshotRow)
            .where(SalesReadinessSnapshotRow.deleted_at.is_(None))
            .order_by(SalesReadinessSnapshotRow.created_at.desc())
            .limit(limit * 3)
        )
        if status:
            stmt = stmt.where(SalesReadinessSnapshotRow.status == status)
        rows = list((await self.session.scalars(stmt)).all())
        # Dedupe to latest per company
        seen: set[str] = set()
        items: list[dict[str, Any]] = []
        needle = (q or "").strip().lower()
        for row in rows:
            cid = str(row.company_id)
            if cid in seen:
                continue
            seen.add(cid)
            payload = dict(row.payload or {})
            name = str(payload.get("company_name") or "")
            if needle and needle not in name.lower() and needle not in cid:
                continue
            items.append(payload)
            if len(items) >= limit:
                break
        return {"results": items, "total": len(items), "scoring_version": "sre-v1"}

    async def list_by_flag(self, *, flag: str, limit: int = 50) -> dict[str, Any]:
        stmt = select(SalesReadinessSnapshotRow).where(SalesReadinessSnapshotRow.deleted_at.is_(None))
        if flag == "outreach-ready":
            stmt = stmt.where(SalesReadinessSnapshotRow.visible_in_founder_queue.is_(True))
        elif flag == "enterprise":
            stmt = stmt.where(SalesReadinessSnapshotRow.status == "ENTERPRISE READY")
        elif flag == "high-intent":
            stmt = stmt.where(SalesReadinessSnapshotRow.status.in_(["SALES READY", "ENTERPRISE READY", "CONTACT READY"]))
        else:
            stmt = stmt.where(SalesReadinessSnapshotRow.eligible_for_revenue_hunter.is_(True))
        rows = list(
            (
                await self.session.scalars(stmt.order_by(SalesReadinessSnapshotRow.trust_score.desc()).limit(limit * 3))
            ).all()
        )
        seen: set[str] = set()
        items = []
        for row in rows:
            cid = str(row.company_id)
            if cid in seen:
                continue
            seen.add(cid)
            payload = dict(row.payload or {})
            if flag == "high-intent":
                level = ((payload.get("intent") or {}) if isinstance(payload.get("intent"), dict) else {}).get("level")
                if level not in {"Very High", "High"}:
                    continue
            items.append(payload)
            if len(items) >= limit:
                break
        return {"results": items, "total": len(items), "flag": flag, "scoring_version": "sre-v1"}

    async def trust_dashboard(self) -> dict[str, Any]:
        avg = await self.session.scalar(select(func.avg(SalesTrustScoreRow.overall)))
        count = int(await self.session.scalar(select(func.count()).select_from(SalesTrustScoreRow)) or 0)
        return {
            "average_trust": round(float(avg or 0.0), 2),
            "trust_rows": count,
            "dashboard": await self.dashboard(),
            "scoring_version": "sre-v1",
        }

    async def process_pending(self, *, limit: int = 40) -> dict[str, Any]:
        # Prefer companies with domains that lack a recent SRE snapshot
        companies = list(
            (
                await self.session.scalars(
                    select(Company)
                    .where(Company.deleted_at.is_(None), Company.primary_domain.is_not(None))
                    .order_by(Company.last_seen_at.desc().nulls_last())
                    .limit(limit)
                )
            ).all()
        )
        evaluated = 0
        sales_ready = 0
        for company in companies:
            data = await self.evaluate_company(company.id, persist=True)
            if data.get("error"):
                continue
            evaluated += 1
            if data.get("eligible_for_revenue_hunter"):
                sales_ready += 1
        return {"evaluated": evaluated, "sales_ready_or_enterprise": sales_ready, "scoring_version": "sre-v1"}
