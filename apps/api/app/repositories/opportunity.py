from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import case, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.context import (
    BusinessContext,
    BusinessGoal,
    BusinessPain,
    CompanyProfile,
    DecisionSignal,
    TechnologySignal,
)
from app.models.intelligence import ClassifiedSignal, Company, CompanyTimeline
from app.models.opportunity import (
    Opportunity,
    OpportunityConflict,
    OpportunityEvidence,
    OpportunityFeedback,
    OpportunityHistory,
    OpportunityLifecycle,
    OpportunityMetric,
    OpportunityRecommendation as OpportunityRecommendationModel,
    OpportunityScore,
    OpportunityTimeline,
)
from opportunity_engine.models import (
    CompanyOpportunityInput,
    OpportunityDecision,
    OpportunityEvidenceItem,
    OpportunityStatus,
)


class OpportunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def pending_company_inputs(self, *, limit: int) -> Sequence[CompanyOpportunityInput]:
        stale_or_missing_opportunity = ~exists().where(
            Opportunity.company_id == BusinessContext.company_id,
            Opportunity.created_at >= BusinessContext.created_at,
        )
        result = await self.session.execute(
            select(Company.id)
            .join(BusinessContext, BusinessContext.company_id == Company.id)
            .where(stale_or_missing_opportunity)
            .group_by(Company.id)
            .order_by(func.max(BusinessContext.created_at).desc())
            .limit(limit)
        )
        inputs: list[CompanyOpportunityInput] = []
        for company_id in result.scalars().all():
            company_input = await self.company_input(company_id)
            if company_input is not None:
                inputs.append(company_input)
        return inputs

    async def company_input(self, company_id: UUID) -> CompanyOpportunityInput | None:
        company = await self.session.get(Company, company_id)
        if company is None:
            return None
        contexts = list(await self._contexts(company_id))
        if not contexts:
            return None
        profile = await self._latest_profile(company_id)
        pains = list(await self._pains(company_id))
        goals = list(await self._goals(company_id))
        technologies = list(await self._technologies(company_id))
        signals = list(await self._signals(company_id))
        timeline = list(await self._timeline(company_id))
        previous = await self.latest_for_company(company_id)
        evidence = self._evidence_items(contexts, pains, goals, technologies, signals, timeline)
        latest_context_at = max(context.created_at for context in contexts)
        return CompanyOpportunityInput(
            company_id=company.id,
            company_name=company.name,
            business_context_ids=[context.id for context in contexts],
            latest_context_at=latest_context_at,
            contexts=[self._context_dict(context) for context in contexts],
            company_profile=self._profile_dict(profile),
            signals=[self._signal_dict(signal) for signal in signals],
            timeline=[self._timeline_dict(item) for item in timeline],
            pains=[self._inference_dict(item) for item in pains],
            goals=[self._inference_dict(item) for item in goals],
            technologies=[self._technology_dict(item) for item in technologies],
            evidence=evidence,
            previous_opportunity_id=previous.id if previous else None,
            previous_score=previous.opportunity_score if previous else None,
            previous_status=OpportunityStatus(previous.status) if previous else None,
        )

    async def store_decision(self, decision: OpportunityDecision) -> Opportunity:
        opportunity = Opportunity(
            company_id=decision.company_id,
            company_name=decision.company_name,
            status=decision.status.value,
            recommendation=decision.recommendation.action.value,
            opportunity_score=decision.opportunity_score,
            confidence_score=decision.confidence_score,
            timing_score=decision.timing_score,
            urgency_score=decision.urgency_score,
            narrative=decision.narrative,
            created_from_context_ids=[str(item) for item in decision.created_from_context_ids],
            score_breakdown={
                score.name: score.model_dump(mode="json") for score in decision.score_breakdown
            },
            delta=decision.delta.model_dump(mode="json"),
        )
        self.session.add(opportunity)
        await self.session.flush()
        self._store_scores(opportunity.id, decision)
        self._store_evidence(opportunity.id, decision)
        self._store_recommendation(opportunity.id, decision)
        self._store_timeline(opportunity.id, decision)
        self._store_conflicts(opportunity.id, decision)
        self._store_lifecycle(opportunity.id, decision)
        self._store_metrics(opportunity.id, decision)
        self.session.add(
            OpportunityHistory(
                opportunity_id=opportunity.id,
                company_id=decision.company_id,
                action="opportunity_scored",
                actor="opportunity_engine",
                details={
                    "status": decision.status.value,
                    "recommendation": decision.recommendation.action.value,
                    "score": decision.opportunity_score,
                    "delta": decision.delta.model_dump(mode="json"),
                },
            )
        )
        await self.session.flush()
        await self.session.refresh(opportunity)
        return opportunity

    async def list_opportunities(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Opportunity]:
        query = select(Opportunity)
        if status:
            query = query.where(Opportunity.status == status)
        result = await self.session.execute(
            query.order_by(Opportunity.opportunity_score.desc(), Opportunity.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_opportunity(self, opportunity_id: UUID) -> Opportunity | None:
        return await self.session.get(Opportunity, opportunity_id)

    async def latest_for_company(self, company_id: UUID) -> Opportunity | None:
        result = await self.session.execute(
            select(Opportunity)
            .where(Opportunity.company_id == company_id)
            .order_by(Opportunity.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def history(self, opportunity_id: UUID) -> Sequence[OpportunityHistory]:
        result = await self.session.execute(
            select(OpportunityHistory)
            .where(OpportunityHistory.opportunity_id == opportunity_id)
            .order_by(OpportunityHistory.created_at.desc())
        )
        return result.scalars().all()

    async def evidence(self, opportunity_id: UUID) -> Sequence[OpportunityEvidence]:
        result = await self.session.execute(
            select(OpportunityEvidence)
            .where(OpportunityEvidence.opportunity_id == opportunity_id)
            .order_by(OpportunityEvidence.created_at.desc())
        )
        return result.scalars().all()

    async def timeline(self, opportunity_id: UUID) -> Sequence[OpportunityTimeline]:
        result = await self.session.execute(
            select(OpportunityTimeline)
            .where(OpportunityTimeline.opportunity_id == opportunity_id)
            .order_by(OpportunityTimeline.created_at.desc())
        )
        return result.scalars().all()

    async def recommendation(self, opportunity_id: UUID) -> OpportunityRecommendationModel | None:
        result = await self.session.execute(
            select(OpportunityRecommendationModel)
            .where(OpportunityRecommendationModel.opportunity_id == opportunity_id)
            .order_by(OpportunityRecommendationModel.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def statistics(self, *, since: datetime) -> dict[str, float | int]:
        result = await self.session.execute(
            select(
                func.count(Opportunity.id),
                func.avg(Opportunity.opportunity_score),
                func.avg(Opportunity.confidence_score),
                func.count(case((Opportunity.status == "high_intent", 1))),
            ).where(Opportunity.created_at >= since)
        )
        row = result.one()
        feedback_result = await self.session.execute(
            select(
                func.count(OpportunityFeedback.id),
                func.sum(case((OpportunityFeedback.review_outcome.in_(["accepted", "correct"]), 1), else_=0)),
            ).where(OpportunityFeedback.created_at >= since)
        )
        feedback_count, positive_feedback = feedback_result.one()
        false_positive_rate = (
            100.0 - (float(positive_feedback or 0) / float(feedback_count) * 100.0)
            if int(feedback_count or 0) > 0
            else 0.0
        )
        return {
            "opportunities": int(row[0] or 0),
            "average_score": round(float(row[1] or 0.0), 4),
            "average_confidence": round(float(row[2] or 0.0), 4),
            "high_intent_count": int(row[3] or 0),
            "false_positive_rate": round(false_positive_rate, 4),
        }

    async def add_feedback(
        self,
        *,
        opportunity_id: UUID,
        reviewer: str,
        review_outcome: str,
        corrected_fields: dict[str, Any],
        outcome_label: str | None,
        notes: str | None,
    ) -> OpportunityFeedback:
        opportunity = await self.get_opportunity(opportunity_id)
        if opportunity is None:
            raise LookupError("Opportunity was not found.")
        feedback = OpportunityFeedback(
            opportunity_id=opportunity_id,
            reviewer=reviewer,
            review_outcome=review_outcome,
            corrected_fields=corrected_fields,
            outcome_label=outcome_label,
            notes=notes,
        )
        self.session.add(feedback)
        self.session.add(
            OpportunityHistory(
                opportunity_id=opportunity_id,
                company_id=opportunity.company_id,
                action="opportunity_reviewed",
                actor=reviewer,
                details={"review_outcome": review_outcome, "outcome_label": outcome_label},
            )
        )
        await self.session.flush()
        await self.session.refresh(feedback)
        return feedback

    async def _contexts(self, company_id: UUID) -> Sequence[BusinessContext]:
        result = await self.session.execute(
            select(BusinessContext)
            .where(BusinessContext.company_id == company_id)
            .order_by(BusinessContext.created_at.desc())
            .limit(100)
        )
        return result.scalars().all()

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

    async def _technologies(self, company_id: UUID) -> Sequence[TechnologySignal]:
        result = await self.session.execute(
            select(TechnologySignal).where(TechnologySignal.company_id == company_id).limit(100)
        )
        return result.scalars().all()

    async def _signals(self, company_id: UUID) -> Sequence[ClassifiedSignal]:
        result = await self.session.execute(
            select(ClassifiedSignal)
            .where(ClassifiedSignal.company_id == company_id)
            .order_by(ClassifiedSignal.created_at.desc())
            .limit(100)
        )
        return result.scalars().all()

    async def _timeline(self, company_id: UUID) -> Sequence[CompanyTimeline]:
        result = await self.session.execute(
            select(CompanyTimeline)
            .where(CompanyTimeline.company_id == company_id)
            .order_by(CompanyTimeline.timestamp.desc())
            .limit(100)
        )
        return result.scalars().all()

    def _evidence_items(
        self,
        contexts: list[BusinessContext],
        pains: list[BusinessPain],
        goals: list[BusinessGoal],
        technologies: list[TechnologySignal],
        signals: list[ClassifiedSignal],
        timeline: list[CompanyTimeline],
    ) -> list[OpportunityEvidenceItem]:
        items: list[OpportunityEvidenceItem] = []
        for context in contexts:
            items.append(
                OpportunityEvidenceItem(
                    source_type="business_context",
                    reference_id=context.id,
                    category=context.growth_stage,
                    summary=context.narrative if hasattr(context, "narrative") else context.business_urgency,
                    confidence=context.confidence,
                    occurred_at=context.created_at,
                    details=context.evidence,
                )
            )
        for pain in pains:
            polarity = "contradicting" if pain.category in {"layoffs", "budget_cuts", "store_closures"} else "supporting"
            items.append(
                OpportunityEvidenceItem(
                    source_type="business_pain",
                    reference_id=pain.id,
                    category=pain.category,
                    summary=pain.value,
                    confidence=pain.confidence,
                    occurred_at=pain.created_at,
                    polarity=polarity,
                    details=pain.evidence,
                )
            )
        for goal in goals:
            items.append(
                OpportunityEvidenceItem(
                    source_type="business_goal",
                    reference_id=goal.id,
                    category=goal.category,
                    summary=goal.value,
                    confidence=goal.confidence,
                    occurred_at=goal.created_at,
                    details=goal.evidence,
                )
            )
        for technology in technologies:
            items.append(
                OpportunityEvidenceItem(
                    source_type="technology_signal",
                    reference_id=technology.id,
                    category=technology.category,
                    summary=technology.technology,
                    confidence=technology.confidence,
                    occurred_at=technology.created_at,
                    details=technology.evidence,
                )
            )
        for signal in signals:
            polarity = "contradicting" if signal.category in {"layoffs", "hiring_freeze", "customer_complaints"} else "supporting"
            items.append(
                OpportunityEvidenceItem(
                    source_type="classified_signal",
                    reference_id=signal.id,
                    category=signal.category,
                    summary=signal.subcategory or signal.category,
                    confidence=signal.overall_confidence,
                    occurred_at=signal.created_at,
                    polarity=polarity,
                    details=signal.evidence,
                )
            )
        for event in timeline:
            items.append(
                OpportunityEvidenceItem(
                    source_type="timeline",
                    reference_id=event.id,
                    category=event.signal_type,
                    summary=event.summary,
                    confidence=event.confidence,
                    occurred_at=event.timestamp,
                    details=event.evidence,
                )
            )
        return items

    def _store_scores(self, opportunity_id: UUID, decision: OpportunityDecision) -> None:
        for component in decision.score_breakdown:
            self.session.add(
                OpportunityScore(
                    opportunity_id=opportunity_id,
                    company_id=decision.company_id,
                    score_name=component.name,
                    score_value=component.value,
                    weight=component.weight,
                    explanation=component.explanation,
                    evidence_ids=[str(item) for item in component.evidence_ids],
                )
            )

    def _store_evidence(self, opportunity_id: UUID, decision: OpportunityDecision) -> None:
        for evidence in decision.evidence:
            self.session.add(
                OpportunityEvidence(
                    opportunity_id=opportunity_id,
                    company_id=decision.company_id,
                    source_type=evidence.source_type,
                    reference_id=evidence.reference_id,
                    category=evidence.category,
                    summary=evidence.summary,
                    confidence=evidence.confidence,
                    polarity=evidence.polarity,
                    weight=evidence.weight,
                    details=evidence.details,
                )
            )

    def _store_recommendation(self, opportunity_id: UUID, decision: OpportunityDecision) -> None:
        self.session.add(
            OpportunityRecommendationModel(
                opportunity_id=opportunity_id,
                company_id=decision.company_id,
                action=decision.recommendation.action.value,
                confidence=decision.recommendation.confidence,
                reasons=decision.recommendation.reasons,
                next_step=decision.recommendation.next_step,
            )
        )

    def _store_timeline(self, opportunity_id: UUID, decision: OpportunityDecision) -> None:
        self.session.add(
            OpportunityTimeline(
                opportunity_id=opportunity_id,
                company_id=decision.company_id,
                event_type="opportunity_scored",
                summary=decision.narrative,
                reference_id=None,
                details=decision.delta.model_dump(mode="json"),
            )
        )

    def _store_conflicts(self, opportunity_id: UUID, decision: OpportunityDecision) -> None:
        for conflict in decision.conflicts:
            self.session.add(
                OpportunityConflict(
                    opportunity_id=opportunity_id,
                    company_id=decision.company_id,
                    conflict_type=conflict.conflict_type,
                    supporting_signal=conflict.supporting_signal,
                    contradicting_signal=conflict.contradicting_signal,
                    severity=conflict.severity,
                    explanation=conflict.explanation,
                    evidence_ids=[str(item) for item in conflict.evidence_ids],
                )
            )

    def _store_lifecycle(self, opportunity_id: UUID, decision: OpportunityDecision) -> None:
        self.session.add(
            OpportunityLifecycle(
                opportunity_id=opportunity_id,
                company_id=decision.company_id,
                from_status=None,
                to_status=decision.status.value,
                reason=decision.recommendation.reasons[0],
                rule_key="lifecycle.score_threshold",
            )
        )

    def _store_metrics(self, opportunity_id: UUID, decision: OpportunityDecision) -> None:
        metrics = {
            "scoring_latency_ms": decision.scoring_latency_ms,
            "decision_latency_ms": decision.decision_latency_ms,
            "opportunity_score": decision.opportunity_score,
            "confidence_score": decision.confidence_score,
        }
        for name, value in metrics.items():
            self.session.add(
                OpportunityMetric(
                    opportunity_id=opportunity_id,
                    metric_name=name,
                    metric_value=value,
                    dimensions={"company_id": str(decision.company_id)},
                )
            )

    def _context_dict(self, context: BusinessContext) -> dict[str, Any]:
        return {
            "id": str(context.id),
            "confidence": context.confidence,
            "budget_probability": context.budget_probability,
            "support_pressure": context.support_pressure,
            "operational_pressure": context.operational_pressure,
            "sales_pressure": context.sales_pressure,
            "ai_readiness": context.ai_readiness,
            "automation_readiness": context.automation_readiness,
        }

    def _profile_dict(self, profile: CompanyProfile | None) -> dict[str, Any]:
        if profile is None:
            return {}
        return {
            "technology_maturity": profile.technology_maturity,
            "ai_adoption": profile.ai_adoption,
            "automation_adoption": profile.automation_adoption,
            "digital_maturity": profile.digital_maturity,
            "company_stage": profile.company_stage,
        }

    def _signal_dict(self, signal: ClassifiedSignal) -> dict[str, Any]:
        return {"id": str(signal.id), "category": signal.category, "confidence": signal.overall_confidence}

    def _timeline_dict(self, item: CompanyTimeline) -> dict[str, Any]:
        return {"id": str(item.id), "signal_type": item.signal_type, "timestamp": item.timestamp.isoformat()}

    def _inference_dict(self, item: BusinessPain | BusinessGoal) -> dict[str, Any]:
        return {"id": str(item.id), "category": item.category, "confidence": item.confidence}

    def _technology_dict(self, item: TechnologySignal) -> dict[str, Any]:
        return {"id": str(item.id), "technology": item.technology, "confidence": item.confidence}
