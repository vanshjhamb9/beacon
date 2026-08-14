from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.context import BusinessContext, BusinessPain, CompanyProfile, ContextEvidence
from app.models.copilot import (
    SalesDraft,
    SalesFeedback,
    SalesGenerationLog,
    SalesPackage,
    SalesPromptVersion,
    SalesVersion,
)
from app.models.decision import DecisionDiscoveryReport, DecisionMaker
from app.models.enrichment import CompanyJob, CompanyTechnology, EnrichmentReport
from app.models.intelligence import Company, CompanyTimeline
from app.models.opportunity import Opportunity, OpportunityEvidence
from app.models.quality import QualityReport
from app.models.revenue import SalesPlaybook, SolutionMatch
from app.models.verification import VerificationReport
from sales_copilot.models.types import ReviewAction, ReviewStatus, SalesCopilotInput, SalesIntelligencePackage
from sales_copilot.prompting.versions import PROMPT_V1


class SalesCopilotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_prompt_seed(self) -> None:
        existing = await self.session.scalar(
            select(SalesPromptVersion).where(SalesPromptVersion.version == PROMPT_V1.version).limit(1)
        )
        if existing is not None:
            return
        self.session.add(
            SalesPromptVersion(
                version=PROMPT_V1.version,
                name=PROMPT_V1.name,
                system_prompt=PROMPT_V1.system_prompt,
                user_prompt_template=PROMPT_V1.user_prompt_template,
                temperature=PROMPT_V1.temperature,
                model_hint=PROMPT_V1.model_hint,
                provider_hint=PROMPT_V1.provider_hint.value,
                is_active=True,
                metadata_json={},
            )
        )
        await self.session.flush()

    async def pending_inputs(self, *, limit: int) -> Sequence[SalesCopilotInput]:
        latest_package = (
            select(SalesPackage.opportunity_id, func.max(SalesPackage.created_at).label("created_at"))
            .group_by(SalesPackage.opportunity_id)
            .subquery()
        )
        result = await self.session.execute(
            select(Opportunity)
            .outerjoin(latest_package, latest_package.c.opportunity_id == Opportunity.id)
            .where(
                or_(
                    latest_package.c.created_at.is_(None),
                    Opportunity.updated_at > latest_package.c.created_at,
                )
            )
            .order_by(Opportunity.opportunity_score.desc(), Opportunity.created_at.desc())
            .limit(limit)
        )
        inputs: list[SalesCopilotInput] = []
        for opportunity in result.scalars().all():
            item = await self.build_input_for_opportunity(opportunity.id)
            if item is not None:
                inputs.append(item)
        return inputs

    async def build_input_for_company(self, company_id: UUID, *, force_refresh: bool = False) -> SalesCopilotInput | None:
        opportunity = await self.session.scalar(
            select(Opportunity)
            .where(Opportunity.company_id == company_id)
            .order_by(Opportunity.opportunity_score.desc(), Opportunity.created_at.desc())
            .limit(1)
        )
        if opportunity is None:
            return None
        return await self.build_input_for_opportunity(opportunity.id, force_refresh=force_refresh)

    async def build_input_for_opportunity(
        self, opportunity_id: UUID, *, force_refresh: bool = False
    ) -> SalesCopilotInput | None:
        opportunity = await self.session.get(Opportunity, opportunity_id)
        if opportunity is None:
            return None
        company = await self.session.get(Company, opportunity.company_id)
        if company is None:
            return None

        enrichment = await self.session.scalar(
            select(EnrichmentReport)
            .where(EnrichmentReport.opportunity_id == opportunity_id)
            .order_by(EnrichmentReport.created_at.desc())
            .limit(1)
        )
        verification = await self.session.scalar(
            select(VerificationReport)
            .where(VerificationReport.opportunity_id == opportunity_id)
            .order_by(VerificationReport.created_at.desc())
            .limit(1)
        )
        decision = await self.session.scalar(
            select(DecisionDiscoveryReport)
            .where(DecisionDiscoveryReport.opportunity_id == opportunity_id)
            .order_by(DecisionDiscoveryReport.created_at.desc())
            .limit(1)
        )
        playbook = await self.session.scalar(
            select(SalesPlaybook)
            .where(SalesPlaybook.opportunity_id == opportunity_id)
            .order_by(SalesPlaybook.created_at.desc())
            .limit(1)
        )
        solution = await self.session.scalar(
            select(SolutionMatch)
            .where(SolutionMatch.opportunity_id == opportunity_id)
            .order_by(SolutionMatch.created_at.desc())
            .limit(1)
        )
        profile = await self.session.scalar(
            select(CompanyProfile)
            .where(CompanyProfile.company_id == company.id)
            .order_by(CompanyProfile.created_at.desc())
            .limit(1)
        )
        pains = (
            await self.session.execute(
                select(BusinessPain)
                .where(BusinessPain.company_id == company.id)
                .order_by(BusinessPain.created_at.desc())
                .limit(20)
            )
        ).scalars().all()
        context_ids = (
            await self.session.execute(
                select(BusinessContext.id)
                .where(BusinessContext.company_id == company.id)
                .order_by(BusinessContext.created_at.desc())
                .limit(20)
            )
        ).scalars().all()
        evidence_rows = []
        if context_ids:
            evidence_rows = (
                await self.session.execute(
                    select(ContextEvidence)
                    .where(ContextEvidence.business_context_id.in_(list(context_ids)))
                    .order_by(ContextEvidence.created_at.desc())
                    .limit(40)
                )
            ).scalars().all()
        opp_evidence = (
            await self.session.execute(
                select(OpportunityEvidence)
                .where(OpportunityEvidence.opportunity_id == opportunity_id)
                .order_by(OpportunityEvidence.created_at.desc())
                .limit(40)
            )
        ).scalars().all()
        timeline = (
            await self.session.execute(
                select(CompanyTimeline)
                .where(CompanyTimeline.company_id == company.id)
                .order_by(CompanyTimeline.timestamp.desc())
                .limit(30)
            )
        ).scalars().all()
        latest_context = await self.session.scalar(
            select(BusinessContext)
            .where(BusinessContext.company_id == company.id)
            .order_by(BusinessContext.created_at.desc())
            .limit(1)
        )
        quality = None
        if latest_context is not None:
            quality = await self.session.get(QualityReport, latest_context.quality_report_id)

        technologies: list[dict[str, Any]] = []
        jobs: list[dict[str, Any]] = []
        makers: list[dict[str, Any]] = []
        if enrichment is not None:
            tech_rows = (
                await self.session.execute(
                    select(CompanyTechnology).where(CompanyTechnology.enrichment_report_id == enrichment.id)
                )
            ).scalars().all()
            technologies = [
                {
                    "id": str(row.id),
                    "name": row.name,
                    "confidence": row.confidence,
                    "source": row.source,
                    "source_url": row.source_url,
                }
                for row in tech_rows
            ]
            job_rows = (
                await self.session.execute(select(CompanyJob).where(CompanyJob.enrichment_report_id == enrichment.id))
            ).scalars().all()
            jobs = [
                {"title": row.title, "role": row.title, "confidence": row.confidence, "source": row.source}
                for row in job_rows
            ]
        if decision is not None:
            maker_rows = (
                await self.session.execute(
                    select(DecisionMaker).where(DecisionMaker.discovery_report_id == decision.id)
                )
            ).scalars().all()
            makers = [
                {
                    "id": str(row.id),
                    "name": row.name,
                    "role": row.role,
                    "normalized_role": row.normalized_role,
                    "confidence": row.confidence,
                    "evidence": row.evidence,
                    "source": row.source,
                    "source_url": row.source_url,
                    "is_primary": row.is_primary,
                    "is_secondary": row.is_secondary,
                }
                for row in maker_rows
            ]

        lead_profile = dict(enrichment.lead_profile or {}) if enrichment else {}
        if enrichment is not None:
            lead_profile.setdefault("business_pain", enrichment.business_pain)
            lead_profile.setdefault("recommended_service", enrichment.recommended_service)
            lead_profile.setdefault("buyer_persona", enrichment.buyer_persona)
            lead_profile.setdefault("why_now", enrichment.why_now)
            lead_profile.setdefault("outreach_angles", [enrichment.best_outreach_angle] if enrichment.best_outreach_angle else [])
        conversation_angles: list[str] = []
        if playbook and playbook.conversation_angle:
            conversation_angles.append(playbook.conversation_angle)
        conversation_angles.extend(list(lead_profile.get("outreach_angles") or []))
        revenue = {
            "recommended_service": (
                (playbook.recommended_service if playbook else None)
                or lead_profile.get("recommended_service")
                or (solution.primary_service_key if solution else None)
            ),
            "business_pain": (
                (playbook.business_pain if playbook else None)
                or lead_profile.get("business_pain")
                or opportunity.narrative
            ),
            "buyer_persona": (playbook.decision_maker if playbook else None) or lead_profile.get("buyer_persona"),
            "value_proposition": (playbook.why if playbook else None) or lead_profile.get("why_now"),
            "conversation_angles": conversation_angles,
            "playbook": {
                "recommended_service": playbook.recommended_service if playbook else None,
                "business_pain": playbook.business_pain if playbook else None,
                "value_proposition": playbook.why if playbook else None,
                "conversation_angles": conversation_angles,
            },
        }
        primary = next((item for item in makers if item.get("is_primary")), makers[0] if makers else None)
        secondary = next((item for item in makers if item.get("is_secondary")), None)

        evidence_chain: list[dict[str, Any]] = []
        for row in evidence_rows:
            details = dict(row.details or {})
            evidence_chain.append(
                {
                    "category": row.evidence_type or "context",
                    "summary": str(details.get("summary") or details.get("explanation") or row.reference_key or "Context evidence"),
                    "source": "beacon_context",
                    "confidence": float(row.confidence or 60.0),
                    "reference_id": str(row.id),
                }
            )
        for row in opp_evidence:
            evidence_chain.append(
                {
                    "category": row.category or "opportunity",
                    "summary": row.summary,
                    "source": "beacon_opportunity",
                    "confidence": float(row.confidence or 70.0),
                    "reference_id": str(row.id),
                }
            )
        if enrichment is not None:
            evidence_chain.extend(list(enrichment.evidence_chain or []))
        if decision is not None:
            evidence_chain.extend(list(decision.evidence_chain or []))

        return SalesCopilotInput(
            company_id=company.id,
            opportunity_id=opportunity.id,
            company_name=company.name,
            domain=company.primary_domain,
            website=f"https://{company.primary_domain}" if company.primary_domain else None,
            industry=company.industry,
            opportunity_score=opportunity.opportunity_score,
            opportunity_status=opportunity.status,
            opportunity_narrative=opportunity.narrative or "",
            business_pain=str(revenue.get("business_pain") or ""),
            recommended_service=str(revenue.get("recommended_service") or ""),
            buyer_persona=str(revenue.get("buyer_persona")) if revenue.get("buyer_persona") else None,
            company={
                "id": str(company.id),
                "name": company.name,
                "industry": company.industry,
                "primary_domain": company.primary_domain,
                "memory_summary": company.memory_summary,
            },
            opportunity={
                "id": str(opportunity.id),
                "status": opportunity.status,
                "narrative": opportunity.narrative,
                "opportunity_score": opportunity.opportunity_score,
            },
            revenue=revenue,
            lead_enrichment={
                **lead_profile,
                "technologies": technologies,
                "jobs": jobs,
                "business_pain": lead_profile.get("business_pain") or revenue.get("business_pain"),
                "recommended_service": lead_profile.get("recommended_service") or revenue.get("recommended_service"),
                "why_now": lead_profile.get("why_now"),
                "company_profile": lead_profile.get("company_profile") or {},
            },
            verification={
                "id": str(verification.id) if verification else None,
                "decision": verification.decision if verification else None,
                "result_payload": dict(verification.result_payload or {}) if verification else {},
                "overall_score": verification.overall_data_quality if verification else None,
                "trust": {"score": verification.trust_score, "status": verification.freshness_status}
                if verification
                else {},
            },
            decision_makers={
                "primary_decision_maker": primary,
                "secondary_decision_maker": secondary,
                "decision_makers": makers,
                "recommended_service": decision.recommended_service if decision else revenue.get("recommended_service"),
                "business_pain": decision.business_pain if decision else revenue.get("business_pain"),
            },
            context={
                "dna": {
                    "industry": profile.industry if profile else company.industry,
                    "business_model": profile.business_model if profile else None,
                    "hiring_pattern": profile.hiring_pattern if profile else None,
                },
                "pains": [
                    {
                        "id": str(pain.id),
                        "title": pain.category,
                        "description": pain.value,
                        "confidence": pain.confidence,
                    }
                    for pain in pains
                ],
                "technologies": list(profile.technology_stack) if profile else [],
            },
            quality={
                "id": str(quality.id) if quality else None,
                "decision": quality.decision if quality else None,
            },
            knowledge_graph={"nodes": []},
            timeline=[
                {
                    "id": str(event.id),
                    "summary": event.summary,
                    "title": event.signal_type,
                    "event_type": event.signal_type,
                    "confidence": event.confidence,
                }
                for event in timeline
            ],
            evidence_chain=evidence_chain,
            force_refresh=force_refresh,
        )

    async def next_version(self, opportunity_id: UUID) -> int:
        current = await self.session.scalar(
            select(func.max(SalesPackage.version)).where(SalesPackage.opportunity_id == opportunity_id)
        )
        return int(current or 0) + 1

    async def store_package(self, package: SalesIntelligencePackage) -> SalesPackage:
        await self.ensure_prompt_seed()
        row = SalesPackage(
            company_id=package.company_id,
            opportunity_id=package.opportunity_id,
            company_name=package.company_name,
            opportunity_score=package.opportunity_score,
            recommended_service=package.recommended_service or "",
            business_pain=package.business_pain or "",
            version=package.version,
            review_status=package.review_status.value,
            is_favorite=package.is_favorite,
            prompt_version=package.generation.prompt_version,
            llm_provider=package.generation.llm_provider.value,
            llm_model=package.generation.model,
            temperature=package.generation.temperature,
            prompt_tokens=package.generation.prompt_tokens,
            completion_tokens=package.generation.completion_tokens,
            total_tokens=package.generation.total_tokens,
            latency_ms=package.generation.latency_ms,
            generation_time_ms=package.generation.generation_time_ms,
            cost_estimate_usd=package.generation.cost_estimate_usd,
            quality_scores=package.quality.model_dump(mode="json"),
            sections=[item.model_dump(mode="json") for item in package.sections],
            style_variants=[item.model_dump(mode="json") for item in package.style_variants],
            evidence_chain=[item.model_dump(mode="json") for item in package.evidence_chain],
            package_payload=package.package_payload,
        )
        self.session.add(row)
        await self.session.flush()

        for variant in package.style_variants:
            for draft in variant.drafts:
                self.session.add(
                    SalesDraft(
                        package_id=row.id,
                        company_id=package.company_id,
                        opportunity_id=package.opportunity_id,
                        kind=draft.kind.value,
                        style=draft.style.value,
                        title=draft.title,
                        body=draft.body,
                        subject_lines=list(draft.subject_lines),
                        attribution=draft.attribution.model_dump(mode="json"),
                        metadata_json=dict(draft.metadata),
                    )
                )

        self.session.add(
            SalesGenerationLog(
                package_id=row.id,
                company_id=package.company_id,
                opportunity_id=package.opportunity_id,
                prompt_version=package.generation.prompt_version,
                llm_provider=package.generation.llm_provider.value,
                llm_model=package.generation.model,
                temperature=package.generation.temperature,
                prompt_tokens=package.generation.prompt_tokens,
                completion_tokens=package.generation.completion_tokens,
                total_tokens=package.generation.total_tokens,
                latency_ms=package.generation.latency_ms,
                generation_time_ms=package.generation.generation_time_ms,
                cost_estimate_usd=package.generation.cost_estimate_usd,
                status="succeeded",
                request_payload={"prompt_version": package.generation.prompt_version},
                response_payload={
                    "quality": package.quality.model_dump(mode="json"),
                    "section_count": len(package.sections),
                    "draft_count": sum(len(variant.drafts) for variant in package.style_variants),
                },
            )
        )
        self.session.add(
            SalesVersion(
                package_id=row.id,
                company_id=package.company_id,
                opportunity_id=package.opportunity_id,
                version=package.version,
                snapshot={
                    "sections": [item.model_dump(mode="json") for item in package.sections],
                    "style_variants": [item.model_dump(mode="json") for item in package.style_variants],
                    "quality": package.quality.model_dump(mode="json"),
                    "evidence_chain": [item.model_dump(mode="json") for item in package.evidence_chain],
                    "generation": package.generation.model_dump(mode="json"),
                },
                change_reason="generated" if package.version == 1 else "regenerated",
            )
        )
        await self.session.flush()
        return row

    async def latest_for_company(self, company_id: UUID) -> SalesPackage | None:
        return await self.session.scalar(
            select(SalesPackage)
            .where(SalesPackage.company_id == company_id)
            .order_by(SalesPackage.version.desc(), SalesPackage.created_at.desc())
            .limit(1)
        )

    async def latest_for_opportunity(self, opportunity_id: UUID) -> SalesPackage | None:
        return await self.session.scalar(
            select(SalesPackage)
            .where(SalesPackage.opportunity_id == opportunity_id)
            .order_by(SalesPackage.version.desc(), SalesPackage.created_at.desc())
            .limit(1)
        )

    async def get_package(self, package_id: UUID) -> SalesPackage | None:
        return await self.session.get(SalesPackage, package_id)

    async def package_bundle(self, package: SalesPackage) -> dict[str, Any]:
        drafts = (
            await self.session.execute(
                select(SalesDraft)
                .where(SalesDraft.package_id == package.id)
                .order_by(SalesDraft.style, SalesDraft.kind)
            )
        ).scalars().all()
        feedback = (
            await self.session.execute(
                select(SalesFeedback)
                .where(SalesFeedback.package_id == package.id)
                .order_by(SalesFeedback.created_at.desc())
            )
        ).scalars().all()
        return {"package": package, "drafts": drafts, "feedback": feedback}

    async def history_for_entity(self, entity_id: UUID) -> list[SalesPackage]:
        result = await self.session.execute(
            select(SalesPackage)
            .where(or_(SalesPackage.company_id == entity_id, SalesPackage.opportunity_id == entity_id, SalesPackage.id == entity_id))
            .order_by(SalesPackage.version.desc(), SalesPackage.created_at.desc())
        )
        return list(result.scalars().all())

    async def apply_review(
        self,
        package: SalesPackage,
        *,
        action: ReviewAction,
        reviewer: str,
        notes: str,
        rating: float | None,
    ) -> SalesPackage:
        status_map = {
            ReviewAction.APPROVE: ReviewStatus.APPROVED,
            ReviewAction.REJECT: ReviewStatus.REJECTED,
            ReviewAction.ARCHIVE: ReviewStatus.ARCHIVED,
            ReviewAction.MARK_FAVORITE: ReviewStatus.FAVORITE,
            ReviewAction.REGENERATE: ReviewStatus.REGENERATED,
        }
        package.review_status = status_map[action].value
        if action == ReviewAction.MARK_FAVORITE:
            package.is_favorite = True
        self.session.add(
            SalesFeedback(
                package_id=package.id,
                company_id=package.company_id,
                opportunity_id=package.opportunity_id,
                action=action.value,
                reviewer=reviewer,
                notes=notes,
                rating=rating,
                metadata_json={},
            )
        )
        await self.session.flush()
        return package
