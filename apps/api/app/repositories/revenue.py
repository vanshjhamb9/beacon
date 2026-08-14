from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import case, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.context import BusinessContext, BusinessGoal, BusinessPain, CompanyProfile
from app.models.intelligence import Company, KnowledgeGraphNode
from app.models.opportunity import Opportunity, OpportunityEvidence
from app.models.quality import QualityReport
from app.models.revenue import (
    DealEstimate,
    DealPredictionModel,
    RecommendationHistory,
    RevenueBuyerPersona,
    RevenueHistory,
    RevenueMetric,
    SalesCycle,
    SalesPlaybook,
    ServiceCatalog,
    ServiceRule,
    SolutionMatch,
)
from revenue_engine.catalog import default_service_catalog, default_service_rules
from revenue_engine.models.types import (
    RevenueOpportunityInput,
    RevenueRecommendationResult,
    ServiceDefinition,
)


class RevenueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def pending_opportunity_inputs(self, *, limit: int) -> Sequence[RevenueOpportunityInput]:
        await self.ensure_services_seeded()
        stale_or_missing = ~exists().where(
            SolutionMatch.opportunity_id == Opportunity.id,
            SolutionMatch.created_at >= Opportunity.created_at,
        )
        result = await self.session.execute(
            select(Opportunity.id)
            .where(stale_or_missing)
            .order_by(Opportunity.opportunity_score.desc(), Opportunity.created_at.desc())
            .limit(limit)
        )
        inputs: list[RevenueOpportunityInput] = []
        for opportunity_id in result.scalars().all():
            opportunity_input = await self.opportunity_input(opportunity_id)
            if opportunity_input is not None:
                inputs.append(opportunity_input)
        return inputs

    async def opportunity_input(self, opportunity_id: UUID) -> RevenueOpportunityInput | None:
        opportunity = await self.session.get(Opportunity, opportunity_id)
        if opportunity is None:
            return None
        company = await self.session.get(Company, opportunity.company_id)
        if company is None:
            return None
        profile = await self._latest_profile(opportunity.company_id)
        pains = list(await self._pains(opportunity.company_id))
        goals = list(await self._goals(opportunity.company_id))
        contexts = list(await self._contexts(opportunity.company_id))
        evidence = list(await self._opportunity_evidence(opportunity_id))
        knowledge_node_ids = list(await self._knowledge_node_ids(company.normalized_name))
        quality_score = await self._latest_quality_score(opportunity.company_id)
        services = list(await self.list_enabled_services())
        return RevenueOpportunityInput(
            company_id=company.id,
            company_name=company.name,
            opportunity_id=opportunity.id,
            opportunity_score=opportunity.opportunity_score,
            urgency_score=opportunity.urgency_score,
            confidence_score=opportunity.confidence_score,
            recommendation=opportunity.recommendation,
            narrative=opportunity.narrative,
            industry=profile.industry if profile else company.industry,
            business_model=profile.business_model if profile else None,
            company_stage=profile.company_stage if profile else None,
            technology_stack=list(profile.technology_stack) if profile else [],
            pains=[self._inference_dict(item) for item in pains],
            goals=[self._inference_dict(item) for item in goals],
            contexts=[self._context_dict(item) for item in contexts],
            opportunity_evidence=[self._evidence_dict(item) for item in evidence],
            knowledge_node_ids=knowledge_node_ids,
            quality_score=quality_score,
            services=services,
        )

    async def store_recommendation(self, result: RevenueRecommendationResult) -> SolutionMatch:
        match = SolutionMatch(
            company_id=result.company_id,
            opportunity_id=result.opportunity_id,
            primary_service_key=result.primary_service.service.service_key,
            secondary_service_key=(
                result.secondary_service.service.service_key if result.secondary_service else None
            ),
            cross_sell_service_keys=[item.service.service_key for item in result.cross_sell],
            upsell_service_keys=[item.service.service_key for item in result.upsell],
            confidence=result.confidence,
            reasoning=result.reasoning,
            evidence=result.evidence,
        )
        self.session.add(match)
        await self.session.flush()

        for persona in result.buyer_personas:
            self.session.add(
                RevenueBuyerPersona(
                    company_id=result.company_id,
                    solution_match_id=match.id,
                    persona=persona.persona,
                    confidence=persona.confidence,
                    explanation=persona.explanation,
                    evidence=persona.evidence,
                )
            )

        estimate = result.revenue_estimate
        prediction = result.deal_prediction
        self.session.add(
            DealEstimate(
                solution_match_id=match.id,
                company_id=result.company_id,
                opportunity_id=result.opportunity_id,
                project_size=estimate.project_size.value,
                implementation_complexity=estimate.implementation_complexity,
                estimated_budget_range=estimate.estimated_budget_range.value,
                priority_level=prediction.priority_level.value,
                mrr_potential=estimate.mrr_potential,
                one_time_revenue=estimate.one_time_revenue,
                expansion_potential=estimate.expansion_potential,
                renewal_potential=estimate.renewal_potential,
                strategic_account_value=estimate.strategic_account_value,
                revenue_score=prediction.revenue_score,
                urgency=prediction.urgency,
                closing_probability=prediction.closing_probability,
                strategic_importance=prediction.strategic_importance,
                expected_sales_cycle_days=prediction.expected_sales_cycle_days,
                explanation=estimate.explanation,
            )
        )
        self.session.add(
            DealPredictionModel(
                solution_match_id=match.id,
                company_id=result.company_id,
                opportunity_id=result.opportunity_id,
                revenue_score=prediction.revenue_score,
                urgency=prediction.urgency,
                closing_probability=prediction.closing_probability,
                strategic_importance=prediction.strategic_importance,
                customer_lifetime_value=prediction.customer_lifetime_value,
                implementation_complexity=prediction.implementation_complexity,
                priority_level=prediction.priority_level.value,
                expected_sales_cycle_days=prediction.expected_sales_cycle_days,
                explanation=prediction.explanation,
            )
        )
        self.session.add(
            SalesCycle(
                solution_match_id=match.id,
                expected_days=prediction.expected_sales_cycle_days,
                stage_plan=[
                    {"stage": "discovery", "days": 7},
                    {"stage": "proposal", "days": max(14, prediction.expected_sales_cycle_days // 2)},
                    {"stage": "close", "days": prediction.expected_sales_cycle_days},
                ],
            )
        )

        playbook = result.playbook
        self.session.add(
            SalesPlaybook(
                company_id=result.company_id,
                opportunity_id=result.opportunity_id,
                solution_match_id=match.id,
                business_pain=playbook.business_pain,
                recommended_service=playbook.recommended_service,
                why=playbook.why,
                conversation_angle=playbook.conversation_angle,
                decision_maker=playbook.decision_maker,
                expected_outcome=playbook.expected_outcome,
                risk=playbook.risk,
                playbook=playbook.model_dump(mode="json"),
            )
        )
        self.session.add(
            RecommendationHistory(
                solution_match_id=match.id,
                recommendation_type="revenue_recommendation",
                recommendation=result.model_dump(mode="json"),
                evidence=result.evidence,
            )
        )
        self.session.add(
            RevenueHistory(
                solution_match_id=match.id,
                company_id=result.company_id,
                action="revenue_recommendation_created",
                actor="revenue_engine",
                details={
                    "primary_service": result.primary_service.service.service_key,
                    "priority": prediction.priority_level.value,
                    "budget_range": estimate.estimated_budget_range.value,
                },
            )
        )
        for metric_name, metric_value in {
            "processing_latency_ms": result.processing_latency_ms,
            "match_confidence": result.confidence,
            "opportunity_score": float(result.evidence.get("opportunity_score", 0.0)),
            "priority_score": prediction.revenue_score,
        }.items():
            self.session.add(
                RevenueMetric(
                    solution_match_id=match.id,
                    metric_name=metric_name,
                    metric_value=float(metric_value),
                    dimensions={"company_id": str(result.company_id)},
                )
            )
        await self.session.flush()
        await self.session.refresh(match)
        return match

    async def list_opportunities(
        self,
        *,
        priority: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[dict[str, Any]]:
        query = (
            select(SolutionMatch, Opportunity, Company)
            .join(Opportunity, Opportunity.id == SolutionMatch.opportunity_id)
            .join(Company, Company.id == SolutionMatch.company_id)
        )
        if priority:
            query = query.join(DealEstimate, DealEstimate.solution_match_id == SolutionMatch.id).where(
                DealEstimate.priority_level == priority
            )
        result = await self.session.execute(
            query.order_by(Opportunity.opportunity_score.desc(), SolutionMatch.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows: list[dict[str, Any]] = []
        seen: set[UUID] = set()
        for match, opportunity, company in result.all():
            if match.id in seen:
                continue
            seen.add(match.id)
            estimate = await self.latest_estimate(match.id)
            playbook = await self.latest_playbook(match.id)
            personas = list(await self.personas_for_match(match.id))
            rows.append(
                self._company_revenue_payload(
                    company=company,
                    opportunity=opportunity,
                    match=match,
                    estimate=estimate,
                    playbook=playbook,
                    personas=personas,
                )
            )
        return rows

    async def company_revenue(self, company_id: UUID) -> dict[str, Any] | None:
        match = await self.latest_match_for_company(company_id)
        if match is None:
            return None
        company = await self.session.get(Company, company_id)
        opportunity = await self.session.get(Opportunity, match.opportunity_id)
        if company is None or opportunity is None:
            return None
        estimate = await self.latest_estimate(match.id)
        playbook = await self.latest_playbook(match.id)
        personas = list(await self.personas_for_match(match.id))
        return self._company_revenue_payload(
            company=company,
            opportunity=opportunity,
            match=match,
            estimate=estimate,
            playbook=playbook,
            personas=personas,
        )

    async def company_playbook(self, company_id: UUID) -> SalesPlaybook | None:
        match = await self.latest_match_for_company(company_id)
        if match is None:
            return None
        return await self.latest_playbook(match.id)

    async def latest_match_for_company(self, company_id: UUID) -> SolutionMatch | None:
        result = await self.session.execute(
            select(SolutionMatch)
            .where(SolutionMatch.company_id == company_id)
            .order_by(SolutionMatch.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def latest_estimate(self, solution_match_id: UUID) -> DealEstimate | None:
        result = await self.session.execute(
            select(DealEstimate)
            .where(DealEstimate.solution_match_id == solution_match_id)
            .order_by(DealEstimate.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def latest_playbook(self, solution_match_id: UUID) -> SalesPlaybook | None:
        result = await self.session.execute(
            select(SalesPlaybook)
            .where(SalesPlaybook.solution_match_id == solution_match_id)
            .order_by(SalesPlaybook.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def personas_for_match(self, solution_match_id: UUID) -> Sequence[RevenueBuyerPersona]:
        result = await self.session.execute(
            select(RevenueBuyerPersona)
            .where(RevenueBuyerPersona.solution_match_id == solution_match_id)
            .order_by(RevenueBuyerPersona.confidence.desc())
        )
        return result.scalars().all()

    async def list_enabled_services(self) -> Sequence[ServiceDefinition]:
        result = await self.session.execute(
            select(ServiceCatalog)
            .where(ServiceCatalog.enabled.is_(True), ServiceCatalog.deleted_at.is_(None))
            .order_by(ServiceCatalog.name.asc())
        )
        services = [
            ServiceDefinition(
                service_key=item.service_key,
                name=item.name,
                category=item.category_key,
                base_price=item.base_price,
                monthly_price=item.monthly_price,
                complexity=item.complexity,
                matching_terms=list(item.matching_terms),
                target_pains=list(item.target_pains),
                target_industries=list(item.target_industries),
                enabled=item.enabled,
            )
            for item in result.scalars().all()
        ]
        return services or default_service_catalog()

    async def ensure_services_seeded(self) -> None:
        existing = await self.session.execute(select(func.count(ServiceCatalog.id)))
        if int(existing.scalar_one() or 0) > 0:
            return
        for service in default_service_catalog():
            self.session.add(
                ServiceCatalog(
                    service_key=service.service_key,
                    name=service.name,
                    category_key=service.category,
                    base_price=service.base_price,
                    monthly_price=service.monthly_price,
                    complexity=service.complexity,
                    matching_terms=service.matching_terms,
                    target_pains=service.target_pains,
                    target_industries=service.target_industries,
                    enabled=service.enabled,
                )
            )
        existing_rules = await self.session.execute(select(func.count(ServiceRule.id)))
        if int(existing_rules.scalar_one() or 0) == 0:
            for rule in default_service_rules():
                conditions = rule["conditions"]
                self.session.add(
                    ServiceRule(
                        service_key=str(rule["service_key"]),
                        rule_key=str(rule["rule_key"]),
                        version=int(rule["version"]),
                        enabled=bool(rule["enabled"]),
                        priority=int(rule["priority"]),
                        conditions=conditions if isinstance(conditions, dict) else {},
                        weight=float(rule["weight"]),
                        explanation=str(rule["explanation"]),
                    )
                )
        await self.session.flush()

    async def statistics(self, *, since: datetime) -> dict[str, float | int]:
        result = await self.session.execute(
            select(
                func.count(SolutionMatch.id),
                func.avg(SolutionMatch.confidence),
                func.count(case((DealEstimate.priority_level.in_(["high", "critical"]), 1))),
            )
            .outerjoin(DealEstimate, DealEstimate.solution_match_id == SolutionMatch.id)
            .where(SolutionMatch.created_at >= since)
        )
        row = result.one()
        latency = await self.session.execute(
            select(func.avg(RevenueMetric.metric_value)).where(
                RevenueMetric.metric_name == "processing_latency_ms",
                RevenueMetric.created_at >= since,
            )
        )
        return {
            "recommendations": int(row[0] or 0),
            "average_confidence": round(float(row[1] or 0.0), 4),
            "high_priority_count": int(row[2] or 0),
            "average_latency_ms": round(float(latency.scalar_one() or 0.0), 4),
        }

    async def _latest_profile(self, company_id: UUID) -> CompanyProfile | None:
        result = await self.session.execute(
            select(CompanyProfile)
            .where(CompanyProfile.company_id == company_id)
            .order_by(CompanyProfile.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _pains(self, company_id: UUID) -> Sequence[BusinessPain]:
        result = await self.session.execute(
            select(BusinessPain).where(BusinessPain.company_id == company_id).limit(100)
        )
        return result.scalars().all()

    async def _goals(self, company_id: UUID) -> Sequence[BusinessGoal]:
        result = await self.session.execute(
            select(BusinessGoal).where(BusinessGoal.company_id == company_id).limit(100)
        )
        return result.scalars().all()

    async def _contexts(self, company_id: UUID) -> Sequence[BusinessContext]:
        result = await self.session.execute(
            select(BusinessContext)
            .where(BusinessContext.company_id == company_id)
            .order_by(BusinessContext.created_at.desc())
            .limit(50)
        )
        return result.scalars().all()

    async def _opportunity_evidence(self, opportunity_id: UUID) -> Sequence[OpportunityEvidence]:
        result = await self.session.execute(
            select(OpportunityEvidence)
            .where(OpportunityEvidence.opportunity_id == opportunity_id)
            .order_by(OpportunityEvidence.created_at.desc())
            .limit(100)
        )
        return result.scalars().all()

    async def _knowledge_node_ids(self, normalized_company_name: str) -> Sequence[UUID]:
        result = await self.session.execute(
            select(KnowledgeGraphNode.id)
            .where(
                KnowledgeGraphNode.node_type == "company",
                KnowledgeGraphNode.external_id == normalized_company_name,
            )
            .limit(50)
        )
        return list(result.scalars().all())

    async def _latest_quality_score(self, company_id: UUID) -> float:
        result = await self.session.execute(
            select(QualityReport.overall_quality_score)
            .join(BusinessContext, BusinessContext.quality_report_id == QualityReport.id)
            .where(BusinessContext.company_id == company_id)
            .order_by(QualityReport.created_at.desc())
            .limit(1)
        )
        value = result.scalar_one_or_none()
        return float(value or 50.0)

    def _company_revenue_payload(
        self,
        *,
        company: Company,
        opportunity: Opportunity,
        match: SolutionMatch,
        estimate: DealEstimate | None,
        playbook: SalesPlaybook | None,
        personas: Sequence[RevenueBuyerPersona],
    ) -> dict[str, Any]:
        primary_persona = personas[0] if personas else None
        return {
            "company": {
                "id": company.id,
                "name": company.name,
                "industry": company.industry,
            },
            "opportunity_id": opportunity.id,
            "solution_match_id": match.id,
            "opportunity_score": opportunity.opportunity_score,
            "business_pain": playbook.business_pain if playbook else None,
            "recommended_service": (
                playbook.recommended_service if playbook else match.primary_service_key
            ),
            "secondary_service": match.secondary_service_key,
            "buyer_persona": (
                {
                    "persona": primary_persona.persona,
                    "confidence": primary_persona.confidence,
                    "explanation": primary_persona.explanation,
                }
                if primary_persona
                else None
            ),
            "buyer_personas": [
                {
                    "persona": item.persona,
                    "confidence": item.confidence,
                    "explanation": item.explanation,
                }
                for item in personas
            ],
            "estimated_budget_range": estimate.estimated_budget_range if estimate else None,
            "project_size": estimate.project_size if estimate else None,
            "implementation_complexity": estimate.implementation_complexity if estimate else None,
            "priority": estimate.priority_level if estimate else None,
            "confidence": match.confidence,
            "evidence": match.evidence,
            "reason": match.reasoning,
            "playbook": (
                {
                    "business_pain": playbook.business_pain,
                    "recommended_service": playbook.recommended_service,
                    "why": playbook.why,
                    "conversation_angle": playbook.conversation_angle,
                    "decision_maker": playbook.decision_maker,
                    "expected_outcome": playbook.expected_outcome,
                    "risk": playbook.risk,
                }
                if playbook
                else None
            ),
            "created_at": match.created_at,
        }

    def _inference_dict(self, item: BusinessPain | BusinessGoal) -> dict[str, Any]:
        return {
            "id": str(item.id),
            "category": item.category,
            "value": item.value,
            "confidence": item.confidence,
        }

    def _context_dict(self, item: BusinessContext) -> dict[str, Any]:
        return {
            "id": str(item.id),
            "confidence": item.confidence,
            "budget_probability": item.budget_probability,
            "support_pressure": item.support_pressure,
            "operational_pressure": item.operational_pressure,
            "sales_pressure": item.sales_pressure,
            "ai_readiness": item.ai_readiness,
            "automation_readiness": item.automation_readiness,
            "growth_stage": item.growth_stage,
        }

    def _evidence_dict(self, item: OpportunityEvidence) -> dict[str, Any]:
        return {
            "id": str(item.id),
            "source_type": item.source_type,
            "category": item.category,
            "summary": item.summary,
            "confidence": item.confidence,
            "polarity": item.polarity,
        }
