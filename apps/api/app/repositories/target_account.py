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
from app.models.target_account import (
    HunterJobRow,
    ICPProfileRow,
    TAIImprovementRecommendation,
    TargetAccount,
)
from app.models.verification import VerificationReport
from target_account_engine.industry.defaults import default_icp_profiles
from target_account_engine.models.types import (
    HunterJob,
    HunterStatus,
    ICPProfile,
    ImprovementRecommendation,
    TargetAccountDecision,
    TargetAccountInput,
)


class TargetAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_default_icps(self) -> None:
        existing = (await self.session.execute(select(ICPProfileRow.key))).scalars().all()
        existing_keys = set(existing)
        for profile in default_icp_profiles():
            if profile.key in existing_keys:
                continue
            self.session.add(self._icp_to_row(profile))
        await self.session.flush()

    async def list_icps(self, *, active_only: bool = True) -> list[ICPProfileRow]:
        stmt = select(ICPProfileRow).order_by(ICPProfileRow.priority.asc())
        if active_only:
            stmt = stmt.where(ICPProfileRow.is_active.is_(True))
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_icp(self, icp_id: UUID) -> ICPProfileRow | None:
        return await self.session.get(ICPProfileRow, icp_id)

    async def get_icp_by_key(self, key: str) -> ICPProfileRow | None:
        return await self.session.scalar(select(ICPProfileRow).where(ICPProfileRow.key == key).limit(1))

    async def upsert_icp(self, profile: ICPProfile) -> ICPProfileRow:
        row = await self.get_icp_by_key(profile.key)
        if row is None:
            row = self._icp_to_row(profile)
            self.session.add(row)
        else:
            for field, value in self._icp_fields(profile).items():
                setattr(row, field, value)
            row.is_active = True
        await self.session.flush()
        return row

    async def delete_icp(self, icp_id: UUID) -> bool:
        row = await self.get_icp(icp_id)
        if row is None:
            return False
        row.is_active = False
        await self.session.flush()
        return True

    async def domain_icps(self) -> list[ICPProfile]:
        rows = await self.list_icps(active_only=True)
        if not rows:
            await self.ensure_default_icps()
            rows = await self.list_icps(active_only=True)
        return [self._row_to_icp(row) for row in rows]

    async def pending_inputs(self, *, limit: int) -> list[TargetAccountInput]:
        latest = (
            select(TargetAccount.company_id, func.max(TargetAccount.created_at).label("created_at"))
            .group_by(TargetAccount.company_id)
            .subquery()
        )
        result = await self.session.execute(
            select(Opportunity)
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
        inputs: list[TargetAccountInput] = []
        for opportunity in result.scalars().all():
            item = await self.build_input(opportunity.company_id, opportunity_id=opportunity.id)
            if item is not None:
                inputs.append(item)
        return inputs

    async def build_input(self, company_id: UUID, *, opportunity_id: UUID | None = None) -> TargetAccountInput | None:
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
            await self.session.execute(
                select(BusinessPain).where(BusinessPain.company_id == company_id).limit(30)
            )
        ).scalars().all()
        goals = (
            await self.session.execute(
                select(BusinessGoal).where(BusinessGoal.company_id == company_id).limit(30)
            )
        ).scalars().all()
        techs = (
            await self.session.execute(
                select(CompanyTechnology).where(CompanyTechnology.company_id == company_id).limit(50)
            )
        ).scalars().all()
        jobs = (
            await self.session.execute(
                select(CompanyJob).where(CompanyJob.company_id == company_id).limit(50)
            )
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
            profile_attrs = {
                "industry": profile.industry,
                "business_model": profile.business_model,
                "company_stage": profile.company_stage,
                "growth_pattern": profile.growth_pattern,
                "hiring_pattern": profile.hiring_pattern,
                "expansion_pattern": profile.expansion_pattern,
                "technology_stack": list(profile.technology_stack or []),
            }
            if profile.evidence and isinstance(profile.evidence, dict):
                profile_attrs.update(
                    {
                        k: v
                        for k, v in profile.evidence.items()
                        if k
                        in {
                            "employee_count",
                            "country",
                            "revenue_band",
                            "funding_stage",
                            "funding_amount",
                            "funding_days_ago",
                        }
                    }
                )

        employee_count = (
            attrs.get("employee_count")
            or profile_attrs.get("employee_count")
            or attrs.get("employees")
        )
        try:
            employee_count_i = int(employee_count) if employee_count is not None else None
        except (TypeError, ValueError):
            employee_count_i = None

        hiring_roles = [str(job.title) for job in jobs if job.title]
        technologies = [str(tech.name) for tech in techs if tech.name]
        if isinstance(profile_attrs.get("technology_stack"), list):
            technologies = list(dict.fromkeys(technologies + [str(t) for t in profile_attrs["technology_stack"]]))
        vendors = list(technologies)
        channel_names: list[str] = []
        contacts: list[dict[str, Any]] = []
        for channel in channels:
            kind = str(channel.kind or "")
            value = str(channel.value or "")
            if kind:
                channel_names.append(kind)
            contacts.append({"type": kind, "value": value, kind: value})

        decision_makers = []
        for maker in makers:
            decision_makers.append(
                {
                    "name": maker.name,
                    "role": maker.role,
                    "confidence": maker.confidence,
                }
            )
            if maker.work_email:
                channel_names.append("email")
                contacts.append({"type": "email", "email": maker.work_email, "value": maker.work_email})
            if maker.linkedin_url:
                channel_names.append("linkedin")
                contacts.append({"type": "linkedin", "linkedin": maker.linkedin_url, "value": maker.linkedin_url})
            if maker.business_phone:
                channel_names.append("phone")
                contacts.append({"type": "phone", "phone": maker.business_phone, "value": maker.business_phone})

        website_metrics = {}
        if isinstance(attrs.get("website_metrics"), dict):
            website_metrics = dict(attrs["website_metrics"])
        enrichment_payload = {}
        if enrichment is not None:
            enrichment_payload = {
                "id": str(enrichment.id),
                "summary": getattr(enrichment, "summary", None),
            }

        verification_score = 0.0
        if verification is not None:
            for key in ("overall_readiness", "trust_score"):
                value = getattr(verification, key, None)
                if isinstance(value, (int, float)):
                    verification_score = float(value)
                    break

        funding_days_ago = attrs.get("funding_days_ago")
        try:
            funding_days_ago_i = int(funding_days_ago) if funding_days_ago is not None else None
        except (TypeError, ValueError):
            funding_days_ago_i = None

        return TargetAccountInput(
            company_id=company.id,
            company_name=company.name,
            opportunity_id=opportunity.id if opportunity else None,
            industry=company.industry or profile_attrs.get("industry"),
            country=profile_attrs.get("country") or attrs.get("country"),
            domain=company.primary_domain,
            website=attrs.get("website") or (f"https://{company.primary_domain}" if company.primary_domain else None),
            employee_count=employee_count_i,
            revenue_band=profile_attrs.get("revenue_band") or attrs.get("revenue_band"),
            funding_stage=profile_attrs.get("funding_stage")
            or profile_attrs.get("company_stage")
            or attrs.get("funding_stage"),
            funding_amount=(
                float(profile_attrs["funding_amount"])
                if isinstance(profile_attrs.get("funding_amount"), (int, float))
                else float(attrs["funding_amount"])
                if isinstance(attrs.get("funding_amount"), (int, float))
                else None
            ),
            funding_days_ago=funding_days_ago_i
            if funding_days_ago_i is not None
            else (
                int(profile_attrs["funding_days_ago"])
                if isinstance(profile_attrs.get("funding_days_ago"), (int, float))
                else None
            ),
            technologies=technologies,
            hiring_roles=hiring_roles,
            hiring_count=len(hiring_roles),
            pains=[str(p.value) for p in pains],
            goals=[str(g.value) for g in goals],
            signals=list(attrs.get("signals") or [])
            if isinstance(attrs.get("signals"), list)
            else [str(profile_attrs.get("hiring_pattern") or ""), str(profile_attrs.get("expansion_pattern") or "")],
            business_model=profile_attrs.get("business_model") or attrs.get("business_model"),
            growth_signals=(
                list(attrs.get("growth_signals") or [])
                if isinstance(attrs.get("growth_signals"), list)
                else [str(profile_attrs.get("growth_pattern") or ""), str(profile_attrs.get("expansion_pattern") or "")]
            ),
            decision_makers=decision_makers,
            contacts=contacts,
            channels=channel_names + (["website"] if company.primary_domain else []),
            vendors=vendors,
            opportunity_score=float(opportunity.opportunity_score) if opportunity is not None else 0.0,
            verification_score=verification_score,
            enrichment=enrichment_payload,
            website_metrics=website_metrics,
            reviews=list(attrs.get("reviews") or []) if isinstance(attrs.get("reviews"), list) else [],
            social_profiles=list(attrs.get("social_profiles") or []) if isinstance(attrs.get("social_profiles"), list) else [],
            news=list(attrs.get("news") or []) if isinstance(attrs.get("news"), list) else [],
            products=list(attrs.get("products") or []) if isinstance(attrs.get("products"), list) else [],
            customers=list(attrs.get("customers") or []) if isinstance(attrs.get("customers"), list) else [],
            metadata={"attributes": attrs},
        )

    async def store_decision(self, decision: TargetAccountDecision) -> TargetAccount:
        icp_row = None
        if decision.matched_icp_key:
            icp_row = await self.get_icp_by_key(decision.matched_icp_key)
        row = TargetAccount(
            company_id=decision.company_id,
            opportunity_id=decision.opportunity_id,
            icp_profile_id=icp_row.id if icp_row else None,
            matched_icp_key=decision.matched_icp_key,
            matched_icp_name=decision.matched_icp_name,
            service_match=decision.service_match,
            company_name=decision.company_name,
            industry=decision.explanations.get("industry"),
            country=decision.explanations.get("country"),
            fit_score=decision.fit.score,
            intent_score=decision.intent.score,
            budget_score=decision.budget.score,
            budget_band=decision.budget.band,
            urgency_score=decision.urgency.score,
            accessibility_score=decision.accessibility.score,
            competition_score=decision.competition.score,
            revenue_opportunity_score=decision.revenue_opportunity_score,
            tier=decision.tier.value,
            why_now=decision.why_now,
            buying_signals=list(decision.buying_signals),
            negative_signals=list(decision.negative_signals),
            score_breakdown=[c.model_dump(mode="json") for c in decision.score_breakdown],
            evidence_chain=list(decision.evidence_chain),
            explanations=dict(decision.explanations),
            hunter_triggered=decision.hunter_triggered,
            hunter_tasks=list(decision.hunter_tasks),
            proceed_to_copilot=decision.proceed_to_copilot,
            scoring_version=decision.scoring_version,
            metadata_json={},
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_targets(
        self,
        *,
        tier: str | None = None,
        icp_key: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[TargetAccount]:
        stmt = select(TargetAccount).order_by(TargetAccount.revenue_opportunity_score.desc())
        if tier:
            stmt = stmt.where(TargetAccount.tier == tier)
        if icp_key:
            stmt = stmt.where(TargetAccount.matched_icp_key == icp_key)
        stmt = stmt.offset(offset).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_target(self, target_id: UUID) -> TargetAccount | None:
        return await self.session.get(TargetAccount, target_id)

    async def latest_for_company(self, company_id: UUID) -> TargetAccount | None:
        return await self.session.scalar(
            select(TargetAccount)
            .where(TargetAccount.company_id == company_id)
            .order_by(TargetAccount.created_at.desc())
            .limit(1)
        )

    async def create_hunter_job(self, job: HunterJob, *, target_account_id: UUID | None) -> HunterJobRow:
        now = datetime.now(UTC)
        row = HunterJobRow(
            company_id=job.company_id,
            target_account_id=target_account_id,
            status=job.status.value,
            tasks=list(job.tasks),
            completed_tasks=list(job.completed_tasks),
            started_at=now if job.status != HunterStatus.QUEUED else None,
            completed_at=now if job.status == HunterStatus.COMPLETED else None,
            result=dict(job.result),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def latest_hunter(self, company_id: UUID | None = None) -> HunterJobRow | None:
        stmt = select(HunterJobRow).order_by(HunterJobRow.created_at.desc()).limit(1)
        if company_id is not None:
            stmt = (
                select(HunterJobRow)
                .where(HunterJobRow.company_id == company_id)
                .order_by(HunterJobRow.created_at.desc())
                .limit(1)
            )
        return await self.session.scalar(stmt)

    async def store_improvements(
        self,
        *,
        target_account_id: UUID | None,
        company_id: UUID | None,
        outcome: str,
        recommendations: list[ImprovementRecommendation],
    ) -> list[TAIImprovementRecommendation]:
        rows: list[TAIImprovementRecommendation] = []
        for rec in recommendations:
            row = TAIImprovementRecommendation(
                target_account_id=target_account_id,
                company_id=company_id,
                outcome=outcome,
                area=rec.area,
                recommendation=rec.recommendation,
                reason=rec.reason,
                expected_impact=rec.expected_impact,
                requires_approval=rec.requires_approval,
                status="proposed",
                metadata_json={},
            )
            self.session.add(row)
            rows.append(row)
        await self.session.flush()
        return rows

    async def top_tier_company_ids(self, *, limit: int = 500) -> set[UUID]:
        rows = (
            await self.session.execute(
                select(TargetAccount.company_id)
                .where(TargetAccount.proceed_to_copilot.is_(True), TargetAccount.tier == "top")
                .order_by(TargetAccount.revenue_opportunity_score.desc())
                .limit(limit)
            )
        ).scalars().all()
        return set(rows)

    def _icp_to_row(self, profile: ICPProfile) -> ICPProfileRow:
        return ICPProfileRow(**self._icp_fields(profile), is_active=True)

    def _icp_fields(self, profile: ICPProfile) -> dict[str, Any]:
        return {
            "key": profile.key,
            "name": profile.name,
            "service_match": profile.service_match,
            "priority": profile.priority,
            "company_size_min": profile.company_size_min,
            "company_size_max": profile.company_size_max,
            "employee_count_min": profile.employee_count_min,
            "employee_count_max": profile.employee_count_max,
            "industries": list(profile.industries),
            "revenue_bands": list(profile.revenue_bands),
            "countries": list(profile.countries),
            "funding_stages": list(profile.funding_stages),
            "hiring_signals": list(profile.hiring_signals),
            "technology_stack": list(profile.technology_stack),
            "business_models": list(profile.business_models),
            "growth_signals": list(profile.growth_signals),
            "decision_makers": list(profile.decision_makers),
            "pain_points": list(profile.pain_points),
            "buying_signals": list(profile.buying_signals),
            "negative_signals": list(profile.negative_signals),
            "metadata_json": {
                **dict(profile.metadata),
                "headquarters_cities": list(profile.headquarters_cities),
                "specialties": list(profile.specialties),
                "company_types": list(profile.company_types),
                "year_founded_min": profile.year_founded_min,
                "year_founded_max": profile.year_founded_max,
                "linkedin_url_required": profile.linkedin_url_required,
                "company_name_contains": list(profile.company_name_contains),
                "domains": list(profile.domains),
                "lists": list(profile.lists),
            },
        }

    def _row_to_icp(self, row: ICPProfileRow) -> ICPProfile:
        meta = dict(row.metadata_json or {})
        return ICPProfile(
            key=row.key,
            name=row.name,
            service_match=row.service_match,
            priority=row.priority,
            company_size_min=row.company_size_min,
            company_size_max=row.company_size_max,
            employee_count_min=row.employee_count_min,
            employee_count_max=row.employee_count_max,
            industries=list(row.industries or []),
            revenue_bands=list(row.revenue_bands or []),
            countries=list(row.countries or []),
            funding_stages=list(row.funding_stages or []),
            hiring_signals=list(row.hiring_signals or []),
            technology_stack=list(row.technology_stack or []),
            business_models=list(row.business_models or []),
            growth_signals=list(row.growth_signals or []),
            decision_makers=list(row.decision_makers or []),
            pain_points=list(row.pain_points or []),
            buying_signals=list(row.buying_signals or []),
            negative_signals=list(row.negative_signals or []),
            headquarters_cities=list(meta.get("headquarters_cities") or []),
            specialties=list(meta.get("specialties") or []),
            company_types=list(meta.get("company_types") or []),
            year_founded_min=meta.get("year_founded_min"),
            year_founded_max=meta.get("year_founded_max"),
            linkedin_url_required=bool(meta.get("linkedin_url_required") or False),
            company_name_contains=list(meta.get("company_name_contains") or []),
            domains=list(meta.get("domains") or []),
            lists=list(meta.get("lists") or []),
            metadata=meta,
        )
