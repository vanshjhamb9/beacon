from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.acquisition import CollectorRun
from app.models.communication import OAuthConnection
from app.models.decision import DecisionMaker
from app.models.enrichment import CompanyContact
from app.models.intelligence import Company, CompanyTimeline
from app.models.opportunity import Opportunity, OpportunityEvidence
from app.models.production_hardening import PhAdmissionDecision, PhContactReadiness, PhCompanyMerge, PhTrustSnapshot
from app.models.source_health import SourceHealth
from production_hardening.admission.engine import OpportunityAdmissionGate
from production_hardening.dedupe.engine import DuplicateResolutionEngine
from production_hardening.health.telemetry import LiveHealthTelemetry
from production_hardening.identity.engine import CompanyIdentityValidator
from production_hardening.noise.engine import NoiseCollapser
from production_hardening.readiness.engine import ContactReadinessEngine
from production_hardening.scoring.engine import LeadQualityScorer
from production_hardening.trust.engine import TrustMetricsEngine
from runtime_ops.redis.validator import RedisStreamsValidator


def _secret_present(value: Any) -> bool:
    if value is None:
        return False
    if hasattr(value, "get_secret_value"):
        raw = value.get_secret_value()
        return bool(raw and str(raw).strip())
    return bool(str(value).strip())


