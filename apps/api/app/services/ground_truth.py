from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decision import DecisionMaker
from app.models.enrichment import CompanyContact
from app.models.ground_truth import GtAcceptanceRow, GtDailyReportRow, GtFounderQueueRow, GtSnapshotRow
from app.models.intelligence import Company, CompanyTimeline
from app.models.opportunity import Opportunity, OpportunityEvidence
from ground_truth.acceptance.engine import GtAcceptanceEngine
from ground_truth.daily_report.engine import DailyImprovementReportEngine
from ground_truth.founder_queue.engine import GtFounderQueueEngine
from ground_truth.pipelines.engine import GroundTruthPipeline
from ground_truth.quality_funnel.engine import QualityFunnelEngine


class GroundTruthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pipeline = GroundTruthPipeline()
        self.funnel = QualityFunnelEngine()
        self.daily = DailyImprovementReportEngine()
        self._acceptance_engine = GtAcceptanceEngine()
        self.queue = GtFounderQueueEngine()

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
            "legal_name": attrs.get("legal_name") or company.name,
            "website": company.primary_domain,
            "domain": company.primary_domain,
            "industry": company.industry,
            "country": attrs.get("country") or attrs.get("location"),
            "employees": attrs.get("employees") or attrs.get("employee_estimate"),
            "description": company.memory_summary or attrs.get("description"),
            "business_description": company.memory_summary or attrs.get("business_description"),
            "narrative": opportunity.narrative if opportunity else company.memory_summary,
            "source": timeline[0].source if timeline else attrs.get("source"),
            "source_url": attrs.get("source_url"),
            "entity_type": attrs.get("entity_type"),
            "evidence": [{"summary": getattr(e, "summary", None) or str(e.id), "source": getattr(e, "source", None)} for e in evidence_rows],
            "timeline": [
                {
                    "signal_type": t.signal_type,
                    "summary": t.summary,
                    "source": t.source,
                    "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                }
                for t in timeline
            ],
            "signals": [t.signal_type for t in timeline],
            "technologies": attrs.get("technologies") or [],
            "products": attrs.get("products") or [],
            "funding": attrs.get("funding"),
            "stage": attrs.get("stage"),
            "decision_makers": [
                {
                    "name": d.name,
                    "role": d.role,
                    "email": d.work_email,
                    "phone": d.business_phone,
                    "linkedin_url": d.linkedin_url,
                    "source": d.source,
                    "confidence": d.confidence,
                }
                for d in dms
            ],
            "emails": list(dict.fromkeys(emails)),
            "phones": list(dict.fromkeys(phones)),
            "linkedin_company": attrs.get("linkedin_company_url") or attrs.get("linkedin_url"),
            "website_html": attrs.get("website_html"),
            "discovered_pages": attrs.get("discovered_pages"),
            "website_alive": attrs.get("website_alive") or bool(company.primary_domain),
            "ssl": attrs.get("ssl", True),
            "mx_valid": attrs.get("mx_valid"),
            "recommended_service": attrs.get("recommended_service"),
            "estimated_deal": attrs.get("estimated_deal") or attrs.get("estimated_budget"),
            "why_now": attrs.get("why_now"),
            "collected_at": company.created_at,
            "last_seen_at": company.last_seen_at,
        }

    async def evaluate_company(self, company_id: UUID, *, persist: bool = True) -> dict[str, Any]:
        payload = await self.build_payload(company_id)
        if payload is None:
            return {"error": "not_found"}
        snap = self.pipeline.evaluate(payload)
        data = snap.model_dump(mode="json")
        if persist:
            self.session.add(
                GtSnapshotRow(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    verdict=snap.verdict.value,
                    trust=snap.trust,
                    readiness=snap.readiness,
                    lock_unlocked=snap.production_lock.unlocked,
                    questions_complete=snap.questions.all_answered,
                    payload=data,
                    evidence=snap.evidence,
                    scoring_version=snap.scoring_version,
                )
            )
            await self.session.commit()
        return data

    async def latest(self, company_id: UUID) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(GtSnapshotRow)
            .where(GtSnapshotRow.company_id == company_id, GtSnapshotRow.deleted_at.is_(None))
            .order_by(GtSnapshotRow.created_at.desc())
            .limit(1)
        )
        if row and row.payload:
            return dict(row.payload)
        return await self.evaluate_company(company_id, persist=False)

    async def founder_queue(self) -> dict[str, Any]:
        rows = list(
            (
                await self.session.scalars(
                    select(GtSnapshotRow)
                    .where(
                        GtSnapshotRow.deleted_at.is_(None),
                        GtSnapshotRow.lock_unlocked.is_(True),
                        GtSnapshotRow.questions_complete.is_(True),
                        GtSnapshotRow.verdict.in_(["SALES_READY", "ENTERPRISE_READY"]),
                    )
                    .order_by(GtSnapshotRow.trust.desc())
                    .limit(40)
                )
            ).all()
        )
        snaps = []
        from ground_truth.models.types import GtSnapshot

        seen: set[str] = set()
        for row in rows:
            cid = str(row.company_id)
            if cid in seen:
                continue
            seen.add(cid)
            snaps.append(GtSnapshot.model_validate(row.payload))
        items = self.queue.top10(snaps)
        out = []
        for rank, item in enumerate(items, start=1):
            data = item.model_dump(mode="json")
            out.append(data)
            self.session.add(
                GtFounderQueueRow(
                    id=uuid.uuid4(),
                    company_id=UUID(item.company_id),
                    rank=rank,
                    trust=item.trust,
                    payload=data,
                    scoring_version="alpha-plus-v1",
                )
            )
        await self.session.commit()
        return {"items": out, "total": len(out), "scoring_version": "alpha-plus-v1"}

    async def quality_funnel(self) -> dict[str, Any]:
        rows = list(
            (
                await self.session.scalars(
                    select(GtSnapshotRow).where(GtSnapshotRow.deleted_at.is_(None)).order_by(GtSnapshotRow.created_at.desc()).limit(2000)
                )
            ).all()
        )
        seen: set[str] = set()
        latest = []
        for row in rows:
            cid = str(row.company_id)
            if cid in seen:
                continue
            seen.add(cid)
            latest.append(dict(row.payload or {}))
        return self.funnel.compute(latest).model_dump(mode="json")

    async def daily_report(self) -> dict[str, Any]:
        funnel_data = await self.quality_funnel()
        from ground_truth.models.types import QualityFunnel

        funnel = QualityFunnel.model_validate(funnel_data)
        rows = list(
            (
                await self.session.scalars(
                    select(GtSnapshotRow).where(GtSnapshotRow.deleted_at.is_(None)).order_by(GtSnapshotRow.created_at.desc()).limit(2000)
                )
            ).all()
        )
        seen: set[str] = set()
        latest = []
        for row in rows:
            cid = str(row.company_id)
            if cid in seen:
                continue
            seen.add(cid)
            latest.append(dict(row.payload or {}))
        report = self.daily.build(latest, funnel=funnel)
        data = report.model_dump(mode="json")
        self.session.add(
            GtDailyReportRow(
                id=uuid.uuid4(),
                report_date=report.date,
                collected=report.collected,
                rejected=report.rejected,
                sales_ready=report.sales_ready,
                average_quality=report.average_quality,
                payload=data,
                scoring_version="alpha-plus-v1",
            )
        )
        await self.session.commit()
        return data

    async def acceptance(self) -> dict[str, Any]:
        funnel = await self.quality_funnel()
        n = max(int(funnel.get("companies") or 0), 1)
        metrics = {
            "real_companies": int(funnel.get("companies") or 0) - int(funnel.get("fake") or 0),
            "real_identities_percent": round(100.0 * (n - int(funnel.get("fake") or 0)) / n, 2),
            "websites_percent": round(100.0 * (n - int(funnel.get("missing_website") or 0)) / n, 2),
            "decision_makers_percent": 0.0,
            "verified_contact_percent": 0.0,
            "duplicate_percent": 0.0,
            "fake_percent": round(100.0 * int(funnel.get("fake") or 0) / n, 2),
            "evidence_coverage_percent": round(100.0 * (n - int(funnel.get("missing_evidence") or 0)) / n, 2),
            "founder_email_confidence_percent": 0.0,
        }
        # Improve DM/contact rates from latest payloads
        rows = list(
            (
                await self.session.scalars(
                    select(GtSnapshotRow).where(GtSnapshotRow.deleted_at.is_(None)).order_by(GtSnapshotRow.created_at.desc()).limit(2000)
                )
            ).all()
        )
        seen: set[str] = set()
        dm_ok = contact_ok = 0
        count = 0
        for row in rows:
            cid = str(row.company_id)
            if cid in seen:
                continue
            seen.add(cid)
            count += 1
            p = dict(row.payload or {})
            truth = p.get("truth") or {}
            if (truth.get("decision_makers") or []):
                dm_ok += 1
            if (truth.get("contacts_email") or []) or (truth.get("contacts_phone") or []):
                contact_ok += 1
        if count:
            metrics["decision_makers_percent"] = round(100.0 * dm_ok / count, 2)
            metrics["verified_contact_percent"] = round(100.0 * contact_ok / count, 2)
            metrics["founder_email_confidence_percent"] = round(100.0 * int(funnel.get("sales_ready") or 0) / count, 2)

        result = self._acceptance_engine.evaluate(metrics)
        data = result.model_dump(mode="json")
        self.session.add(
            GtAcceptanceRow(
                id=uuid.uuid4(),
                production_unlocked=result.production_unlocked,
                failures=result.failures,
                payload=data,
                scoring_version="alpha-plus-v1",
            )
        )
        await self.session.commit()
        return data

    async def process_pending(self, *, limit: int = 80) -> dict[str, Any]:
        companies = list(
            (
                await self.session.scalars(
                    select(Company).where(Company.deleted_at.is_(None)).order_by(Company.last_seen_at.desc().nulls_last()).limit(limit)
                )
            ).all()
        )
        sales_ready = rejected = 0
        for company in companies:
            data = await self.evaluate_company(company.id, persist=True)
            if data.get("error"):
                continue
            if data.get("verdict") in {"SALES_READY", "ENTERPRISE_READY"}:
                sales_ready += 1
            else:
                rejected += 1
        queue = await self.founder_queue()
        report = await self.daily_report()
        return {
            "processed": len(companies),
            "sales_ready": sales_ready,
            "rejected": rejected,
            "founder_queue": queue.get("total"),
            "daily_report": report,
            "scoring_version": "alpha-plus-v1",
        }

    async def dashboard(self) -> dict[str, Any]:
        funnel = await self.quality_funnel()
        return {
            "funnel": funnel,
            "production_send_locked": True,
            "scoring_version": "alpha-plus-v1",
            "question": "Would Vansh confidently send an email to this company today?",
        }
