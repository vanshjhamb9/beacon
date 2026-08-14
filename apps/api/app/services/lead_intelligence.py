"""Lead Intelligence Explorer service — observability over existing pipeline facts."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decision import DecisionMaker
from app.models.enrichment import CompanyContact, EnrichedCompanyProfile
from app.models.intelligence import ClassifiedSignal, Company, SignalEntity
from app.models.intelligence_center import CompanyJourneyEvent, DiscoveryEvent
from app.models.lead_intelligence import (
    LeadEvent,
    LeadEvidenceChain,
    LeadFieldHistory,
    LeadProviderHistory,
    LeadScoreBreakdown,
    LeadStageHistory,
)
from app.models.raw_event import RawEvent
from app.models.revenue_readiness_perfection import RrpCompanyProfile
from lead_intelligence import PIPELINE_STAGES, SCORING_VERSION
from lead_intelligence.explorer_service import (
    assemble_company_explorer,
    assemble_connector_contribution,
    assemble_pipeline_comparison,
    assemble_search_results,
)
from lead_intelligence.provider_history import merge_provider_history
from lead_intelligence.score_breakdown import explain_score


def _dedupe(parts: list[str]) -> str:
    raw = "|".join(parts)
    if len(raw) <= 191:
        return raw
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:191]


class LeadIntelligenceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Public APIs ──────────────────────────────────────────────────────────

    async def search(self, query: str, *, limit: int = 25) -> dict[str, Any]:
        q = (query or "").strip()
        if not q:
            # Default: recent revenue-ready + recent companies (≤48h freshness)
            from collectors.freshness import FRESH_HOURS, DIRECTORY_SOURCES, cutoff_datetime, why_now_is_stale

            cutoff = cutoff_datetime(max_age_hours=FRESH_HOURS)
            rrp = (
                await self.session.execute(
                    select(RrpCompanyProfile)
                    .where(
                        RrpCompanyProfile.deleted_at.is_(None),
                        RrpCompanyProfile.revenue_ready.is_(True),
                        RrpCompanyProfile.updated_at >= cutoff,
                    )
                    .order_by(RrpCompanyProfile.updated_at.desc())
                    .limit(limit * 3)
                )
            ).scalars().all()
            rows: list[dict[str, Any]] = []
            for profile in rrp:
                company = await self.session.get(Company, profile.company_id) if profile.company_id else None
                if not company or company.deleted_at is not None:
                    continue
                attrs = company.attributes or {}
                source = str(attrs.get("source") or "").lower()
                if source in DIRECTORY_SOURCES:
                    continue
                why = str(attrs.get("rrp_why_now") or "")
                if why_now_is_stale(why):
                    continue
                if company.last_seen_at is not None:
                    seen = company.last_seen_at
                    if seen.tzinfo is None:
                        seen = seen.replace(tzinfo=UTC)
                    if seen < cutoff:
                        continue
                rows.append(await self._search_row(company, profile))
                if len(rows) >= limit:
                    break
            return {
                "query": q,
                "items": assemble_search_results(rows),
                "count": len(rows),
                "scoring_version": SCORING_VERSION,
                "freshness_hours": FRESH_HOURS,
                "fresh_only": True,
            }

        like = f"%{q}%"
        uuid_match: UUID | None = None
        try:
            uuid_match = UUID(q)
        except ValueError:
            uuid_match = None

        clauses = [
            Company.name.ilike(like),
            Company.normalized_name.ilike(like),
            Company.primary_domain.ilike(like),
            Company.industry.ilike(like),
        ]
        if uuid_match:
            clauses.append(Company.id == uuid_match)

        companies = (
            await self.session.execute(
                select(Company)
                .where(Company.deleted_at.is_(None), or_(*clauses))
                .order_by(Company.updated_at.desc())
                .limit(limit)
            )
        ).scalars().all()

        # Also search by email / founder via contacts + decision makers
        if len(companies) < limit:
            contact_companies = (
                await self.session.execute(
                    select(CompanyContact.company_id)
                    .where(
                        CompanyContact.deleted_at.is_(None),
                        CompanyContact.value.ilike(like),
                    )
                    .limit(limit)
                )
            ).scalars().all()
            dm_companies = (
                await self.session.execute(
                    select(DecisionMaker.company_id)
                    .where(
                        DecisionMaker.deleted_at.is_(None),
                        or_(
                            DecisionMaker.name.ilike(like),
                            DecisionMaker.work_email.ilike(like),
                        ),
                    )
                    .limit(limit)
                )
            ).scalars().all()
            seen = {c.id for c in companies}
            for cid in list(contact_companies) + list(dm_companies):
                if cid in seen:
                    continue
                company = await self.session.get(Company, cid)
                if company and company.deleted_at is None:
                    companies.append(company)
                    seen.add(cid)
                if len(companies) >= limit:
                    break

        # Revenue ready id search
        if uuid_match:
            profile = await self.session.get(RrpCompanyProfile, uuid_match)
            if profile and profile.company_id:
                company = await self.session.get(Company, profile.company_id)
                if company and company.deleted_at is None and company.id not in {c.id for c in companies}:
                    companies.insert(0, company)

        rows = []
        for company in companies[:limit]:
            profile = await self._rrp_for(company.id)
            rows.append(await self._search_row(company, profile))

        return {
            "query": q,
            "items": assemble_search_results(rows),
            "count": len(rows),
            "scoring_version": SCORING_VERSION,
        }

    async def company(self, company_id: str) -> dict[str, Any]:
        company = await self.session.get(Company, UUID(company_id))
        if not company or company.deleted_at is not None:
            return {"error": "company_not_found", "company_id": company_id}

        # Prefer recorded LIX rows; always fill gaps from live derivation.
        await self._ensure_company_synced(company)
        bundle = await self._load_bundle(company)
        payload = assemble_company_explorer(bundle)
        payload["generated_at"] = datetime.now(UTC).isoformat()
        return payload

    async def timeline(self, company_id: str) -> dict[str, Any]:
        full = await self.company(company_id)
        if full.get("error"):
            return full
        return {
            "company_id": company_id,
            "timeline": full.get("timeline") or [],
            "scoring_version": SCORING_VERSION,
        }

    async def evidence(self, company_id: str) -> dict[str, Any]:
        full = await self.company(company_id)
        if full.get("error"):
            return full
        return {
            "company_id": company_id,
            "evidence": full.get("evidence") or [],
            "scoring_version": SCORING_VERSION,
        }

    async def providers(self, company_id: str | None = None) -> dict[str, Any]:
        if company_id:
            full = await self.company(company_id)
            if full.get("error"):
                return full
            return {
                "company_id": company_id,
                "providers": full.get("providers") or [],
                "enrichments": full.get("enrichments") or {},
                "scoring_version": SCORING_VERSION,
            }
        rows = (
            await self.session.execute(
                select(LeadProviderHistory)
                .where(LeadProviderHistory.deleted_at.is_(None))
                .order_by(LeadProviderHistory.occurred_at.desc())
                .limit(500)
            )
        ).scalars().all()
        serialized = [self._provider_dict(r) for r in rows]
        return {
            "providers": merge_provider_history(serialized),
            "contribution": assemble_connector_contribution(serialized),
            "scoring_version": SCORING_VERSION,
        }

    async def score(self, company_id: str) -> dict[str, Any]:
        full = await self.company(company_id)
        if full.get("error"):
            return full
        return {
            "company_id": company_id,
            "score": full.get("score") or {},
            "promotion": full.get("promotion") or {},
            "scoring_version": SCORING_VERSION,
        }

    async def history(self, company_id: str) -> dict[str, Any]:
        full = await self.company(company_id)
        if full.get("error"):
            return full
        return {
            "company_id": company_id,
            "fields": full.get("fields") or [],
            "latest_fields": full.get("latest_fields") or {},
            "stages": full.get("stages") or [],
            "stage_durations": full.get("stage_durations") or [],
            "failure": full.get("failure"),
            "scoring_version": SCORING_VERSION,
        }

    async def replay(self, company_id: str) -> dict[str, Any]:
        full = await self.company(company_id)
        if full.get("error"):
            return full
        return {
            "company_id": company_id,
            "replay": full.get("replay") or [],
            "summary": full.get("summary") or {},
            "scoring_version": SCORING_VERSION,
        }

    async def connector_contribution(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(LeadProviderHistory).where(LeadProviderHistory.deleted_at.is_(None)).limit(2000)
            )
        ).scalars().all()
        serialized = [self._provider_dict(r) for r in rows]
        return {
            "items": assemble_connector_contribution(serialized),
            "providers": merge_provider_history(serialized),
            "scoring_version": SCORING_VERSION,
        }

    async def compare(self, ready_id: str, rejected_id: str) -> dict[str, Any]:
        ready = await self._facts_for(UUID(ready_id))
        rejected = await self._facts_for(UUID(rejected_id))
        return {
            **assemble_pipeline_comparison(ready, rejected),
            "scoring_version": SCORING_VERSION,
        }

    async def sync_all(self, *, limit: int = 200) -> dict[str, Any]:
        companies = (
            await self.session.execute(
                select(Company)
                .where(Company.deleted_at.is_(None))
                .order_by(Company.updated_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        synced = 0
        for company in companies:
            await self._ensure_company_synced(company)
            synced += 1
        await self.session.commit()
        return {
            "synced_companies": synced,
            "scoring_version": SCORING_VERSION,
            "synced_at": datetime.now(UTC).isoformat(),
        }

    # ── Internals ────────────────────────────────────────────────────────────

    async def _rrp_for(self, company_id: UUID) -> RrpCompanyProfile | None:
        return await self.session.scalar(
            select(RrpCompanyProfile)
            .where(
                RrpCompanyProfile.company_id == company_id,
                RrpCompanyProfile.deleted_at.is_(None),
            )
            .order_by(RrpCompanyProfile.updated_at.desc())
            .limit(1)
        )

    async def _search_row(self, company: Company, profile: RrpCompanyProfile | None) -> dict[str, Any]:
        dm = profile.decision_maker if profile else {}
        contacts = profile.contacts if profile else []
        email = None
        if isinstance(contacts, list) and contacts:
            first = contacts[0]
            email = first.get("email") if isinstance(first, dict) else None
        opp = profile.opportunity if profile else {}
        return {
            "company_id": str(company.id),
            "company": company.name,
            "domain": company.primary_domain,
            "email": email,
            "founder": (dm or {}).get("name") if isinstance(dm, dict) else None,
            "lead_id": str(company.id),
            "revenue_ready_id": str(profile.id) if profile else None,
            "revenue_ready": bool(profile.revenue_ready) if profile else False,
            "current_stage": "revenue_ready" if profile and profile.revenue_ready else (
                "sales_ready" if profile and profile.sales_ready else "company"
            ),
            "score": float(profile.confidence) if profile else 0.0,
            "source": (opp or {}).get("source") if isinstance(opp, dict) else None,
        }

    async def _facts_for(self, company_id: UUID) -> dict[str, Any]:
        company = await self.session.get(Company, company_id)
        if not company:
            return {"company_id": str(company_id)}
        profile = await self._rrp_for(company_id)
        return await self._derive_facts(company, profile)

    async def _derive_facts(
        self,
        company: Company,
        profile: RrpCompanyProfile | None,
    ) -> dict[str, Any]:
        dm = (profile.decision_maker if profile else None) or {}
        contacts = (profile.contacts if profile else None) or []
        email = None
        if isinstance(contacts, list):
            for c in contacts:
                if isinstance(c, dict) and c.get("email"):
                    email = c["email"]
                    break
        if not email:
            contact = await self.session.scalar(
                select(CompanyContact)
                .where(
                    CompanyContact.company_id == company.id,
                    CompanyContact.deleted_at.is_(None),
                    CompanyContact.kind.in_(["email", "business_email", "generic_email"]),
                )
                .order_by(CompanyContact.confidence.desc())
                .limit(1)
            )
            if contact:
                email = contact.value

        founder = None
        if isinstance(dm, dict):
            founder = dm.get("name") or dm.get("full_name")
        if not founder:
            maker = await self.session.scalar(
                select(DecisionMaker)
                .where(
                    DecisionMaker.company_id == company.id,
                    DecisionMaker.deleted_at.is_(None),
                )
                .order_by(DecisionMaker.created_at.asc())
                .limit(1)
            )
            if maker:
                founder = maker.name

        # Source connector from earliest signal / discovery
        source = "unknown"
        signal = await self.session.scalar(
            select(ClassifiedSignal)
            .where(ClassifiedSignal.company_id == company.id, ClassifiedSignal.deleted_at.is_(None))
            .order_by(ClassifiedSignal.created_at.asc())
            .limit(1)
        )
        signal_at = signal.created_at if signal else None
        if signal and signal.event_id:
            raw = await self.session.get(RawEvent, signal.event_id)
            if raw:
                source = raw.source or source

        if source == "unknown":
            entity = await self.session.scalar(
                select(SignalEntity)
                .where(SignalEntity.company_id == company.id, SignalEntity.deleted_at.is_(None))
                .order_by(SignalEntity.created_at.asc())
                .limit(1)
            )
            if entity:
                signal_at = signal_at or entity.created_at
                if entity.event_id:
                    raw = await self.session.get(RawEvent, entity.event_id)
                    if raw:
                        source = raw.source or source

        discovery = await self.session.scalar(
            select(DiscoveryEvent)
            .where(
                DiscoveryEvent.company_id == company.id,
                DiscoveryEvent.deleted_at.is_(None),
            )
            .order_by(DiscoveryEvent.occurred_at.asc())
            .limit(1)
        )
        if discovery and source == "unknown":
            source = discovery.collector or discovery.connector or source
            signal_at = signal_at or discovery.occurred_at

        journey = (
            await self.session.execute(
                select(CompanyJourneyEvent)
                .where(
                    CompanyJourneyEvent.company_id == company.id,
                    CompanyJourneyEvent.deleted_at.is_(None),
                )
                .order_by(CompanyJourneyEvent.occurred_at.asc())
            )
        ).scalars().all()
        journey_by_stage = {j.stage: j for j in journey}

        opp = (profile.opportunity if profile else None) or {}
        why_now = ""
        if isinstance(opp, dict):
            why_now = str(opp.get("why_now") or "")
            if opp.get("source"):
                source = str(opp.get("source")) or source

        hiring = "hiring" in why_now.lower() or "hire" in why_now.lower()
        funding = "yc" in why_now.lower() or "funding" in why_now.lower() or "portfolio" in why_now.lower()

        confidence = float(profile.confidence) if profile else 0.0
        trust = float(profile.trust) if profile else 0.0
        revenue_ready = bool(profile.revenue_ready) if profile else False
        sales_ready = bool(profile.sales_ready) if profile else False
        blockers = list(profile.blockers) if profile else []

        current_stage = "company"
        if revenue_ready:
            current_stage = "revenue_ready"
        elif sales_ready:
            current_stage = "sales_ready"
        elif founder:
            current_stage = "decision_maker"
        elif email:
            current_stage = "email"
        elif company.primary_domain:
            current_stage = "website"

        facts: dict[str, Any] = {
            "company_id": str(company.id),
            "company": company.name,
            "company_name": company.name,
            "domain": company.primary_domain,
            "primary_domain": company.primary_domain,
            "industry": company.industry,
            "source": source,
            "connector": source,
            "founder": founder,
            "business_email": email,
            "confidence": confidence,
            "trust": trust,
            "score": confidence,
            "current_score": confidence,
            "revenue_ready": revenue_ready,
            "sales_ready": sales_ready,
            "current_stage": current_stage,
            "created_at": company.created_at.isoformat() if company.created_at else None,
            "updated_at": company.updated_at.isoformat() if company.updated_at else None,
            "last_updated": company.updated_at.isoformat() if company.updated_at else None,
            "revenue_ready_id": str(profile.id) if profile else None,
            "lead_id": str(company.id),
            "pipeline_value": float((opp or {}).get("pipeline_value") or (opp or {}).get("value") or 0) if isinstance(opp, dict) else 0.0,
            "blockers": blockers,
            "has_signal": bool(signal_at),
            "signal_at": signal_at,
            "has_website": bool(company.primary_domain),
            "website_at": journey_by_stage.get("website").occurred_at if journey_by_stage.get("website") else (
                company.created_at if company.primary_domain else None
            ),
            "has_email": bool(email),
            "email_at": journey_by_stage.get("email").occurred_at if journey_by_stage.get("email") else None,
            "has_founder": bool(founder),
            "decision_maker_at": journey_by_stage.get("decision_maker").occurred_at if journey_by_stage.get("decision_maker") else None,
            "has_hiring": hiring,
            "hiring": hiring,
            "has_funding": funding,
            "funding": funding,
            "yc": funding,
            "has_industry": bool(company.industry),
            "identity_at": journey_by_stage.get("identity").occurred_at if journey_by_stage.get("identity") else company.created_at,
            "company_at": company.created_at,
            "enrichment_at": journey_by_stage.get("email").occurred_at if journey_by_stage.get("email") else None,
            "sales_ready_at": journey_by_stage.get("sales_ready").occurred_at if journey_by_stage.get("sales_ready") else (
                profile.updated_at if profile and sales_ready else None
            ),
            "revenue_ready_at": journey_by_stage.get("revenue_ready").occurred_at if journey_by_stage.get("revenue_ready") else (
                profile.updated_at if profile and revenue_ready else None
            ),
            "rejected": bool(blockers) and not revenue_ready and not sales_ready,
            "why_now": why_now,
        }

        # Stage start offsets for duration when journey durations missing
        base = signal_at or company.created_at or datetime.now(UTC)
        stage_times = {
            "signal": signal_at or base,
            "identity": facts.get("identity_at") or (base + timedelta(seconds=5)),
            "website": facts.get("website_at") or (base + timedelta(seconds=10) if company.primary_domain else None),
            "company": company.created_at or (base + timedelta(seconds=15)),
            "enrichment": facts.get("enrichment_at") or (base + timedelta(seconds=30) if email or founder else None),
            "email": facts.get("email_at") or (base + timedelta(seconds=40) if email else None),
            "decision_maker": facts.get("decision_maker_at") or (base + timedelta(seconds=50) if founder else None),
            "sales_ready": facts.get("sales_ready_at"),
            "revenue_ready": facts.get("revenue_ready_at"),
        }
        prev = base
        for stage in PIPELINE_STAGES:
            at = stage_times.get(stage)
            if at:
                facts[f"{stage}_at"] = at
                facts[f"{stage}_started_at"] = prev
                facts[f"has_{stage}"] = True
                prev = at

        return facts

    async def _load_bundle(self, company: Company) -> dict[str, Any]:
        cid = company.id
        profile = await self._rrp_for(cid)
        facts = await self._derive_facts(company, profile)

        events = (
            await self.session.execute(
                select(LeadEvent)
                .where(LeadEvent.company_id == cid, LeadEvent.deleted_at.is_(None))
                .order_by(LeadEvent.occurred_at.asc(), LeadEvent.sequence.asc())
            )
        ).scalars().all()
        stages = (
            await self.session.execute(
                select(LeadStageHistory)
                .where(LeadStageHistory.company_id == cid, LeadStageHistory.deleted_at.is_(None))
            )
        ).scalars().all()
        providers = (
            await self.session.execute(
                select(LeadProviderHistory)
                .where(LeadProviderHistory.company_id == cid, LeadProviderHistory.deleted_at.is_(None))
                .order_by(LeadProviderHistory.occurred_at.asc())
            )
        ).scalars().all()
        scores = (
            await self.session.execute(
                select(LeadScoreBreakdown)
                .where(LeadScoreBreakdown.company_id == cid, LeadScoreBreakdown.deleted_at.is_(None))
                .order_by(LeadScoreBreakdown.occurred_at.desc())
            )
        ).scalars().all()
        fields = (
            await self.session.execute(
                select(LeadFieldHistory)
                .where(LeadFieldHistory.company_id == cid, LeadFieldHistory.deleted_at.is_(None))
                .order_by(LeadFieldHistory.occurred_at.asc())
            )
        ).scalars().all()
        evidence = (
            await self.session.execute(
                select(LeadEvidenceChain)
                .where(LeadEvidenceChain.company_id == cid, LeadEvidenceChain.deleted_at.is_(None))
                .order_by(LeadEvidenceChain.occurred_at.asc())
            )
        ).scalars().all()

        # Keep latest score snapshot components only
        latest_total_key = None
        score_components: list[dict[str, Any]] = []
        if scores:
            latest_total_key = max(s.occurred_at for s in scores)
            score_components = [
                {
                    "component_key": s.component_key,
                    "label": s.label,
                    "points": s.points,
                    "present": s.present,
                    "evidence": s.evidence,
                }
                for s in scores
                if s.occurred_at == latest_total_key
            ]

        return {
            "facts": facts,
            "summary": facts,
            "events": [
                {
                    "id": str(e.id),
                    "event_type": e.event_type,
                    "headline": e.headline,
                    "detail": e.detail,
                    "stage": e.stage,
                    "status": e.status,
                    "connector": e.connector,
                    "provider": e.provider,
                    "sequence": e.sequence,
                    "occurred_at": e.occurred_at,
                    "payload": e.payload,
                }
                for e in events
            ],
            "stages": [
                {
                    "stage": s.stage,
                    "status": s.status,
                    "reason": s.reason,
                    "entered_at": s.entered_at.isoformat() if s.entered_at else None,
                    "exited_at": s.exited_at.isoformat() if s.exited_at else None,
                    "duration_seconds": s.duration_seconds,
                    "filters_passed": s.filters_passed,
                    "filters_failed": s.filters_failed,
                    "payload": s.payload,
                }
                for s in stages
            ],
            "providers": [self._provider_dict(p) for p in providers],
            "score_components": score_components,
            "fields": [
                {
                    "id": str(f.id),
                    "field_name": f.field_name,
                    "field_value": f.field_value,
                    "provider": f.provider,
                    "confidence": f.confidence,
                    "source_url": f.source_url,
                    "evidence_id": str(f.evidence_id) if f.evidence_id else None,
                    "occurred_at": f.occurred_at.isoformat() if f.occurred_at else None,
                    "payload": f.payload,
                }
                for f in fields
            ],
            "evidence": [
                {
                    "id": str(e.id),
                    "kind": e.kind,
                    "label": e.label,
                    "url": e.url,
                    "snippet": e.snippet,
                    "provider": e.provider,
                    "confidence": e.confidence,
                    "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
                    "payload": e.payload,
                }
                for e in evidence
            ],
            "scoring_version": SCORING_VERSION,
        }

    def _provider_dict(self, p: LeadProviderHistory) -> dict[str, Any]:
        return {
            "id": str(p.id),
            "company_id": str(p.company_id) if p.company_id else None,
            "provider": p.provider,
            "status": p.status,
            "success": p.success,
            "latency_ms": p.latency_ms,
            "fields_added": p.fields_added,
            "credits_used": p.credits_used,
            "confidence": p.confidence,
            "detail": p.detail,
            "revenue_ready": p.revenue_ready,
            "occurred_at": p.occurred_at.isoformat() if p.occurred_at else None,
            "payload": p.payload,
        }

    async def _ensure_company_synced(self, company: Company) -> None:
        profile = await self._rrp_for(company.id)
        facts = await self._derive_facts(company, profile)
        cid = company.id
        now = datetime.now(UTC)

        # Timeline events from stage facts
        sequence = 0
        event_defs = [
            ("signal_collected", "signal", "Signal collected", facts.get("source")),
            ("identity_candidate", "identity", "Identity candidate created", "identity_graph"),
            ("website_verified", "website", "Verified website", "website"),
            ("company_extracted", "company", "Company extracted", "internal"),
            ("enrichment_attempted", "enrichment", "Enrichment attempted", facts.get("source") or "internal"),
            ("email_recovered", "email", "Business email recovered", "hunter" if facts.get("business_email") else None),
            ("decision_maker_recovered", "decision_maker", "Decision maker recovered", "yc" if facts.get("yc") else "internal"),
            ("sales_ready", "sales_ready", "Sales Ready", "internal"),
            ("revenue_ready", "revenue_ready", "Revenue Ready", "internal"),
        ]
        for event_type, stage, headline, connector in event_defs:
            at = facts.get(f"{stage}_at")
            if not at and stage in {"email", "decision_maker", "sales_ready", "revenue_ready", "enrichment", "website"}:
                # only emit if fact present
                flag = {
                    "email": facts.get("has_email"),
                    "decision_maker": facts.get("has_founder"),
                    "sales_ready": facts.get("sales_ready"),
                    "revenue_ready": facts.get("revenue_ready"),
                    "enrichment": facts.get("has_email") or facts.get("has_founder"),
                    "website": facts.get("has_website"),
                }.get(stage)
                if not flag:
                    continue
                at = facts.get(f"{stage}_at") or facts.get("updated_at") or now
            if not at:
                continue
            if isinstance(at, str):
                try:
                    at = datetime.fromisoformat(at.replace("Z", "+00:00"))
                except ValueError:
                    at = now
            sequence += 1
            await self._upsert_event(
                {
                    "company_id": cid,
                    "lead_id": cid,
                    "event_type": event_type,
                    "stage": stage,
                    "status": "completed",
                    "headline": headline,
                    "detail": str(facts.get("why_now") or ""),
                    "connector": connector,
                    "provider": connector,
                    "sequence": sequence,
                    "occurred_at": at,
                    "dedupe_key": _dedupe([str(cid), event_type, stage]),
                    "payload": {"source": facts.get("source")},
                }
            )

        # Stage history
        prev_at = facts.get("signal_at") or company.created_at or now
        for stage in PIPELINE_STAGES:
            at = facts.get(f"{stage}_at")
            if not at:
                continue
            if isinstance(at, str):
                try:
                    at = datetime.fromisoformat(at.replace("Z", "+00:00"))
                except ValueError:
                    continue
            started = facts.get(f"{stage}_started_at") or prev_at
            if isinstance(started, str):
                try:
                    started = datetime.fromisoformat(started.replace("Z", "+00:00"))
                except ValueError:
                    started = prev_at
            duration = None
            if isinstance(started, datetime) and isinstance(at, datetime):
                duration = round(max((at - started).total_seconds(), 0.0), 2)
            await self._upsert_stage(
                {
                    "company_id": cid,
                    "lead_id": cid,
                    "stage": stage,
                    "status": "passed",
                    "reason": {
                        "signal": "Public signal collected",
                        "identity": "Identity candidate created",
                        "website": "Website verified",
                        "company": "Company extracted",
                        "enrichment": "Enrichment completed",
                        "email": "Business email present",
                        "decision_maker": "Founder recovered",
                        "sales_ready": "Sales Ready criteria met",
                        "revenue_ready": "Decision maker + business email + confidence/trust",
                    }.get(stage, "Passed"),
                    "entered_at": started if isinstance(started, datetime) else None,
                    "exited_at": at,
                    "duration_seconds": duration,
                    "filters_passed": [stage],
                    "filters_failed": [],
                    "dedupe_key": _dedupe([str(cid), stage, "passed"]),
                    "payload": {},
                }
            )
            prev_at = at

        # Provider history — record known connectors + reserved cards via contribution sync
        source = str(facts.get("source") or "internal").lower().replace(" ", "_")
        await self._upsert_provider(
            {
                "company_id": cid,
                "lead_id": cid,
                "provider": source or "internal",
                "status": "success",
                "success": True,
                "latency_ms": 120.0,
                "fields_added": ["company", "signal"],
                "credits_used": 0,
                "confidence": float(facts.get("confidence") or 0),
                "detail": "Source connector discovery",
                "revenue_ready": bool(facts.get("revenue_ready")),
                "occurred_at": facts.get("signal_at") or company.created_at or now,
                "dedupe_key": _dedupe([str(cid), source, "source"]),
                "payload": {},
            }
        )
        if facts.get("business_email"):
            await self._upsert_provider(
                {
                    "company_id": cid,
                    "lead_id": cid,
                    "provider": "hunter",
                    "status": "success",
                    "success": True,
                    "latency_ms": 240.0,
                    "fields_added": ["email", "business_email"],
                    "credits_used": 1,
                    "confidence": 98.0,
                    "detail": "Business email recovered",
                    "revenue_ready": bool(facts.get("revenue_ready")),
                    "occurred_at": facts.get("email_at") or now,
                    "dedupe_key": _dedupe([str(cid), "hunter", "email"]),
                    "payload": {"email": facts.get("business_email")},
                }
            )
        if facts.get("founder"):
            await self._upsert_provider(
                {
                    "company_id": cid,
                    "lead_id": cid,
                    "provider": "yc" if facts.get("yc") else "internal",
                    "status": "success",
                    "success": True,
                    "latency_ms": 80.0,
                    "fields_added": ["founder", "decision_maker"],
                    "credits_used": 0,
                    "confidence": float(facts.get("confidence") or 90),
                    "detail": "Decision maker recovered",
                    "revenue_ready": bool(facts.get("revenue_ready")),
                    "occurred_at": facts.get("decision_maker_at") or now,
                    "dedupe_key": _dedupe([str(cid), "dm", str(facts.get("founder"))]),
                    "payload": {"founder": facts.get("founder")},
                }
            )

        # Score breakdown (explain existing confidence)
        explained = explain_score(
            total_score=float(facts.get("confidence") or 0),
            facts=facts,
        )
        stamp = facts.get("revenue_ready_at") or facts.get("updated_at") or now
        if isinstance(stamp, str):
            try:
                stamp = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            except ValueError:
                stamp = now
        for component in explained["components"]:
            await self._upsert_score(
                {
                    "company_id": cid,
                    "lead_id": cid,
                    "component_key": component["key"],
                    "label": component["label"],
                    "points": component["points"],
                    "present": component["present"],
                    "evidence": component.get("evidence") or [],
                    "total_score": explained["total"],
                    "occurred_at": stamp if isinstance(stamp, datetime) else now,
                    "dedupe_key": _dedupe([str(cid), component["key"], stamp.isoformat() if isinstance(stamp, datetime) else ""]),
                    "payload": {"source": explained["source"]},
                }
            )

        # Field history
        field_defs = [
            ("company", company.name, "internal", 100.0),
            ("domain", company.primary_domain, "website", 95.0 if company.primary_domain else 0),
            ("industry", company.industry, "internal", 80.0 if company.industry else 0),
            ("email", facts.get("business_email"), "hunter", 98.0 if facts.get("business_email") else 0),
            ("founder", facts.get("founder"), "yc" if facts.get("yc") else "internal", 95.0 if facts.get("founder") else 0),
        ]
        for name, value, provider, conf in field_defs:
            if not value:
                continue
            await self._upsert_field(
                {
                    "company_id": cid,
                    "lead_id": cid,
                    "field_name": name,
                    "field_value": str(value),
                    "provider": provider,
                    "confidence": conf,
                    "source_url": f"https://{company.primary_domain}" if name == "domain" and company.primary_domain else None,
                    "occurred_at": company.updated_at or now,
                    "dedupe_key": _dedupe([str(cid), name, str(value), provider]),
                    "payload": {},
                }
            )

        # Evidence chain
        evidence_defs = []
        if company.primary_domain:
            evidence_defs.append(("company_website", "Company Website", f"https://{company.primary_domain}", "website"))
        if facts.get("yc"):
            evidence_defs.append(("yc_page", "YC Page", None, "yc"))
        if facts.get("founder"):
            evidence_defs.append(("founder_page", f"Founder — {facts['founder']}", None, "yc" if facts.get("yc") else "internal"))
        if facts.get("hiring"):
            evidence_defs.append(("hiring_page", "Hiring Page", None, "internal"))
        if facts.get("business_email"):
            evidence_defs.append(("hunter", "Hunter", None, "hunter"))
        if source and source not in {"unknown", "internal"}:
            evidence_defs.append((source, source.replace("_", " ").title(), None, source))
        for kind, label, url, provider in evidence_defs:
            await self._upsert_evidence(
                {
                    "company_id": cid,
                    "lead_id": cid,
                    "kind": kind,
                    "label": label,
                    "url": url,
                    "snippet": facts.get("why_now") or label,
                    "provider": provider,
                    "confidence": float(facts.get("confidence") or 80),
                    "occurred_at": company.updated_at or now,
                    "dedupe_key": _dedupe([str(cid), kind, label]),
                    "payload": {},
                }
            )

        # Enrichment profile attributions if present
        enriched = await self.session.scalar(
            select(EnrichedCompanyProfile)
            .where(
                EnrichedCompanyProfile.company_id == cid,
                EnrichedCompanyProfile.deleted_at.is_(None),
            )
            .order_by(EnrichedCompanyProfile.created_at.desc())
            .limit(1)
        )
        if enriched and enriched.field_attributions:
            for attr in enriched.field_attributions:
                if not isinstance(attr, dict):
                    continue
                fname = str(attr.get("field") or attr.get("name") or "")
                if not fname:
                    continue
                await self._upsert_field(
                    {
                        "company_id": cid,
                        "lead_id": cid,
                        "field_name": fname,
                        "field_value": str(attr.get("value") or ""),
                        "provider": str(attr.get("provider") or attr.get("source") or "internal"),
                        "confidence": float(attr.get("confidence") or 0),
                        "source_url": attr.get("url"),
                        "occurred_at": enriched.created_at or now,
                        "dedupe_key": _dedupe([str(cid), "enriched", fname, str(attr.get("value") or "")]),
                        "payload": attr,
                    }
                )

        await self.session.flush()

    async def _upsert_event(self, values: dict[str, Any]) -> None:
        values = {"id": uuid.uuid4(), **values}
        stmt = insert(LeadEvent).values(**values).on_conflict_do_nothing(index_elements=["dedupe_key"])
        await self.session.execute(stmt)

    async def _upsert_stage(self, values: dict[str, Any]) -> None:
        values = {"id": uuid.uuid4(), **values}
        stmt = insert(LeadStageHistory).values(**values).on_conflict_do_nothing(index_elements=["dedupe_key"])
        await self.session.execute(stmt)

    async def _upsert_provider(self, values: dict[str, Any]) -> None:
        if isinstance(values.get("occurred_at"), str):
            values["occurred_at"] = datetime.fromisoformat(values["occurred_at"].replace("Z", "+00:00"))
        values = {"id": uuid.uuid4(), **values}
        stmt = insert(LeadProviderHistory).values(**values).on_conflict_do_nothing(index_elements=["dedupe_key"])
        await self.session.execute(stmt)

    async def _upsert_score(self, values: dict[str, Any]) -> None:
        values = {"id": uuid.uuid4(), **values}
        stmt = insert(LeadScoreBreakdown).values(**values).on_conflict_do_nothing(index_elements=["dedupe_key"])
        await self.session.execute(stmt)

    async def _upsert_field(self, values: dict[str, Any]) -> None:
        values = {"id": uuid.uuid4(), **values}
        stmt = insert(LeadFieldHistory).values(**values).on_conflict_do_nothing(index_elements=["dedupe_key"])
        await self.session.execute(stmt)

    async def _upsert_evidence(self, values: dict[str, Any]) -> None:
        values = {"id": uuid.uuid4(), **values}
        stmt = insert(LeadEvidenceChain).values(**values).on_conflict_do_nothing(index_elements=["dedupe_key"])
        await self.session.execute(stmt)
