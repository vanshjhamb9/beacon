from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import case, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.context import (
    BusinessContext,
    BusinessGoal,
    BusinessImpact,
    BusinessPain,
    BusinessTrigger,
    CompanyProfile,
    ContextEvidence,
    ContextFeedback,
    ContextHistory,
    DecisionSignal,
    TechnologySignal,
)
from app.models.intelligence import ClassifiedSignal, Company, CompanyTimeline, KnowledgeGraphNode
from app.models.quality import QualityReport
from app.models.raw_event import RawEvent
from context_engine.models import BusinessContextInput, BusinessContextResult, CompanyDNAResult


class ContextRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def has_context_for_signal(self, classified_signal_id: UUID) -> bool:
        result = await self.session.execute(
            select(BusinessContext.id)
            .where(BusinessContext.classified_signal_id == classified_signal_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def pending_context_inputs(self, *, limit: int = 100) -> Sequence[BusinessContextInput]:
        context_exists = exists().where(
            BusinessContext.classified_signal_id == ClassifiedSignal.id
        )
        result = await self.session.execute(
            select(ClassifiedSignal, Company, RawEvent, QualityReport)
            .join(Company, Company.id == ClassifiedSignal.company_id)
            .join(RawEvent, RawEvent.id == ClassifiedSignal.event_id)
            .join(QualityReport, QualityReport.raw_event_id == RawEvent.id)
            .where(QualityReport.decision.in_(("accept", "review")), ~context_exists)
            .order_by(ClassifiedSignal.created_at)
            .limit(limit)
        )
        items: list[BusinessContextInput] = []
        for signal, company, raw_event, quality_report in result.all():
            timeline_id = await self._timeline_id(company.id, raw_event.id, signal.category)
            graph_ids = await self._knowledge_node_ids(company.normalized_name)
            items.append(
                BusinessContextInput(
                    company_id=company.id,
                    company_name=company.name,
                    classified_signal_id=signal.id,
                    raw_event_id=raw_event.id,
                    category=signal.category,
                    subcategory=signal.subcategory,
                    signal_confidence=signal.overall_confidence,
                    business_function=signal.business_function,
                    urgency=signal.urgency,
                    polarity=signal.positive_or_negative,
                    title=raw_event.title,
                    content=raw_event.content,
                    source=raw_event.source,
                    published_at=raw_event.published_at,
                    quality_report_id=quality_report.id,
                    quality_score=quality_report.overall_quality_score,
                    timeline_item_id=timeline_id,
                    knowledge_node_ids=graph_ids,
                    company_attributes={
                        **company.attributes,
                        "industry": company.industry,
                        "signal_frequency": company.signal_frequency,
                    },
                    signal_evidence=signal.evidence,
                )
            )
        return items

    async def store_context(
        self,
        context: BusinessContextResult,
        dna: CompanyDNAResult,
    ) -> BusinessContext:
        model = BusinessContext(
            company_id=context.company_id,
            classified_signal_id=context.classified_signal_id,
            raw_event_id=context.raw_event_id,
            quality_report_id=context.evidence.quality_references[0],
            business_urgency=context.business_urgency,
            buying_stage=context.buying_stage.value,
            decision_stage=context.decision_stage.value,
            growth_stage=context.growth_stage.value,
            digital_maturity=context.digital_maturity,
            ai_readiness=context.ai_readiness,
            automation_readiness=context.automation_readiness,
            budget_probability=context.budget_probability,
            technology_maturity=context.technology_maturity,
            expansion_probability=context.expansion_probability,
            operational_pressure=context.operational_pressure,
            customer_experience_pressure=context.customer_experience_pressure,
            support_pressure=context.support_pressure,
            engineering_pressure=context.engineering_pressure,
            marketing_pressure=context.marketing_pressure,
            sales_pressure=context.sales_pressure,
            confidence=context.confidence,
            processing_time_ms=context.processing_time_ms,
            evidence=context.evidence.model_dump(mode="json"),
        )
        self.session.add(model)
        await self.session.flush()

        await self._store_inferences(model.id, context)
        await self._store_decision_signal(model.id, context)
        await self._store_technology_signals(model.id, dna)
        await self._store_company_profile(model.id, dna)
        await self._store_evidence(model.id, context)
        self.session.add(
            ContextHistory(
                company_id=context.company_id,
                business_context_id=model.id,
                action="context_created",
                actor="context_engine",
                details={"classified_signal_id": str(context.classified_signal_id)},
            )
        )
        await self.session.flush()
        await self.session.refresh(model)
        return model

    async def latest_company_contexts(self, company_id: UUID, *, limit: int = 100) -> Sequence[BusinessContext]:
        result = await self.session.execute(
            select(BusinessContext)
            .where(BusinessContext.company_id == company_id)
            .order_by(BusinessContext.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def latest_company_profile(self, company_id: UUID) -> CompanyProfile | None:
        result = await self.session.execute(
            select(CompanyProfile)
            .where(CompanyProfile.company_id == company_id)
            .order_by(CompanyProfile.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def company_pains(self, company_id: UUID, *, limit: int = 100) -> Sequence[BusinessPain]:
        result = await self.session.execute(
            select(BusinessPain)
            .where(BusinessPain.company_id == company_id)
            .order_by(BusinessPain.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def company_goals(self, company_id: UUID, *, limit: int = 100) -> Sequence[BusinessGoal]:
        result = await self.session.execute(
            select(BusinessGoal)
            .where(BusinessGoal.company_id == company_id)
            .order_by(BusinessGoal.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def company_evidence(self, company_id: UUID, *, limit: int = 200) -> Sequence[ContextEvidence]:
        result = await self.session.execute(
            select(ContextEvidence)
            .join(BusinessContext, BusinessContext.id == ContextEvidence.business_context_id)
            .where(BusinessContext.company_id == company_id)
            .order_by(ContextEvidence.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def add_feedback(
        self,
        *,
        business_context_id: UUID,
        reviewer: str,
        review_outcome: str,
        corrected_fields: dict[str, Any],
        ground_truth: dict[str, Any],
        notes: str | None,
    ) -> ContextFeedback:
        context = await self.session.get(BusinessContext, business_context_id)
        if context is None:
            raise LookupError("Business context was not found.")
        feedback = ContextFeedback(
            business_context_id=business_context_id,
            reviewer=reviewer,
            review_outcome=review_outcome,
            corrected_fields=corrected_fields,
            ground_truth=ground_truth,
            notes=notes,
        )
        self.session.add(feedback)
        self.session.add(
            ContextHistory(
                company_id=context.company_id,
                business_context_id=business_context_id,
                action="context_reviewed",
                actor=reviewer,
                details={"review_outcome": review_outcome, "corrected_fields": corrected_fields},
            )
        )
        await self.session.flush()
        await self.session.refresh(feedback)
        return feedback

    async def statistics(self, *, since: datetime) -> dict[str, float | int]:
        result = await self.session.execute(
            select(
                func.count(BusinessContext.id),
                func.avg(BusinessContext.confidence),
                func.avg(BusinessContext.processing_time_ms),
                func.avg(BusinessContext.ai_readiness),
                func.avg(BusinessContext.automation_readiness),
            ).where(BusinessContext.created_at >= since)
        )
        row = result.one()
        pain_result = await self.session.execute(
            select(func.count(BusinessPain.id)).where(BusinessPain.created_at >= since)
        )
        tech_result = await self.session.execute(
            select(func.count(TechnologySignal.id)).where(TechnologySignal.created_at >= since)
        )
        dna_result = await self.session.execute(
            select(func.avg(CompanyProfile.completeness_score)).where(CompanyProfile.created_at >= since)
        )
        feedback_result = await self.session.execute(
            select(
                func.count(ContextFeedback.id),
                func.sum(case((ContextFeedback.review_outcome.in_(["accepted", "correct"]), 1), else_=0)),
            ).where(ContextFeedback.created_at >= since)
        )
        feedback_count, positive_feedback = feedback_result.one()
        context_accuracy = (
            float(positive_feedback or 0) / float(feedback_count) * 100.0
            if int(feedback_count or 0) > 0
            else 0.0
        )
        return {
            "contexts": int(row[0] or 0),
            "context_accuracy": round(context_accuracy, 4),
            "inference_confidence": round(float(row[1] or 0.0), 4),
            "reasoning_latency_ms": round(float(row[2] or 0.0), 4),
            "average_ai_readiness": round(float(row[3] or 0.0), 4),
            "average_automation_readiness": round(float(row[4] or 0.0), 4),
            "pain_detection_rate": int(pain_result.scalar_one() or 0),
            "technology_detection_rate": int(tech_result.scalar_one() or 0),
            "company_dna_completeness": round(float(dna_result.scalar_one() or 0.0), 4),
        }

    async def _timeline_id(self, company_id: UUID, raw_event_id: UUID, signal_type: str) -> UUID | None:
        result = await self.session.execute(
            select(CompanyTimeline.id)
            .where(
                CompanyTimeline.company_id == company_id,
                CompanyTimeline.event_id == raw_event_id,
                CompanyTimeline.signal_type == signal_type,
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _knowledge_node_ids(self, normalized_company_name: str) -> list[UUID]:
        result = await self.session.execute(
            select(KnowledgeGraphNode.id)
            .where(KnowledgeGraphNode.node_type == "company", KnowledgeGraphNode.external_id == normalized_company_name)
            .limit(10)
        )
        return list(result.scalars().all())

    async def _store_inferences(self, context_id: UUID, context: BusinessContextResult) -> None:
        mapping = [
            (BusinessPain, context.business_pain),
            (BusinessGoal, context.business_goal),
            (BusinessTrigger, context.business_trigger),
            (BusinessImpact, context.business_impact),
        ]
        for model, inference in mapping:
            self.session.add(
                model(
                    company_id=context.company_id,
                    business_context_id=context_id,
                    category=inference.category,
                    value=inference.value,
                    confidence=inference.confidence,
                    evidence=inference.evidence.model_dump(mode="json"),
                )
            )

    async def _store_decision_signal(self, context_id: UUID, context: BusinessContextResult) -> None:
        budget_range = "high" if context.budget_probability >= 70 else "medium" if context.budget_probability >= 45 else "low"
        self.session.add(
            DecisionSignal(
                company_id=context.company_id,
                business_context_id=context_id,
                buying_stage=context.buying_stage.value,
                decision_stage=context.decision_stage.value,
                decision_maker_type="functional_leader",
                implementation_complexity="high" if context.technology_maturity >= 70 else "medium",
                potential_budget_range=budget_range,
                implementation_urgency=context.business_urgency,
                confidence=context.confidence,
                evidence=context.evidence.model_dump(mode="json"),
            )
        )

    async def _store_technology_signals(self, context_id: UUID, dna: CompanyDNAResult) -> None:
        for technology in dna.technology_stack:
            self.session.add(
                TechnologySignal(
                    company_id=dna.company_id,
                    business_context_id=context_id,
                    technology=technology,
                    category="detected_stack",
                    maturity_score=dna.technology_maturity,
                    adoption_signal="mentioned",
                    confidence=dna.evidence.confidence_breakdown.get("context_confidence", 0.0),
                    evidence=dna.evidence.model_dump(mode="json"),
                )
            )

    async def _store_company_profile(self, context_id: UUID, dna: CompanyDNAResult) -> None:
        self.session.add(
            CompanyProfile(
                company_id=dna.company_id,
                business_context_id=context_id,
                industry=dna.industry,
                business_model=dna.business_model,
                company_stage=dna.company_stage.value,
                growth_pattern=dna.growth_pattern,
                technology_stack=dna.technology_stack,
                digital_maturity=dna.digital_maturity,
                ai_adoption=dna.ai_adoption,
                automation_adoption=dna.automation_adoption,
                hiring_pattern=dna.hiring_pattern,
                expansion_pattern=dna.expansion_pattern,
                innovation_score=dna.innovation_score,
                support_maturity=dna.support_maturity,
                operational_maturity=dna.operational_maturity,
                technology_maturity=dna.technology_maturity,
                customer_maturity=dna.customer_maturity,
                completeness_score=dna.completeness_score,
                evidence=dna.evidence.model_dump(mode="json"),
            )
        )

    async def _store_evidence(self, context_id: UUID, context: BusinessContextResult) -> None:
        for raw_event_id in context.evidence.source_events:
            self.session.add(ContextEvidence(business_context_id=context_id, evidence_type="source_event", reference_id=raw_event_id, confidence=context.confidence, details={}))
        for timeline_id in context.evidence.timeline_references:
            self.session.add(ContextEvidence(business_context_id=context_id, evidence_type="timeline", reference_id=timeline_id, confidence=context.confidence, details={}))
        for node_id in context.evidence.knowledge_graph_references:
            self.session.add(ContextEvidence(business_context_id=context_id, evidence_type="knowledge_graph", reference_id=node_id, confidence=context.confidence, details={}))
        for quality_id in context.evidence.quality_references:
            self.session.add(ContextEvidence(business_context_id=context_id, evidence_type="quality", reference_id=quality_id, confidence=context.confidence, details=context.evidence.confidence_breakdown))
        for rule_key in context.evidence.rule_references:
            self.session.add(ContextEvidence(business_context_id=context_id, evidence_type="rule", reference_key=rule_key, confidence=context.confidence, details={}))
