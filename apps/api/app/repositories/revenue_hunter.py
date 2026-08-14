from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.context import BusinessGoal, BusinessPain, CompanyProfile
from app.models.decision import CompanyContactChannel, DecisionMaker
from app.models.enrichment import CompanyJob, CompanyTechnology, EnrichmentReport
from app.models.intelligence import Company
from app.models.opportunity import Opportunity
from app.models.revenue_hunter import (
    RevenueHunterDailyBrief,
    RevenueHunterDossier,
    RevenueHunterWorkQueueItem,
)
from app.models.sales_readiness import SalesReadinessSnapshotRow
from app.models.verification import VerificationReport
from revenue_hunter.filters.taxonomy import size_band_from_employees
from revenue_hunter.models.types import (
    FounderDashboard,
    RevenueDossier,
    RevenueHunterDecision,
    RevenueHunterInput,
    WorkQueueAction,
    WorkQueueItem,
    WorkQueueStatus,
)
from revenue_hunter.queue.work_queue import WorkQueueBuilder

SRE_REVENUE_HUNTER_STATUSES = frozenset({"SALES READY", "ENTERPRISE READY"})


class RevenueHunterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.queue_builder = WorkQueueBuilder()

    async def pending_inputs(self, *, limit: int) -> list[RevenueHunterInput]:
        """Only consume companies classified SALES READY / ENTERPRISE READY by SRE."""
        latest_sre = (
            select(
                SalesReadinessSnapshotRow.company_id,
                func.max(SalesReadinessSnapshotRow.created_at).label("created_at"),
            )
            .where(
                SalesReadinessSnapshotRow.deleted_at.is_(None),
                SalesReadinessSnapshotRow.eligible_for_revenue_hunter.is_(True),
                SalesReadinessSnapshotRow.status.in_(tuple(SRE_REVENUE_HUNTER_STATUSES)),
            )
            .group_by(SalesReadinessSnapshotRow.company_id)
            .subquery()
        )
        latest = (
            select(RevenueHunterDossier.company_id, func.max(RevenueHunterDossier.created_at).label("created_at"))
            .group_by(RevenueHunterDossier.company_id)
            .subquery()
        )
        result = await self.session.execute(
            select(Opportunity)
            .join(latest_sre, latest_sre.c.company_id == Opportunity.company_id)
            .outerjoin(latest, latest.c.company_id == Opportunity.company_id)
            .where(
                or_(
                    latest.c.created_at.is_(None),
                    Opportunity.updated_at > latest.c.created_at,
                )
            )
            .order_by(Opportunity.opportunity_score.desc(), Opportunity.created_at.desc())
            .limit(limit)
        )
        inputs: list[RevenueHunterInput] = []
        for opportunity in result.scalars().all():
            item = await self.build_input(opportunity.company_id, opportunity_id=opportunity.id)
            if item is not None:
                inputs.append(item)
        return inputs

    async def build_input(self, company_id: UUID, *, opportunity_id: UUID | None = None) -> RevenueHunterInput | None:
        company = await self.session.get(Company, company_id)
        if company is None:
            return None
        opportunity = None
        if opportunity_id is not None:
            opportunity = await self.session.get(Opportunity, opportunity_id)
        if opportunity is None:
            opportunity = await self.session.scalar(
                select(Opportunity)
                .where(Opportunity.company_id == company_id)
                .order_by(Opportunity.opportunity_score.desc())
                .limit(1)
            )
        profile = await self.session.scalar(
            select(CompanyProfile)
            .where(CompanyProfile.company_id == company_id)
            .order_by(CompanyProfile.created_at.desc())
            .limit(1)
        )
        pains = (
            await self.session.execute(select(BusinessPain).where(BusinessPain.company_id == company_id).limit(30))
        ).scalars().all()
        goals = (
            await self.session.execute(select(BusinessGoal).where(BusinessGoal.company_id == company_id).limit(30))
        ).scalars().all()
        techs = (
            await self.session.execute(
                select(CompanyTechnology).where(CompanyTechnology.company_id == company_id).limit(50)
            )
        ).scalars().all()
        jobs = (
            await self.session.execute(select(CompanyJob).where(CompanyJob.company_id == company_id).limit(50))
        ).scalars().all()
        makers = (
            await self.session.execute(
                select(DecisionMaker).where(DecisionMaker.company_id == company_id).limit(20)
            )
        ).scalars().all()
        channels = (
            await self.session.execute(
                select(CompanyContactChannel).where(CompanyContactChannel.company_id == company_id).limit(30)
            )
        ).scalars().all()
        verification = None
        enrichment = None
        if opportunity is not None:
            verification = await self.session.scalar(
                select(VerificationReport)
                .where(VerificationReport.opportunity_id == opportunity.id)
                .order_by(VerificationReport.created_at.desc())
                .limit(1)
            )
            enrichment = await self.session.scalar(
                select(EnrichmentReport)
                .where(EnrichmentReport.opportunity_id == opportunity.id)
                .order_by(EnrichmentReport.created_at.desc())
                .limit(1)
            )

        attrs = dict(company.attributes or {})
        profile_attrs: dict[str, Any] = {}
        if profile is not None:
            profile_attrs = dict(getattr(profile, "attributes", None) or {})
            if hasattr(profile, "industry") and profile.industry:
                attrs.setdefault("industry", profile.industry)
            if hasattr(profile, "country") and getattr(profile, "country", None):
                attrs.setdefault("country", profile.country)

        employee_count = attrs.get("employee_count") or attrs.get("employees") or profile_attrs.get("employee_count")
        try:
            employee_count_int = int(employee_count) if employee_count is not None else None
        except (TypeError, ValueError):
            employee_count_int = None

        hiring_roles = [str(j.title or j.role or "") for j in jobs if getattr(j, "title", None) or getattr(j, "role", None)]
        if not hiring_roles:
            hiring_roles = [str(r) for r in (attrs.get("hiring_roles") or [])]

        website_metrics = dict(attrs.get("website_metrics") or profile_attrs.get("website_metrics") or {})
        if enrichment is not None and isinstance(getattr(enrichment, "payload", None), dict):
            website_metrics.update(dict(enrichment.payload.get("website_metrics") or {}))

        decision_makers = []
        for m in makers:
            decision_makers.append(
                {
                    "name": getattr(m, "full_name", None) or getattr(m, "name", None) or "Unknown",
                    "role": getattr(m, "title", None) or getattr(m, "role", None),
                    "email": getattr(m, "email", None),
                    "phone": getattr(m, "phone", None),
                    "linkedin": getattr(m, "linkedin_url", None) or getattr(m, "linkedin", None),
                    "confidence": float(getattr(m, "confidence", 0) or 0),
                }
            )

        contacts = []
        for ch in channels:
            contacts.append(
                {
                    "type": getattr(ch, "channel_type", None) or getattr(ch, "type", None),
                    "value": getattr(ch, "value", None) or getattr(ch, "address", None),
                    "email": getattr(ch, "email", None),
                    "phone": getattr(ch, "phone", None),
                }
            )

        # Compose-only CIR enrichment — consume reconstruction outputs without redesigning RH.
        cir_techs = [str(t) for t in (attrs.get("cir_technologies") or []) if t]
        cir_signals = [str(s) for s in (attrs.get("cir_buying_signals") or []) if s]
        cir_narrative = dict(attrs.get("cir_narrative") or {})
        tech_list = [
            str(t.name or t.technology or "")
            for t in techs
            if getattr(t, "name", None) or getattr(t, "technology", None)
        ] or [str(t) for t in (attrs.get("technologies") or [])]
        for t in cir_techs:
            if t not in tech_list:
                tech_list.append(t)
        signal_list = [str(s) for s in (attrs.get("signals") or [])]
        for s in cir_signals:
            if s not in signal_list:
                signal_list.append(s)
        if cir_narrative.get("what_pain") and cir_narrative["what_pain"] not in {"UNKNOWN", None, ""}:
            pains_list = [str(p.category or p.value or p.description or "") for p in pains] or [
                str(p) for p in (attrs.get("pains") or [])
            ]
            if cir_narrative["what_pain"] not in pains_list:
                pains_list.append(str(cir_narrative["what_pain"]))
        else:
            pains_list = [str(p.category or p.value or p.description or "") for p in pains] or [
                str(p) for p in (attrs.get("pains") or [])
            ]

        return RevenueHunterInput(
            company_id=company_id,
            company_name=company.name or attrs.get("name") or "Unknown",
            opportunity_id=opportunity.id if opportunity else opportunity_id,
            industry=attrs.get("industry") or profile_attrs.get("industry"),
            country=attrs.get("country") or profile_attrs.get("country"),
            domain=attrs.get("domain") or getattr(company, "domain", None) or getattr(company, "primary_domain", None),
            website=attrs.get("official_website") or attrs.get("website") or attrs.get("url"),
            employee_count=employee_count_int,
            company_size_band=attrs.get("company_size_band") or size_band_from_employees(employee_count_int),
            revenue_band=attrs.get("revenue_band") or profile_attrs.get("revenue_band"),
            funding_stage=attrs.get("funding_stage") or profile_attrs.get("funding_stage"),
            funding_amount=float(attrs["funding_amount"]) if attrs.get("funding_amount") is not None else None,
            funding_days_ago=int(attrs["funding_days_ago"]) if attrs.get("funding_days_ago") is not None else None,
            technologies=tech_list,
            hiring_roles=[r for r in hiring_roles if r],
            hiring_count=len(jobs) or int(attrs.get("hiring_count") or 0),
            pains=pains_list,
            goals=[str(g.category or g.value or g.description or "") for g in goals],
            signals=signal_list,
            business_model=attrs.get("business_model") or profile_attrs.get("business_model"),
            growth_signals=[str(s) for s in (attrs.get("growth_signals") or [])],
            decision_makers=decision_makers,
            contacts=contacts,
            channels=[str(getattr(c, "channel_type", None) or getattr(c, "type", None) or "") for c in channels],
            products=[str(p) for p in (attrs.get("products") or [])],
            social_profiles=[str(s) for s in (attrs.get("social_profiles") or [])],
            news=[str(n) for n in (attrs.get("news") or [])],
            website_metrics=website_metrics,
            opportunity_score=float(opportunity.opportunity_score) if opportunity else 0.0,
            verification_score=float(getattr(verification, "overall_score", 0) or 0) if verification else 0.0,
            enrichment=dict(getattr(enrichment, "payload", None) or {}) if enrichment else {},
            metadata={
                "profile": profile_attrs,
                "cir_readiness": attrs.get("cir_readiness_score"),
                "cir_classification": attrs.get("cir_classification"),
                "cir_best_service": attrs.get("cir_best_service"),
                "cir_narrative": cir_narrative,
                "cir_service_match": attrs.get("cir_best_service"),
            },
        )

    async def store_decision(self, decision: RevenueHunterDecision) -> RevenueHunterDossier:
        existing = await self.latest_for_company(decision.company_id)
        payload = self._decision_to_fields(decision)
        if existing is None:
            row = RevenueHunterDossier(**payload)
            self.session.add(row)
        else:
            row = existing
            for key, value in payload.items():
                setattr(row, key, value)
        await self.session.flush()
        if decision.work_queue_eligible:
            await self.upsert_work_queue_from_dossier(decision.dossier, dossier_id=row.id)
        return row

    async def latest_for_company(self, company_id: UUID) -> RevenueHunterDossier | None:
        return await self.session.scalar(
            select(RevenueHunterDossier)
            .where(RevenueHunterDossier.company_id == company_id)
            .order_by(RevenueHunterDossier.created_at.desc())
            .limit(1)
        )

    async def list_dossiers(
        self, *, grade: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[RevenueHunterDossier]:
        stmt = select(RevenueHunterDossier).order_by(RevenueHunterDossier.revenue_score.desc())
        if grade:
            stmt = stmt.where(RevenueHunterDossier.priority_grade == grade)
        stmt = stmt.offset(offset).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_dossier(self, dossier_id: UUID) -> RevenueHunterDossier | None:
        return await self.session.get(RevenueHunterDossier, dossier_id)

    async def campaign_eligible(self, *, limit: int = 100) -> list[RevenueHunterDossier]:
        stmt = (
            select(RevenueHunterDossier)
            .where(RevenueHunterDossier.proceed_to_campaign.is_(True))
            .where(RevenueHunterDossier.priority_grade.in_(["A+", "A"]))
            .order_by(RevenueHunterDossier.revenue_score.desc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def upsert_work_queue_from_dossier(
        self, dossier: RevenueDossier, *, dossier_id: UUID | None
    ) -> RevenueHunterWorkQueueItem | None:
        items = self.queue_builder.build([dossier], limit=1)
        if not items:
            return None
        item = items[0]
        existing = await self.session.scalar(
            select(RevenueHunterWorkQueueItem)
            .where(RevenueHunterWorkQueueItem.company_id == item.company_id)
            .where(RevenueHunterWorkQueueItem.status == WorkQueueStatus.PENDING.value)
            .order_by(RevenueHunterWorkQueueItem.created_at.desc())
            .limit(1)
        )
        fields = {
            "dossier_id": dossier_id,
            "company_id": item.company_id,
            "company_name": item.company_name,
            "priority_grade": item.priority_grade.value,
            "recommended_service": item.recommended_service,
            "why_today": item.why_today,
            "expected_budget": item.expected_budget,
            "probability": item.probability,
            "primary_contact": item.primary_contact.model_dump() if item.primary_contact else {},
            "status": item.status.value,
            "allowed_actions": [a.value for a in item.allowed_actions],
            "rank": item.rank,
        }
        if existing is None:
            row = RevenueHunterWorkQueueItem(**fields, action_log=[])
            self.session.add(row)
        else:
            row = existing
            for key, value in fields.items():
                setattr(row, key, value)
        await self.session.flush()
        return row

    async def list_work_queue(self, *, status: str | None = None, limit: int = 50) -> list[RevenueHunterWorkQueueItem]:
        stmt = select(RevenueHunterWorkQueueItem).order_by(
            RevenueHunterWorkQueueItem.rank.asc(),
            RevenueHunterWorkQueueItem.probability.desc(),
        )
        if status:
            stmt = stmt.where(RevenueHunterWorkQueueItem.status == status)
        else:
            stmt = stmt.where(RevenueHunterWorkQueueItem.status == WorkQueueStatus.PENDING.value)
        return list((await self.session.execute(stmt.limit(limit))).scalars().all())

    async def apply_work_action(
        self, item_id: UUID, *, action: str, actor: str = "founder"
    ) -> RevenueHunterWorkQueueItem | None:
        row = await self.session.get(RevenueHunterWorkQueueItem, item_id)
        if row is None:
            return None
        domain = WorkQueueItem(
            company_id=row.company_id,
            company_name=row.company_name,
            dossier_id=row.dossier_id,
            priority_grade=row.priority_grade,  # type: ignore[arg-type]
            recommended_service=row.recommended_service,
            why_today=row.why_today,
            expected_budget=row.expected_budget,
            probability=row.probability,
            status=WorkQueueStatus(row.status),
            allowed_actions=[WorkQueueAction(a) for a in (row.allowed_actions or [])],
            rank=row.rank,
        )
        updated = self.queue_builder.apply_action(domain, WorkQueueAction(action))
        row.status = updated.status.value
        row.acted_at = datetime.now(UTC)
        log = list(row.action_log or [])
        log.append({"action": action, "actor": actor, "at": row.acted_at.isoformat()})
        row.action_log = log
        await self.session.flush()
        return row

    async def store_daily_brief(self, dashboard: FounderDashboard) -> RevenueHunterDailyBrief:
        row = RevenueHunterDailyBrief(
            expected_revenue=dashboard.expected_revenue,
            expected_pipeline=dashboard.expected_pipeline,
            meetings_today=dashboard.meetings_today,
            campaign_queue=dashboard.campaign_queue,
            reply_queue=dashboard.reply_queue,
            follow_ups=dashboard.follow_ups,
            hot_opportunities=dashboard.hot_opportunities,
            top_25=list(dashboard.top_25_companies),
            todays_targets=[t.model_dump(mode="json") for t in dashboard.todays_targets],
            payload=dashboard.model_dump(mode="json"),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def latest_brief(self) -> RevenueHunterDailyBrief | None:
        return await self.session.scalar(
            select(RevenueHunterDailyBrief).order_by(RevenueHunterDailyBrief.created_at.desc()).limit(1)
        )

    async def dossiers_as_domain(self, rows: Sequence[RevenueHunterDossier]) -> list[RevenueDossier]:
        out: list[RevenueDossier] = []
        for row in rows:
            raw = dict(row.dossier or {})
            if not raw:
                continue
            # Ensure UUID fields are parseable
            raw.setdefault("company_id", str(row.company_id))
            raw.setdefault("company_name", row.company_name)
            raw.setdefault("recommended_service", row.recommended_service)
            raw.setdefault("expected_budget", row.expected_budget)
            raw.setdefault("expected_timeline", row.expected_timeline)
            raw.setdefault("probability", row.probability)
            raw.setdefault("priority_grade", row.priority_grade)
            raw.setdefault("revenue_score", row.revenue_score)
            raw.setdefault("proceed_to_campaign", row.proceed_to_campaign)
            out.append(RevenueDossier.model_validate(raw))
        return out

    def _decision_to_fields(self, decision: RevenueHunterDecision) -> dict[str, Any]:
        item_meta = decision.dossier
        return {
            "company_id": decision.company_id,
            "opportunity_id": decision.opportunity_id,
            "company_name": decision.company_name,
            "industry": decision.filter_match.matched_industry,
            "country": decision.filter_match.matched_country,
            "company_size_band": decision.filter_match.matched_size,
            "funding_stage": decision.filter_match.matched_funding,
            "revenue_band": decision.filter_match.matched_revenue,
            "filter_passed": decision.filter_match.passed,
            "filter_match": decision.filter_match.model_dump(mode="json"),
            "recommended_service": decision.recommended_service,
            "service_confidence": decision.service_confidence,
            "service_matches": [m.model_dump(mode="json") for m in decision.service_matches],
            "pain_points": [p.model_dump(mode="json") for p in decision.pain_points],
            "website_intelligence": decision.website.model_dump(mode="json"),
            "why_now": decision.why_now.model_dump(mode="json"),
            "dossier": item_meta.model_dump(mode="json"),
            "priority_grade": decision.priority_grade.value,
            "revenue_score": decision.revenue_score,
            "expected_budget": decision.why_now.expected_budget,
            "expected_timeline": decision.why_now.expected_timeline,
            "probability": decision.why_now.probability,
            "proceed_to_campaign": decision.proceed_to_campaign,
            "work_queue_eligible": decision.work_queue_eligible,
            "score_breakdown": [c.model_dump(mode="json") for c in decision.score_breakdown],
            "evidence_chain": list(decision.evidence_chain),
            "explanations": dict(decision.explanations),
            "scoring_version": decision.scoring_version,
            "metadata_json": {},
        }
