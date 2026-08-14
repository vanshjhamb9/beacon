from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.context import CompanyProfile, TechnologySignal
from app.models.decision import DecisionDiscoveryReport, DecisionMaker
from app.models.intelligence import Company, CompanyTimeline
from app.models.opportunity import Opportunity
from app.models.outcomes import (
    CollectorAccuracy,
    ContactAttempt,
    CustomerFeedback,
    Deal,
    IndustryAccuracy,
    LearningMetric,
    Meeting,
    OpportunityOutcome,
    PersonaAccuracy,
    PredictionAccuracy,
    Proposal,
    ServiceAccuracy,
)
from app.models.revenue import RevenueBuyerPersona, SalesPlaybook, SolutionMatch
from outcome_intelligence.metrics.lifecycle import normalize_stage
from outcome_intelligence.models.types import (
    AccuracyMetric,
    LearningRecommendation,
    OutcomeDashboard,
    OutcomeLifecycle,
    OutcomeUpdateInput,
)


class OutcomeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def update_outcome(self, payload: OutcomeUpdateInput) -> dict[str, Any]:
        opportunity = await self.session.get(Opportunity, payload.opportunity_id)
        if opportunity is None:
            raise ValueError(f"Opportunity {payload.opportunity_id} not found")

        company_id = payload.company_id or opportunity.company_id
        stage = normalize_stage(payload.lifecycle_stage.value)
        now = datetime.now(UTC)
        context = await self._prediction_context(opportunity)

        outcome = await self.session.scalar(
            select(OpportunityOutcome).where(OpportunityOutcome.opportunity_id == opportunity.id)
        )
        if outcome is None:
            outcome = OpportunityOutcome(
                opportunity_id=opportunity.id,
                company_id=company_id,
                lifecycle_stage=stage.value,
                opportunity_score=float(opportunity.opportunity_score),
                details={},
            )
            self.session.add(outcome)
            await self.session.flush()

        outcome.company_id = company_id
        outcome.lifecycle_stage = stage.value
        outcome.notes = payload.notes if payload.notes is not None else outcome.notes
        outcome.reason = payload.reason if payload.reason is not None else outcome.reason
        outcome.owner = payload.owner if payload.owner is not None else outcome.owner
        outcome.revenue = payload.revenue if payload.revenue is not None else outcome.revenue
        outcome.close_date = payload.close_date if payload.close_date is not None else outcome.close_date
        outcome.opportunity_score = float(opportunity.opportunity_score)
        outcome.recommended_service = context.get("recommended_service") or outcome.recommended_service
        outcome.buyer_persona = context.get("buyer_persona") or outcome.buyer_persona
        outcome.industry = context.get("industry") or outcome.industry
        outcome.collector = context.get("collector") or outcome.collector
        outcome.technology = context.get("technology") or outcome.technology
        outcome.decision_maker_role = context.get("decision_maker_role") or outcome.decision_maker_role
        details = dict(outcome.details or {})
        details.update(payload.metadata)
        details["actor"] = payload.actor
        details["last_stage_at"] = now.isoformat()
        outcome.details = details

        if stage in {
            OutcomeLifecycle.CONTACTED,
            OutcomeLifecycle.REPLIED,
            OutcomeLifecycle.MEETING_SCHEDULED,
            OutcomeLifecycle.QUALIFIED,
            OutcomeLifecycle.PROPOSAL_SENT,
            OutcomeLifecycle.NEGOTIATION,
            OutcomeLifecycle.WON,
        }:
            outcome.contacted_at = payload.contacted_at or outcome.contacted_at or now
        if stage in {
            OutcomeLifecycle.REPLIED,
            OutcomeLifecycle.MEETING_SCHEDULED,
            OutcomeLifecycle.QUALIFIED,
            OutcomeLifecycle.PROPOSAL_SENT,
            OutcomeLifecycle.NEGOTIATION,
            OutcomeLifecycle.WON,
        }:
            outcome.replied_at = payload.replied_at or outcome.replied_at or now
        if stage in {
            OutcomeLifecycle.MEETING_SCHEDULED,
            OutcomeLifecycle.QUALIFIED,
            OutcomeLifecycle.PROPOSAL_SENT,
            OutcomeLifecycle.NEGOTIATION,
            OutcomeLifecycle.WON,
        }:
            outcome.meeting_at = payload.meeting_at or outcome.meeting_at or now
        if stage in {
            OutcomeLifecycle.PROPOSAL_SENT,
            OutcomeLifecycle.NEGOTIATION,
            OutcomeLifecycle.WON,
        }:
            outcome.proposal_at = payload.proposal_at or outcome.proposal_at or now
        if stage == OutcomeLifecycle.WON:
            outcome.close_date = payload.close_date or outcome.close_date or now
            if payload.deal_value is not None:
                outcome.revenue = payload.deal_value
            elif payload.revenue is not None:
                outcome.revenue = payload.revenue
        if stage == OutcomeLifecycle.LOST:
            outcome.close_date = payload.close_date or outcome.close_date or now

        await self._append_lifecycle_artifacts(outcome, payload, stage, now)
        await self.session.flush()
        return self._serialize_outcome(outcome)

    async def outcome_records(self, *, limit: int = 5000) -> Sequence[dict[str, Any]]:
        result = await self.session.execute(
            select(OpportunityOutcome).order_by(OpportunityOutcome.updated_at.desc()).limit(limit)
        )
        rows = result.scalars().all()
        records: list[dict[str, Any]] = []
        for row in rows:
            item = self._serialize_outcome(row)
            item["deal_value"] = row.revenue
            item["proposal_value"] = (row.details or {}).get("proposal_value")
            records.append(item)
        return records

    async def company_outcomes(self, company_id: UUID) -> dict[str, Any]:
        company = await self.session.get(Company, company_id)
        if company is None:
            raise ValueError(f"Company {company_id} not found")

        outcomes = (
            await self.session.execute(
                select(OpportunityOutcome)
                .where(OpportunityOutcome.company_id == company_id)
                .order_by(OpportunityOutcome.updated_at.desc())
            )
        ).scalars().all()
        contacts = (
            await self.session.execute(
                select(ContactAttempt)
                .where(ContactAttempt.company_id == company_id)
                .order_by(ContactAttempt.created_at.desc())
            )
        ).scalars().all()
        meetings = (
            await self.session.execute(
                select(Meeting).where(Meeting.company_id == company_id).order_by(Meeting.scheduled_at.desc())
            )
        ).scalars().all()
        proposals = (
            await self.session.execute(
                select(Proposal).where(Proposal.company_id == company_id).order_by(Proposal.sent_at.desc())
            )
        ).scalars().all()
        deals = (
            await self.session.execute(
                select(Deal).where(Deal.company_id == company_id).order_by(Deal.created_at.desc())
            )
        ).scalars().all()
        feedback = (
            await self.session.execute(
                select(CustomerFeedback)
                .where(CustomerFeedback.company_id == company_id)
                .order_by(CustomerFeedback.created_at.desc())
            )
        ).scalars().all()

        won_revenue = sum(float(item.value or 0.0) for item in deals if item.status == "won")
        return {
            "company_id": company_id,
            "company_name": company.name,
            "outcomes": [self._serialize_outcome(item) for item in outcomes],
            "contact_attempts": [self._serialize_contact(item) for item in contacts],
            "meetings": [self._serialize_meeting(item) for item in meetings],
            "proposals": [self._serialize_proposal(item) for item in proposals],
            "deals": [self._serialize_deal(item) for item in deals],
            "feedback": [self._serialize_feedback(item) for item in feedback],
            "totals": {
                "outcomes": len(outcomes),
                "contact_attempts": len(contacts),
                "meetings": len(meetings),
                "proposals": len(proposals),
                "deals": len(deals),
                "won_revenue": round(won_revenue, 4),
            },
        }

    async def persist_dashboard_metrics(self, dashboard: OutcomeDashboard) -> None:
        for metric in dashboard.prediction_accuracy:
            self.session.add(self._accuracy_row(PredictionAccuracy, "metric_key", metric))
        for metric in dashboard.service_accuracy:
            self.session.add(self._accuracy_row(ServiceAccuracy, "service_key", metric))
        for metric in dashboard.collector_accuracy:
            self.session.add(self._accuracy_row(CollectorAccuracy, "collector", metric))
        for metric in dashboard.persona_accuracy:
            self.session.add(self._accuracy_row(PersonaAccuracy, "persona", metric))
        for metric in dashboard.industry_accuracy:
            self.session.add(self._accuracy_row(IndustryAccuracy, "industry", metric))
        for recommendation in dashboard.learning_recommendations:
            self.session.add(self._learning_row(recommendation))
        await self.session.flush()

    async def _append_lifecycle_artifacts(
        self,
        outcome: OpportunityOutcome,
        payload: OutcomeUpdateInput,
        stage: OutcomeLifecycle,
        now: datetime,
    ) -> None:
        if stage in {OutcomeLifecycle.CONTACTED, OutcomeLifecycle.REPLIED}:
            self.session.add(
                ContactAttempt(
                    opportunity_id=outcome.opportunity_id,
                    company_id=outcome.company_id,
                    outcome_id=outcome.id,
                    channel=payload.channel or "email",
                    owner=payload.owner,
                    notes=payload.notes,
                    attempted_at=payload.contacted_at or now,
                    replied=stage == OutcomeLifecycle.REPLIED,
                    details={"actor": payload.actor},
                )
            )
        if stage == OutcomeLifecycle.MEETING_SCHEDULED:
            self.session.add(
                Meeting(
                    opportunity_id=outcome.opportunity_id,
                    company_id=outcome.company_id,
                    outcome_id=outcome.id,
                    meeting_type=payload.meeting_type or "discovery",
                    owner=payload.owner,
                    notes=payload.notes,
                    scheduled_at=payload.meeting_at or now,
                    completed=False,
                    details={"actor": payload.actor},
                )
            )
        if stage in {OutcomeLifecycle.PROPOSAL_SENT, OutcomeLifecycle.NEGOTIATION}:
            value = payload.proposal_value
            if value is not None:
                details = dict(outcome.details or {})
                details["proposal_value"] = value
                outcome.details = details
            self.session.add(
                Proposal(
                    opportunity_id=outcome.opportunity_id,
                    company_id=outcome.company_id,
                    outcome_id=outcome.id,
                    value=value,
                    owner=payload.owner,
                    notes=payload.notes,
                    sent_at=payload.proposal_at or now,
                    status="sent" if stage == OutcomeLifecycle.PROPOSAL_SENT else "negotiation",
                    details={"actor": payload.actor},
                )
            )
        if stage in {OutcomeLifecycle.WON, OutcomeLifecycle.LOST}:
            value = float(payload.deal_value if payload.deal_value is not None else (payload.revenue or outcome.revenue or 0.0))
            self.session.add(
                Deal(
                    opportunity_id=outcome.opportunity_id,
                    company_id=outcome.company_id,
                    outcome_id=outcome.id,
                    value=value,
                    currency="USD",
                    owner=payload.owner,
                    status=stage.value,
                    closed_at=payload.close_date or now,
                    notes=payload.notes,
                    details={"reason": payload.reason, "actor": payload.actor},
                )
            )
        if payload.feedback_score is not None or payload.feedback_text:
            self.session.add(
                CustomerFeedback(
                    opportunity_id=outcome.opportunity_id,
                    company_id=outcome.company_id,
                    outcome_id=outcome.id,
                    score=payload.feedback_score,
                    feedback_text=payload.feedback_text,
                    owner=payload.owner,
                    details={"actor": payload.actor, "stage": stage.value},
                )
            )

    async def _prediction_context(self, opportunity: Opportunity) -> dict[str, Any | None]:
        playbook = await self.session.scalar(
            select(SalesPlaybook)
            .where(SalesPlaybook.opportunity_id == opportunity.id)
            .order_by(SalesPlaybook.created_at.desc())
            .limit(1)
        )
        solution = await self.session.scalar(
            select(SolutionMatch)
            .where(SolutionMatch.opportunity_id == opportunity.id)
            .order_by(SolutionMatch.created_at.desc())
            .limit(1)
        )
        persona = None
        if solution is not None:
            persona = await self.session.scalar(
                select(RevenueBuyerPersona)
                .where(RevenueBuyerPersona.solution_match_id == solution.id)
                .order_by(RevenueBuyerPersona.confidence.desc())
                .limit(1)
            )
        company = await self.session.get(Company, opportunity.company_id)
        profile = await self.session.scalar(
            select(CompanyProfile)
            .where(CompanyProfile.company_id == opportunity.company_id)
            .order_by(CompanyProfile.created_at.desc())
            .limit(1)
        )
        tech = await self.session.scalar(
            select(TechnologySignal)
            .where(TechnologySignal.company_id == opportunity.company_id)
            .order_by(TechnologySignal.created_at.desc())
            .limit(1)
        )
        timeline = await self.session.scalar(
            select(CompanyTimeline)
            .where(CompanyTimeline.company_id == opportunity.company_id)
            .order_by(CompanyTimeline.timestamp.desc())
            .limit(1)
        )
        discovery = await self.session.scalar(
            select(DecisionDiscoveryReport)
            .where(DecisionDiscoveryReport.opportunity_id == opportunity.id)
            .order_by(DecisionDiscoveryReport.created_at.desc())
            .limit(1)
        )
        maker = None
        if discovery is not None:
            maker = await self.session.scalar(
                select(DecisionMaker)
                .where(DecisionMaker.discovery_report_id == discovery.id, DecisionMaker.is_primary.is_(True))
                .limit(1)
            )

        technology = None
        if tech is not None:
            technology = tech.technology
        elif profile is not None and profile.technology_stack:
            technology = str(profile.technology_stack[0])

        return {
            "recommended_service": (
                (playbook.recommended_service if playbook else None)
                or (solution.primary_service_key if solution else None)
                or (discovery.recommended_service if discovery else None)
            ),
            "buyer_persona": (
                (persona.persona if persona else None)
                or (playbook.decision_maker if playbook else None)
                or (discovery.primary_decision_maker_role if discovery else None)
            ),
            "industry": (profile.industry if profile and profile.industry else None)
            or (company.industry if company else None),
            "collector": timeline.source if timeline else None,
            "technology": technology,
            "decision_maker_role": (
                (maker.role if maker else None)
                or (discovery.primary_decision_maker_role if discovery else None)
                or (playbook.decision_maker if playbook else None)
            ),
        }

    def _accuracy_row(self, model: type[Any], key_field: str, metric: AccuracyMetric) -> Any:
        return model(
            **{
                key_field: metric.key,
                "sample_size": metric.sample_size,
                "accuracy_score": metric.accuracy_score,
                "precision": metric.precision,
                "recall": metric.recall,
                "average_prediction_error": metric.average_prediction_error,
                "details": metric.details | {"category": metric.category},
            }
        )

    def _learning_row(self, recommendation: LearningRecommendation) -> LearningMetric:
        return LearningMetric(
            area=recommendation.area,
            target_key=recommendation.target_key,
            recommendation=recommendation.recommendation,
            reason=recommendation.reason,
            expected_impact=recommendation.expected_impact,
            confidence=recommendation.confidence,
            requires_approval=True,
            evidence=recommendation.evidence,
        )

    def _serialize_outcome(self, row: OpportunityOutcome) -> dict[str, Any]:
        return {
            "id": row.id,
            "opportunity_id": row.opportunity_id,
            "company_id": row.company_id,
            "lifecycle_stage": row.lifecycle_stage,
            "notes": row.notes,
            "reason": row.reason,
            "owner": row.owner,
            "revenue": row.revenue,
            "close_date": row.close_date,
            "contacted_at": row.contacted_at,
            "replied_at": row.replied_at,
            "meeting_at": row.meeting_at,
            "proposal_at": row.proposal_at,
            "opportunity_score": row.opportunity_score,
            "recommended_service": row.recommended_service,
            "buyer_persona": row.buyer_persona,
            "industry": row.industry,
            "collector": row.collector,
            "technology": row.technology,
            "decision_maker_role": row.decision_maker_role,
            "details": row.details or {},
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    def _serialize_contact(self, row: ContactAttempt) -> dict[str, Any]:
        return {
            "id": row.id,
            "opportunity_id": row.opportunity_id,
            "channel": row.channel,
            "owner": row.owner,
            "notes": row.notes,
            "attempted_at": row.attempted_at,
            "replied": row.replied,
            "details": row.details or {},
        }

    def _serialize_meeting(self, row: Meeting) -> dict[str, Any]:
        return {
            "id": row.id,
            "opportunity_id": row.opportunity_id,
            "meeting_type": row.meeting_type,
            "owner": row.owner,
            "notes": row.notes,
            "scheduled_at": row.scheduled_at,
            "completed": row.completed,
            "details": row.details or {},
        }

    def _serialize_proposal(self, row: Proposal) -> dict[str, Any]:
        return {
            "id": row.id,
            "opportunity_id": row.opportunity_id,
            "value": row.value,
            "owner": row.owner,
            "notes": row.notes,
            "sent_at": row.sent_at,
            "status": row.status,
            "details": row.details or {},
        }

    def _serialize_deal(self, row: Deal) -> dict[str, Any]:
        return {
            "id": row.id,
            "opportunity_id": row.opportunity_id,
            "value": row.value,
            "currency": row.currency,
            "owner": row.owner,
            "status": row.status,
            "closed_at": row.closed_at,
            "notes": row.notes,
            "details": row.details or {},
        }

    def _serialize_feedback(self, row: CustomerFeedback) -> dict[str, Any]:
        return {
            "id": row.id,
            "opportunity_id": row.opportunity_id,
            "score": row.score,
            "feedback_text": row.feedback_text,
            "owner": row.owner,
            "details": row.details or {},
            "created_at": row.created_at,
        }
