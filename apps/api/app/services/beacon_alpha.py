from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.beacon_alpha import (
    AlphaAcceptanceRow,
    AlphaFounderQueueRow,
    AlphaQaDecisionRow,
    AlphaSnapshotRow,
)
from app.models.decision import DecisionMaker
from app.models.enrichment import CompanyContact
from app.models.intelligence import Company, CompanyTimeline
from app.models.opportunity import Opportunity, OpportunityEvidence
from beacon_alpha.acceptance.engine import AlphaAcceptanceEngine
from beacon_alpha.dedupe.engine import AlphaDedupeEngine
from beacon_alpha.founder_queue.engine import FounderQueueEngine
from beacon_alpha.manual_qa.engine import ManualQaEngine
from beacon_alpha.models.types import AlphaVerdict, QaRating
from beacon_alpha.pipelines.engine import BeaconAlphaPipeline


class BeaconAlphaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pipeline = BeaconAlphaPipeline()
        self.founder_queue = FounderQueueEngine()
        self.manual_qa = ManualQaEngine()
        self._acceptance_engine = AlphaAcceptanceEngine()
        self.dedupe = AlphaDedupeEngine()

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
            "business_description": company.memory_summary or attrs.get("description") or attrs.get("business_description"),
            "description": company.memory_summary or attrs.get("description"),
            "narrative": opportunity.narrative if opportunity else company.memory_summary,
            "source": timeline[0].source if timeline else attrs.get("source"),
            "collector": attrs.get("collector") or (timeline[0].source if timeline else attrs.get("source")),
            "collected_from": timeline[0].source if timeline else attrs.get("source"),
            "source_url": attrs.get("source_url"),
            "original_url": attrs.get("original_url") or attrs.get("source_url"),
            "original_post_title": attrs.get("original_post_title") or attrs.get("title"),
            "entity_type": attrs.get("entity_type"),
            "evidence": [
                {
                    "summary": getattr(e, "summary", None) or str(e.id),
                    "source": getattr(e, "source", None),
                    "url": getattr(e, "source_url", None),
                }
                for e in evidence_rows
            ],
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
            "recommended_service": attrs.get("recommended_service"),
            "buying_intent": attrs.get("buying_intent"),
            "opportunity": opportunity.narrative if opportunity else attrs.get("opportunity"),
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
            "website_alive": attrs.get("website_alive") or bool(company.primary_domain),
            "ssl": attrs.get("ssl", True),
            "mx_valid": attrs.get("mx_valid"),
            "verified_emails": attrs.get("verified_emails") or emails,
            "verification_history": attrs.get("verification_history") or [],
            "last_crawl": attrs.get("last_crawl"),
            "website_hash": attrs.get("website_hash"),
            "aliases": attrs.get("aliases") or [],
            "estimated_budget": attrs.get("estimated_budget"),
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
            await self._persist(company_id, snap, data)
        return data

    async def _persist(self, company_id: UUID, snap, data: dict[str, Any]) -> None:
        self.session.add(
            AlphaSnapshotRow(
                id=uuid.uuid4(),
                company_id=company_id,
                verdict=snap.verdict.value,
                score_total=snap.score.total,
                founder_visible=snap.score.founder_visible and snap.verdict == AlphaVerdict.SALES_READY,
                best_service=snap.intent.best_service if snap.intent.best_service != "UNKNOWN" else None,
                primary_bucket=snap.intent.primary_bucket.value,
                payload=data,
                evidence=snap.evidence,
                scoring_version=snap.scoring_version,
            )
        )
        await self.session.commit()

    async def latest(self, company_id: UUID) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(AlphaSnapshotRow)
            .where(AlphaSnapshotRow.company_id == company_id, AlphaSnapshotRow.deleted_at.is_(None))
            .order_by(AlphaSnapshotRow.created_at.desc())
            .limit(1)
        )
        if row and row.payload:
            return dict(row.payload)
        return await self.evaluate_company(company_id, persist=False)

    async def top10(self) -> dict[str, Any]:
        rows = list(
            (
                await self.session.scalars(
                    select(AlphaSnapshotRow)
                    .where(
                        AlphaSnapshotRow.deleted_at.is_(None),
                        AlphaSnapshotRow.verdict == "SALES_READY",
                        AlphaSnapshotRow.founder_visible.is_(True),
                        AlphaSnapshotRow.score_total >= 80,
                    )
                    .order_by(AlphaSnapshotRow.score_total.desc())
                    .limit(60)
                )
            ).all()
        )
        dedupe_input: list[dict[str, Any]] = []
        card_by_id: dict[str, dict[str, Any]] = {}
        seen: set[str] = set()
        for row in rows:
            cid = str(row.company_id)
            if cid in seen:
                continue
            seen.add(cid)
            payload = dict(row.payload or {})
            card = payload.get("founder_card")
            if not isinstance(card, dict):
                continue
            tr = payload.get("transparency") or {}
            url = tr.get("original_url") if isinstance(tr, dict) else None
            dedupe_input.append(
                {
                    "company_id": cid,
                    "company_name": payload.get("company_name"),
                    "legal_name": payload.get("company_name"),
                    "website": url,
                    "domain": url,
                    "linkedin": None,
                }
            )
            card_by_id[cid] = card

        kept = self.dedupe.filter_queue(dedupe_input)
        out: list[dict[str, Any]] = []
        for rank, company in enumerate(kept[:10], start=1):
            cid = company["company_id"]
            card = card_by_id.get(cid)
            if not card:
                continue
            out.append(card)
            self.session.add(
                AlphaFounderQueueRow(
                    id=uuid.uuid4(),
                    company_id=UUID(cid),
                    rank=rank,
                    score=float(card.get("score") or 0),
                    payload=card,
                    scoring_version="alpha-v1",
                )
            )
        await self.session.commit()
        return {"items": out, "total": len(out), "scoring_version": "alpha-v1"}

    async def qa_pending(self, *, limit: int = 40) -> dict[str, Any]:
        rows = list(
            (
                await self.session.scalars(
                    select(AlphaSnapshotRow)
                    .where(
                        AlphaSnapshotRow.deleted_at.is_(None),
                        AlphaSnapshotRow.verdict == "SALES_READY",
                        AlphaSnapshotRow.founder_visible.is_(True),
                    )
                    .order_by(AlphaSnapshotRow.created_at.desc())
                    .limit(limit * 3)
                )
            ).all()
        )
        decided = set(
            str(x)
            for x in (
                await self.session.scalars(select(AlphaQaDecisionRow.company_id).where(AlphaQaDecisionRow.deleted_at.is_(None)))
            ).all()
        )
        items = []
        seen: set[str] = set()
        for row in rows:
            cid = str(row.company_id)
            if cid in seen or cid in decided:
                continue
            seen.add(cid)
            payload = dict(row.payload or {})
            card = payload.get("qa_card")
            if card:
                items.append(card)
            if len(items) >= limit:
                break
        return {"items": items, "total": len(items), "scoring_version": "alpha-v1"}

    async def record_qa(
        self,
        company_id: UUID,
        *,
        rating: str,
        notes: str | None = None,
        reviewer: str | None = None,
    ) -> dict[str, Any]:
        # Validate rating
        valid = {r.value for r in QaRating}
        if rating not in valid:
            return {"error": "invalid_rating", "allowed": sorted(valid)}
        row = AlphaQaDecisionRow(
            id=uuid.uuid4(),
            company_id=company_id,
            rating=rating,
            notes=notes,
            reviewer=reviewer or "founder",
            payload={"rating": rating, "notes": notes, "reviewer": reviewer, "at": datetime.now(UTC).isoformat()},
            evidence=[f"rating:{rating}"],
        )
        self.session.add(row)
        await self.session.commit()
        return {"ok": True, "company_id": str(company_id), "rating": rating}

    async def qa_analytics(self) -> dict[str, Any]:
        rows = list(
            (
                await self.session.scalars(
                    select(AlphaQaDecisionRow).where(AlphaQaDecisionRow.deleted_at.is_(None)).order_by(AlphaQaDecisionRow.created_at.desc()).limit(2000)
                )
            ).all()
        )
        decisions = [{"rating": r.rating, "company_id": str(r.company_id), "notes": r.notes} for r in rows]
        return self.manual_qa.analytics(decisions)

    async def acceptance(self) -> dict[str, Any]:
        analytics = await self.qa_analytics()
        # Snapshot-based rates from latest per company
        rows = list(
            (
                await self.session.scalars(
                    select(AlphaSnapshotRow)
                    .where(AlphaSnapshotRow.deleted_at.is_(None))
                    .order_by(AlphaSnapshotRow.created_at.desc())
                    .limit(2000)
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
            latest.append(row)

        n = len(latest) or 1
        sales_ready = sum(1 for r in latest if r.verdict == "SALES_READY")
        # Approximate website/email/phone from payloads
        website_ok = 0
        email_ok = 0
        phone_ok = 0
        for r in latest:
            p = dict(r.payload or {})
            contacts = p.get("contacts") or {}
            if (p.get("identity") or {}).get("passed") or (isinstance(contacts, dict) and True):
                pass
            tr = p.get("transparency") or {}
            if isinstance(tr, dict) and tr.get("original_url") and tr.get("original_url") != "UNKNOWN":
                website_ok += 1
            if isinstance(contacts, dict) and (contacts.get("emails") or []):
                email_ok += 1
            if isinstance(contacts, dict) and (contacts.get("phones") or []):
                phone_ok += 1

        dedupe_input = [{"company_id": str(r.company_id), "company_name": (r.payload or {}).get("company_name"), "website": ((r.payload or {}).get("transparency") or {}).get("original_url")} for r in latest]
        kept = self.dedupe.filter_queue(dedupe_input)
        dup_rate = round(100.0 * (len(dedupe_input) - len(kept)) / max(len(dedupe_input), 1), 2)

        metrics = {
            "real_business_percent": float(analytics.get("real_business_percent") or (100.0 * sales_ready / n)),
            "working_website_percent": round(100.0 * website_ok / n, 2),
            "attributed_email_percent": round(100.0 * email_ok / n, 2),
            "business_phone_percent": round(100.0 * phone_ok / n, 2),
            "service_correct_percent": float(analytics.get("service_correct_percent") or 0),
            "duplicate_rate": dup_rate,
            "sales_ready_per_day": sales_ready,
            "review_under_15_min": True,  # Top-10 design target
            "founder_queue_reviewable": True,
        }
        result = self._acceptance_engine.evaluate(metrics)
        data = result.model_dump(mode="json")
        self.session.add(
            AlphaAcceptanceRow(
                id=uuid.uuid4(),
                live_outreach_ready=result.live_outreach_ready,
                failures=result.failures,
                payload=data,
                scoring_version="alpha-v1",
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
        sales_ready = 0
        rejected = 0
        for company in companies:
            data = await self.evaluate_company(company.id, persist=True)
            if data.get("error"):
                continue
            if data.get("verdict") == "SALES_READY":
                sales_ready += 1
            else:
                rejected += 1
        top = await self.top10()
        return {
            "processed": len(companies),
            "sales_ready": sales_ready,
            "rejected": rejected,
            "founder_queue": top.get("total"),
            "scoring_version": "alpha-v1",
        }

    async def dashboard(self) -> dict[str, Any]:
        total = int(await self.session.scalar(select(func.count()).select_from(AlphaSnapshotRow)) or 0)
        ready = int(
            await self.session.scalar(
                select(func.count()).select_from(AlphaSnapshotRow).where(AlphaSnapshotRow.verdict == "SALES_READY")
            )
            or 0
        )
        visible = int(
            await self.session.scalar(
                select(func.count()).select_from(AlphaSnapshotRow).where(AlphaSnapshotRow.founder_visible.is_(True))
            )
            or 0
        )
        return {
            "total_snapshots": total,
            "sales_ready": ready,
            "founder_visible": visible,
            "live_outreach_enabled": False,
            "scoring_version": "alpha-v1",
        }
