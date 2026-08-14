from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.context import BusinessGoal, BusinessPain, CompanyProfile, TechnologySignal
from app.models.enrichment import (
    CompanyContact,
    CompanyEnrichmentHistory,
    CompanyJob,
    CompanyPerson,
    CompanySocialProfile,
    CompanyTeamInsight,
    CompanyTechnology,
    EnrichedCompanyProfile,
    EnrichmentReport,
    EnrichmentSource,
)
from app.models.intelligence import Company, Person
from app.models.opportunity import Opportunity, OpportunityEvidence
from app.models.revenue import DealEstimate, RevenueBuyerPersona, SalesPlaybook, SolutionMatch
from lead_enrichment.models.types import EnrichmentOpportunityInput, SalesReadyLeadProfile


class EnrichmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def pending_opportunity_inputs(self, *, limit: int) -> Sequence[EnrichmentOpportunityInput]:
        high_priority_statuses = ("qualified", "high_intent")
        stale_or_missing = ~exists().where(
            EnrichmentReport.opportunity_id == Opportunity.id,
            EnrichmentReport.created_at >= Opportunity.created_at,
        )
        has_revenue = exists().where(
            SolutionMatch.opportunity_id == Opportunity.id,
            SolutionMatch.created_at >= Opportunity.created_at,
        )
        high_priority_revenue = exists().where(
            DealEstimate.opportunity_id == Opportunity.id,
            DealEstimate.priority_level.in_(("high", "critical")),
        )
        result = await self.session.execute(
            select(Opportunity.id)
            .where(
                stale_or_missing,
                has_revenue,
                (Opportunity.status.in_(high_priority_statuses) | high_priority_revenue),
            )
            .order_by(Opportunity.opportunity_score.desc(), Opportunity.created_at.desc())
            .limit(limit)
        )
        inputs: list[EnrichmentOpportunityInput] = []
        for opportunity_id in result.scalars().all():
            opportunity_input = await self.opportunity_input(opportunity_id)
            if opportunity_input is not None:
                inputs.append(opportunity_input)
        return inputs

    async def opportunity_input(
        self,
        opportunity_id: UUID,
        *,
        force_refresh: bool = False,
    ) -> EnrichmentOpportunityInput | None:
        opportunity = await self.session.get(Opportunity, opportunity_id)
        if opportunity is None:
            return None
        company = await self.session.get(Company, opportunity.company_id)
        if company is None:
            return None

        profile = await self._latest_context_profile(company.id)
        pains = list(await self._pains(company.id))
        goals = list(await self._goals(company.id))
        tech_signals = list(await self._technology_signals(company.id))
        people = list(await self._people(company.id))
        evidence = list(await self._opportunity_evidence(opportunity_id))
        revenue = await self._revenue_recommendation(company.id, opportunity_id)

        context_intelligence: dict[str, Any] = {
            "industry": profile.industry if profile else company.industry,
            "business_model": profile.business_model if profile else None,
            "company_stage": profile.company_stage if profile else None,
            "technology_stack": list(profile.technology_stack) if profile else [],
            "hiring_pattern": profile.hiring_pattern if profile else None,
            "growth_pattern": profile.growth_pattern if profile else None,
            "location": company.attributes.get("location") if company.attributes else None,
            "sub_industry": company.attributes.get("sub_industry") if company.attributes else None,
        }

        return EnrichmentOpportunityInput(
            company_id=company.id,
            opportunity_id=opportunity.id,
            company_name=company.name,
            domain=company.primary_domain,
            website=f"https://{company.primary_domain}" if company.primary_domain else None,
            opportunity_score=opportunity.opportunity_score,
            opportunity_status=opportunity.status,
            opportunity_narrative=opportunity.narrative,
            industry=profile.industry if profile else company.industry,
            description=company.description or company.memory_summary,
            location=str(company.attributes.get("location")) if company.attributes.get("location") else None,
            country=str(company.attributes.get("country")) if company.attributes.get("country") else None,
            company_attributes=dict(company.attributes or {}),
            context_intelligence=context_intelligence,
            technology_signals=[self._tech_dict(item) for item in tech_signals],
            pains=[self._inference_dict(item) for item in pains],
            goals=[self._inference_dict(item) for item in goals],
            known_people=[self._person_dict(item) for item in people],
            revenue_recommendation=revenue,
            opportunity_evidence=[self._evidence_dict(item) for item in evidence],
            force_refresh=force_refresh,
        )

    async def store_enrichment(self, result: SalesReadyLeadProfile) -> UUID:
        report = EnrichmentReport(
            company_id=result.company_id,
            opportunity_id=result.opportunity_id,
            company_name=result.company_name,
            opportunity_score=result.opportunity_score,
            business_pain=result.business_pain,
            recommended_service=result.recommended_service,
            buyer_persona=result.buyer_persona,
            estimated_budget=result.estimated_budget,
            priority=result.priority,
            why_now=result.why_now,
            best_outreach_angle=result.best_outreach_angle,
            profile_completeness=result.enrichment_confidence.profile_completeness,
            contact_availability=result.enrichment_confidence.contact_availability,
            technology_confidence=result.enrichment_confidence.technology_confidence,
            decision_maker_confidence=result.enrichment_confidence.decision_maker_confidence,
            overall_enrichment_confidence=result.enrichment_confidence.overall_enrichment_confidence,
            evidence_chain=[item.model_dump(mode="json") for item in result.evidence_chain],
            lead_profile=result.model_dump(mode="json"),
            processing_latency_ms=result.processing_latency_ms,
        )
        self.session.add(report)
        await self.session.flush()

        profile = result.company_profile
        self.session.add(
            EnrichedCompanyProfile(
                company_id=result.company_id,
                opportunity_id=result.opportunity_id,
                enrichment_report_id=report.id,
                company_name=profile.company_name,
                website=profile.website,
                domain=profile.domain,
                industry=profile.industry,
                sub_industry=profile.sub_industry,
                description=profile.description,
                location=profile.location,
                country=profile.country,
                founded_year=profile.founded_year,
                employee_count_estimate=profile.employee_count_estimate,
                company_size_range=profile.company_size_range,
                revenue_estimate=profile.revenue_estimate,
                field_attributions=[item.model_dump(mode="json") for item in profile.attributions],
                evidence={"opportunity_id": str(result.opportunity_id)},
            )
        )

        for contact in result.public_contact_information:
            self.session.add(
                CompanyContact(
                    company_id=result.company_id,
                    enrichment_report_id=report.id,
                    kind=contact.kind.value,
                    value=contact.value,
                    label=contact.label,
                    confidence=contact.confidence,
                    source=contact.source.value,
                    source_url=contact.source_url,
                    is_public=contact.is_public,
                )
            )

        for person in result.decision_makers:
            self.session.add(
                CompanyPerson(
                    company_id=result.company_id,
                    enrichment_report_id=report.id,
                    name=person.name,
                    role=person.role,
                    department=person.department,
                    linkedin_url=person.linkedin_url,
                    work_email=person.work_email,
                    business_phone=person.business_phone,
                    confidence=person.confidence,
                    source=person.source.value,
                    source_url=person.source_url,
                )
            )

        for social in result.social_profiles:
            self.session.add(
                CompanySocialProfile(
                    company_id=result.company_id,
                    enrichment_report_id=report.id,
                    platform=social.platform,
                    url=social.url,
                    handle=social.handle,
                    confidence=social.confidence,
                    source=social.source.value,
                )
            )

        for tech in result.technology_stack:
            self.session.add(
                CompanyTechnology(
                    company_id=result.company_id,
                    enrichment_report_id=report.id,
                    name=tech.name,
                    category=tech.category,
                    confidence=tech.confidence,
                    source=tech.source.value,
                    source_url=tech.source_url,
                    signal=tech.signal,
                )
            )

        insights = result.team_insights
        self.session.add(
            CompanyTeamInsight(
                company_id=result.company_id,
                enrichment_report_id=report.id,
                leadership_team_size=insights.leadership_team_size,
                engineering_team_estimate=insights.engineering_team_estimate,
                support_team_estimate=insights.support_team_estimate,
                operations_team_estimate=insights.operations_team_estimate,
                recent_hires=list(insights.recent_hires),
                open_positions=list(insights.open_positions),
                hiring_trends=insights.hiring_trends,
                attributions=[item.model_dump(mode="json") for item in insights.attributions],
            )
        )

        for job in result.open_jobs:
            self.session.add(
                CompanyJob(
                    company_id=result.company_id,
                    enrichment_report_id=report.id,
                    title=job.title,
                    department=job.department,
                    location=job.location,
                    url=job.url,
                    confidence=job.confidence,
                    source=job.source.value,
                    source_url=job.source_url,
                )
            )

        for source in result.source_attribution:
            self.session.add(
                EnrichmentSource(
                    enrichment_report_id=report.id,
                    company_id=result.company_id,
                    source=source.source.value,
                    source_url=source.source_url,
                    fields=list(source.fields),
                    confidence=source.confidence,
                    licensed=source.licensed,
                    notes=source.notes,
                )
            )

        self.session.add(
            CompanyEnrichmentHistory(
                company_id=result.company_id,
                opportunity_id=result.opportunity_id,
                enrichment_report_id=report.id,
                action="enrichment_created",
                actor="lead_enrichment",
                details={
                    "overall_confidence": result.enrichment_confidence.overall_enrichment_confidence,
                    "priority": result.priority,
                    "recommended_service": result.recommended_service,
                },
            )
        )
        await self.session.flush()
        return report.id

    async def latest_report_for_company(self, company_id: UUID) -> EnrichmentReport | None:
        result = await self.session.execute(
            select(EnrichmentReport)
            .where(EnrichmentReport.company_id == company_id)
            .order_by(EnrichmentReport.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def latest_report_for_opportunity(self, opportunity_id: UUID) -> EnrichmentReport | None:
        result = await self.session.execute(
            select(EnrichmentReport)
            .where(EnrichmentReport.opportunity_id == opportunity_id)
            .order_by(EnrichmentReport.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def lead_profile_for_company(self, company_id: UUID) -> dict[str, Any] | None:
        report = await self.latest_report_for_company(company_id)
        if report is None:
            return None
        return self._report_payload(report)

    async def lead_profile_for_opportunity(self, opportunity_id: UUID) -> dict[str, Any] | None:
        report = await self.latest_report_for_opportunity(opportunity_id)
        if report is None:
            return None
        return self._report_payload(report)

    def _report_payload(self, report: EnrichmentReport) -> dict[str, Any]:
        profile = dict(report.lead_profile or {})
        profile.update(
            {
                "enrichment_report_id": str(report.id),
                "created_at": report.created_at.isoformat(),
                "overall_enrichment_confidence": report.overall_enrichment_confidence,
            }
        )
        return profile

    async def _latest_context_profile(self, company_id: UUID) -> CompanyProfile | None:
        result = await self.session.execute(
            select(CompanyProfile)
            .where(CompanyProfile.company_id == company_id)
            .order_by(CompanyProfile.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _pains(self, company_id: UUID) -> Sequence[BusinessPain]:
        result = await self.session.execute(
            select(BusinessPain)
            .where(BusinessPain.company_id == company_id)
            .order_by(BusinessPain.confidence.desc())
            .limit(20)
        )
        return result.scalars().all()

    async def _goals(self, company_id: UUID) -> Sequence[BusinessGoal]:
        result = await self.session.execute(
            select(BusinessGoal)
            .where(BusinessGoal.company_id == company_id)
            .order_by(BusinessGoal.confidence.desc())
            .limit(20)
        )
        return result.scalars().all()

    async def _technology_signals(self, company_id: UUID) -> Sequence[TechnologySignal]:
        result = await self.session.execute(
            select(TechnologySignal)
            .where(TechnologySignal.company_id == company_id)
            .order_by(TechnologySignal.confidence.desc())
            .limit(50)
        )
        return result.scalars().all()

    async def _people(self, company_id: UUID) -> Sequence[Person]:
        result = await self.session.execute(
            select(Person).where(Person.company_id == company_id).order_by(Person.created_at.desc()).limit(20)
        )
        return result.scalars().all()

    async def _opportunity_evidence(self, opportunity_id: UUID) -> Sequence[OpportunityEvidence]:
        result = await self.session.execute(
            select(OpportunityEvidence)
            .where(OpportunityEvidence.opportunity_id == opportunity_id)
            .order_by(OpportunityEvidence.confidence.desc())
            .limit(20)
        )
        return result.scalars().all()

    async def _revenue_recommendation(self, company_id: UUID, opportunity_id: UUID) -> dict[str, Any]:
        result = await self.session.execute(
            select(SolutionMatch)
            .where(
                SolutionMatch.company_id == company_id,
                SolutionMatch.opportunity_id == opportunity_id,
            )
            .order_by(SolutionMatch.created_at.desc())
            .limit(1)
        )
        match = result.scalar_one_or_none()
        if match is None:
            result = await self.session.execute(
                select(SolutionMatch)
                .where(SolutionMatch.company_id == company_id)
                .order_by(SolutionMatch.created_at.desc())
                .limit(1)
            )
            match = result.scalar_one_or_none()
        if match is None:
            return {}

        estimate_result = await self.session.execute(
            select(DealEstimate)
            .where(DealEstimate.solution_match_id == match.id)
            .order_by(DealEstimate.created_at.desc())
            .limit(1)
        )
        estimate = estimate_result.scalar_one_or_none()
        playbook_result = await self.session.execute(
            select(SalesPlaybook)
            .where(SalesPlaybook.solution_match_id == match.id)
            .order_by(SalesPlaybook.created_at.desc())
            .limit(1)
        )
        playbook = playbook_result.scalar_one_or_none()
        persona_result = await self.session.execute(
            select(RevenueBuyerPersona)
            .where(RevenueBuyerPersona.solution_match_id == match.id)
            .order_by(RevenueBuyerPersona.confidence.desc())
            .limit(1)
        )
        persona = persona_result.scalar_one_or_none()
        return {
            "solution_match_id": str(match.id),
            "recommended_service": match.primary_service_key,
            "secondary_service": match.secondary_service_key,
            "confidence": match.confidence,
            "business_pain": playbook.business_pain if playbook else None,
            "conversation_angle": playbook.conversation_angle if playbook else None,
            "buyer_persona": persona.persona if persona else (playbook.decision_maker if playbook else None),
            "estimated_budget_range": estimate.estimated_budget_range if estimate else None,
            "priority": estimate.priority_level if estimate else None,
            "project_size": estimate.project_size if estimate else None,
        }

    def _inference_dict(self, item: BusinessPain | BusinessGoal) -> dict[str, Any]:
        return {
            "category": item.category,
            "value": item.value,
            "confidence": item.confidence,
            "evidence": item.evidence,
        }

    def _tech_dict(self, item: TechnologySignal) -> dict[str, Any]:
        return {
            "technology": item.technology,
            "category": item.category,
            "confidence": item.confidence,
            "adoption_signal": item.adoption_signal,
        }

    def _person_dict(self, item: Person) -> dict[str, Any]:
        attrs = item.attributes or {}
        return {
            "name": item.name,
            "title": item.title,
            "role": item.title,
            "linkedin_url": attrs.get("linkedin_url"),
            "email": attrs.get("email"),
            "confidence": float(attrs.get("confidence") or 80.0),
            "department": attrs.get("department"),
        }

    def _evidence_dict(self, item: OpportunityEvidence) -> dict[str, Any]:
        return {
            "category": item.category,
            "summary": item.summary,
            "confidence": item.confidence,
            "reference_id": str(item.reference_id) if item.reference_id else None,
            "source_type": item.source_type,
        }