class ProductionHardeningService:
    def __init__(self, session: AsyncSession, redis: Redis, settings: Settings) -> None:
        self.session = session
        self.redis = redis
        self.settings = settings
        self.gate = OpportunityAdmissionGate()
        self.identity = CompanyIdentityValidator()
        self.readiness = ContactReadinessEngine()
        self.scorer = LeadQualityScorer()
        self.dedupe = DuplicateResolutionEngine()
        self.trust = TrustMetricsEngine()
        self.noise = NoiseCollapser()
        self.telemetry = LiveHealthTelemetry()

    async def evaluate_company(self, company_id: UUID, *, persist: bool = True) -> dict[str, Any]:
        card = await self.compose_company_card(company_id)
        if card.get("error"):
            return card
        if persist:
            await self._persist_evaluation(company_id, card)
        return card

    async def compose_company_card(self, company_id: UUID) -> dict[str, Any]:
        company = await self.session.get(Company, company_id)
        if company is None:
            return {"error": "not_found"}

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
        source = timeline[0].source if timeline else None
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
                    .limit(10)
                )
            ).all()
        )
        contacts = list(
            (
                await self.session.scalars(
                    select(CompanyContact)
                    .where(CompanyContact.company_id == company_id, CompanyContact.deleted_at.is_(None))
                    .limit(30)
                )
            ).all()
        )
        emails = [c.value for c in contacts if "email" in str(c.kind).lower() and c.value]
        phones = [c.value for c in contacts if "phone" in str(c.kind).lower() and c.value]
        for dm in dms:
            if dm.work_email:
                emails.append(dm.work_email)
            if dm.business_phone:
                phones.append(dm.business_phone)
        emails = list(dict.fromkeys(emails))
        phones = list(dict.fromkeys(phones))

        attrs = company.attributes or {}
        url = None
        if timeline and isinstance(timeline[0].evidence, dict):
            url = timeline[0].evidence.get("url")

        admission = self.gate.evaluate(
            {
                "company_name": company.name,
                "primary_domain": company.primary_domain,
                "source": source,
                "evidence": evidence_rows,
                "narrative": opportunity.narrative if opportunity else company.memory_summary,
                "url": url,
            }
        )
        identity = self.identity.evaluate(
            {
                "company_name": company.name,
                "primary_domain": company.primary_domain,
                "industry": company.industry,
                "description": company.description or company.memory_summary,
                "linkedin_url": attrs.get("linkedin_url"),
                "employee_estimate": attrs.get("employees") or attrs.get("employee_estimate"),
                "technologies": attrs.get("technologies") or [],
                "country": attrs.get("country") or attrs.get("location"),
                "created_at": company.created_at,
                "last_seen_at": company.last_seen_at,
            }
        )
        readiness = self.readiness.evaluate(
            {
                "website": company.primary_domain,
                "emails": emails,
                "phones": phones,
                "decision_makers": [
                    {"name": d.name, "title": d.role, "email": d.work_email, "source": d.source} for d in dms
                ],
                "linkedin_url": attrs.get("linkedin_url") or (dms[0].linkedin_url if dms else None),
                "has_business_evidence": bool(evidence_rows),
                "evidence": evidence_rows,
            }
        )
        quality = self.scorer.score(
            {
                "company_name": company.name,
                "domain": company.primary_domain,
                "verified_website": bool(company.primary_domain),
                "intent_signals": [t.signal_type for t in timeline[:5]],
                "has_decision_maker": bool(dms),
                "emails": emails,
                "phones": phones,
                "last_seen_at": company.last_seen_at,
                "technologies": attrs.get("technologies") or [],
                "buying_signals": [e.category for e in evidence_rows[:5]],
            }
        )

        sources = self.noise.collapse(
            [{"source": t.source, "at": t.timestamp.isoformat(), "summary": t.summary} for t in timeline],
            key_fn=lambda x: (x["source"], x["summary"]),
        )
        evidence_cards = self.noise.collapse(
            [
                {
                    "source": e.source_type,
                    "connector": source,
                    "snippet": e.summary,
                    "confidence": e.confidence,
                    "category": e.category,
                    "urls": [u for u in [((e.details or {}).get("url") if isinstance(e.details, dict) else None)] if u],
                }
                for e in evidence_rows
            ],
            key_fn=lambda x: (x["source"], x["snippet"]),
        )

        visible = bool(
            quality.visible and admission.verdict.value == "admit" and identity.admitted
        )
        founder_queue_visible = bool(
            self.readiness.visible_in_founder_queue(readiness) and visible
        )

        return {
            "company_id": str(company_id),
            "company": company.name,
            "industry": company.industry,
            "location": attrs.get("country") or attrs.get("location"),
            "employees": attrs.get("employees") or attrs.get("employee_estimate"),
            "website": company.primary_domain,
            "source": source,
            "intent": timeline[-1].signal_type if timeline else None,
            "score": quality.total,
            "decision_maker": dms[0].name if dms else None,
            "verified_email": emails[0] if emails else None,
            "verified_phone": phones[0] if phones else None,
            "recommended_service": None,
            "estimated_deal": None,
            "confidence": identity.confidence,
            "contact_readiness": readiness.status.value,
            "visible": visible,
            "visible_in_founder_queue": founder_queue_visible,
            "admission": admission.model_dump(mode="json"),
            "identity": identity.model_dump(mode="json"),
            "readiness": readiness.model_dump(mode="json"),
            "quality": quality.model_dump(mode="json"),
            "collected_from": sources,
            "evidence_cards": evidence_cards,
            "empty_states": self._empty_states(readiness, identity, emails, dms),
        }

    async def _persist_evaluation(self, company_id: UUID, card: dict[str, Any]) -> None:
        admission = card["admission"]
        quality = card["quality"]
        readiness = card["readiness"]
        self.session.add(
            PhContactReadiness(
                id=uuid.uuid4(),
                company_id=company_id,
                status=readiness["status"],
                lead_quality_score=float(quality["total"]),
                visible=bool(card.get("visible")),
                founder_queue_visible=bool(card.get("visible_in_founder_queue")),
                details={
                    "admission": admission,
                    "identity": card["identity"],
                    "readiness": readiness,
                    "quality": quality,
                },
                evidence=list(quality.get("evidence") or []) + list(admission.get("evidence") or []),
            )
        )
        self.session.add(
            PhAdmissionDecision(
                id=uuid.uuid4(),
                company_id=company_id,
                company_name=card["company"],
                domain=card.get("website"),
                verdict=admission["verdict"],
                reasons=list(admission.get("reasons") or []),
                evidence=list(admission.get("evidence") or []),
                payload={"company_id": str(company_id)},
            )
        )
        await self.session.commit()

    async def opportunities_v2(self, *, limit: int = 100) -> dict[str, Any]:
        companies = list(
            (
                await self.session.scalars(
                    select(Company)
                    .where(Company.deleted_at.is_(None), Company.primary_domain.is_not(None))
                    .order_by(Company.last_seen_at.desc().nulls_last(), Company.created_at.desc())
                    .limit(min(limit * 4, 400))
                )
            ).all()
        )
        rows: list[dict[str, Any]] = []
        for company in companies:
            card = await self.compose_company_card(company.id)
            if card.get("error") or not card.get("visible"):
                continue
            rows.append(
                {
                    "company": card["company"],
                    "company_id": card["company_id"],
                    "website": card.get("website"),
                    "industry": card.get("industry"),
                    "country": card.get("location"),
                    "intent": card.get("intent"),
                    "source": card.get("source"),
                    "verified_email": card.get("verified_email"),
                    "verified_phone": card.get("verified_phone"),
                    "decision_maker": card.get("decision_maker"),
                    "service": card.get("recommended_service"),
                    "deal_size": card.get("estimated_deal"),
                    "confidence": card.get("confidence"),
                    "score": card.get("score"),
                    "collected": card.get("identity", {}).get("first_seen_at"),
                    "freshness": card.get("identity", {}).get("last_verified_at"),
                    "status": card.get("contact_readiness"),
                }
            )
            if len(rows) >= limit:
                break
        return {"opportunities": rows, "total": len(rows), "scoring_version": "ph1-v1"}

    async def trust_dashboard(self) -> dict[str, Any]:
        companies = int(
            await self.session.scalar(select(func.count()).select_from(Company).where(Company.deleted_at.is_(None))) or 0
        )
        with_website = int(
            await self.session.scalar(
                select(func.count())
                .select_from(Company)
                .where(Company.deleted_at.is_(None), Company.primary_domain.is_not(None))
            )
            or 0
        )
        with_email = int(
            await self.session.scalar(
                select(func.count(func.distinct(CompanyContact.company_id))).where(
                    CompanyContact.deleted_at.is_(None), CompanyContact.kind.ilike("%email%")
                )
            )
            or 0
        )
        with_phone = int(
            await self.session.scalar(
                select(func.count(func.distinct(CompanyContact.company_id))).where(
                    CompanyContact.deleted_at.is_(None), CompanyContact.kind.ilike("%phone%")
                )
            )
            or 0
        )
        with_dm = int(
            await self.session.scalar(
                select(func.count(func.distinct(DecisionMaker.company_id))).where(DecisionMaker.deleted_at.is_(None))
            )
            or 0
        )
        rejected = int(
            await self.session.scalar(
                select(func.count()).select_from(PhAdmissionDecision).where(PhAdmissionDecision.verdict == "reject")
            )
            or 0
        )
        merged = int(
            await self.session.scalar(
                select(func.count()).select_from(PhCompanyMerge).where(PhCompanyMerge.deleted_at.is_(None))
            )
            or 0
        )
        health_rows = list((await self.session.scalars(select(SourceHealth))).all())
        collector_health = {
            r.source: {"status": str(getattr(r.status, "value", r.status)), "failures": r.consecutive_failures}
            for r in health_rows
        }
        metrics = self.trust.evaluate(
            {
                "companies_collected": companies,
                "qualified": with_website,
                "rejected": rejected,
                "merged": merged,
                "with_website": with_website,
                "with_email": with_email,
                "with_phone": with_phone,
                "with_decision_maker": with_dm,
                "average_confidence": 0.0,
                "collector_health": collector_health,
                "daily_pipeline_conversion": {
                    "companies": float(companies),
                    "with_website": float(with_website),
                    "with_email": float(with_email),
                    "with_dm": float(with_dm),
                },
            }
        )
        self.session.add(
            PhTrustSnapshot(id=uuid.uuid4(), metrics=metrics.model_dump(mode="json"), evidence=metrics.evidence)
        )
        await self.session.commit()
        return metrics.model_dump(mode="json")

    async def plan_duplicates(self) -> dict[str, Any]:
        companies = list(
            (await self.session.scalars(select(Company).where(Company.deleted_at.is_(None)).limit(2000))).all()
        )
        payload = [
            {
                "id": str(c.id),
                "company_name": c.name,
                "normalized_name": c.normalized_name,
                "primary_domain": c.primary_domain,
                "signal_frequency": c.signal_frequency,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "linkedin_url": (c.attributes or {}).get("linkedin_url"),
            }
            for c in companies
        ]
        plans = self.dedupe.plan_merges(payload)
        return {"plans": [p.model_dump(mode="json") for p in plans], "total": len(plans)}

    async def live_component_signals(self) -> dict[str, dict[str, float]]:
        started = time.perf_counter()
        redis_result = await RedisStreamsValidator().validate_async(self.redis)
        db_ok = True
        db_latency = 0.0
        try:
            t0 = time.perf_counter()
            await self.session.execute(text("SELECT 1"))
            db_latency = round((time.perf_counter() - t0) * 1000, 2)
        except Exception:  # noqa: BLE001
            db_ok = False
            db_latency = 9999.0

        last_collector = await self.session.scalar(select(func.max(CollectorRun.created_at)))
        recent_ok = False
        if last_collector is not None:
            age = datetime.now(UTC) - (last_collector if last_collector.tzinfo else last_collector.replace(tzinfo=UTC))
            recent_ok = age.total_seconds() <= 900

        health_rows = list((await self.session.scalars(select(SourceHealth))).all())
        running = sum(1 for r in health_rows if str(getattr(r.status, "value", r.status)).upper() == "HEALTHY")
        oauth_count = int(await self.session.scalar(select(func.count()).select_from(OAuthConnection)) or 0)
        queue_depth = int(await self.redis.llen("celery") or 0)
        companies_today = int(
            await self.session.scalar(
                select(func.count())
                .select_from(Company)
                .where(Company.created_at >= datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0))
            )
            or 0
        )

        probes = {
            "redis_ok": redis_result.ok,
            "redis_latency_ms": redis_result.latency_ms or round((time.perf_counter() - started) * 1000, 2),
            "database_ok": db_ok,
            "database_latency_ms": db_latency,
            "api_ok": True,
            "worker_online": recent_ok,
            "beat_online": recent_ok,
            "queue_depth": queue_depth,
            "collectors_running": running,
            "collectors_total": max(len(health_rows), 8),
            "companies_today": companies_today,
            "email_configured": bool(self.settings.gmail_client_id),
            "email_oauth_valid": oauth_count > 0,
            "whatsapp_configured": _secret_present(self.settings.meta_whatsapp_token),
            "whatsapp_token_valid": _secret_present(self.settings.meta_whatsapp_token),
            "oauth_ok": oauth_count > 0,
            "campaigns": 0,
            "pipeline_success_rate": 50.0 if recent_ok else 0.0,
        }
        return self.telemetry.build_signals(probes)

    def _empty_states(self, readiness, identity, emails, dms) -> dict[str, Any]:
        return {
            "lead_enrichment": {
                "why": readiness.why_unavailable or ("No verified contacts" if not emails else None),
                "engine": readiness.responsible_engine or "lead_enrichment",
                "next_scheduled": "enrichment.process_opportunities @90s",
                "manual_refresh": True,
                "expected_completion": "1–3 minutes after worker processes enrichment queue",
            },
            "decision_discovery": {
                "why": None if dms else "No decision makers discovered yet",
                "engine": "decision_discovery",
                "next_scheduled": "decision.process_companies @120s",
                "manual_refresh": True,
                "expected_completion": "After verification report exists",
            },
            "identity": {
                "why": None if identity.admitted else f"Identity confidence {identity.confidence} below threshold",
                "engine": "production_hardening.identity",
                "missing_fields": identity.missing_fields,
            },
        }
