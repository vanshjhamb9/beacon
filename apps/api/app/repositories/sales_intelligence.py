from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import CommunicationMessage, ConversationItemRow
from app.models.context import BusinessGoal, BusinessPain, CompanyProfile
from app.models.decision import DecisionMaker
from app.models.enrichment import CompanyJob, CompanyTechnology
from app.models.intelligence import Company
from app.models.opportunity import Opportunity
from app.models.outcomes import Meeting, OpportunityOutcome, Proposal
from app.models.revenue_hunter import RevenueHunterDossier
from app.models.sales_intelligence import (
    SalesIntelligenceSnapshot,
    SalesMemoryEventRow,
    SalesReplyIntelligenceRow,
)
from sales_intelligence.models.types import SalesIntelligenceDecision, SalesIntelligenceInput


class SalesIntelligenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def build_input(
        self,
        company_id: UUID,
        *,
        opportunity_id: UUID | None = None,
    ) -> SalesIntelligenceInput | None:
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

        dossier = await self.session.scalar(
            select(RevenueHunterDossier)
            .where(RevenueHunterDossier.company_id == company_id)
            .order_by(RevenueHunterDossier.created_at.desc())
            .limit(1)
        )
        profile = await self.session.scalar(
            select(CompanyProfile).where(CompanyProfile.company_id == company_id).limit(1)
        )
        pains = list(
            (
                await self.session.execute(
                    select(BusinessPain).where(BusinessPain.company_id == company_id).limit(20)
                )
            ).scalars().all()
        )
        goals = list(
            (
                await self.session.execute(
                    select(BusinessGoal).where(BusinessGoal.company_id == company_id).limit(20)
                )
            ).scalars().all()
        )
        techs = list(
            (
                await self.session.execute(
                    select(CompanyTechnology).where(CompanyTechnology.company_id == company_id).limit(40)
                )
            ).scalars().all()
        )
        jobs = list(
            (
                await self.session.execute(
                    select(CompanyJob).where(CompanyJob.company_id == company_id).limit(40)
                )
            ).scalars().all()
        )
        dms = list(
            (
                await self.session.execute(
                    select(DecisionMaker).where(DecisionMaker.company_id == company_id).limit(20)
                )
            ).scalars().all()
        )

        messages = list(
            (
                await self.session.execute(
                    select(CommunicationMessage)
                    .where(CommunicationMessage.company_id == company_id)
                    .order_by(CommunicationMessage.created_at.desc())
                    .limit(50)
                )
            ).scalars().all()
        )
        emails = [
            {
                "id": str(m.id),
                "subject": m.subject,
                "body": m.body_text,
                "sent_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
            if m.direction == "outbound"
        ]
        replies = [
            {
                "id": str(m.id),
                "subject": m.subject,
                "body": m.body_text,
                "received_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
            if m.direction == "inbound"
        ]
        if not replies:
            items = list(
                (
                    await self.session.execute(
                        select(ConversationItemRow)
                        .where(ConversationItemRow.company_id == company_id)
                        .where(ConversationItemRow.direction == "inbound")
                        .order_by(ConversationItemRow.created_at.desc())
                        .limit(25)
                    )
                ).scalars().all()
            )
            replies = [
                {
                    "id": str(i.id),
                    "subject": i.subject or "",
                    "body": i.body,
                    "received_at": i.created_at.isoformat() if i.created_at else None,
                }
                for i in items
            ]

        meetings = list(
            (
                await self.session.execute(
                    select(Meeting).where(Meeting.company_id == company_id).limit(20)
                )
            ).scalars().all()
        )
        proposals = list(
            (
                await self.session.execute(
                    select(Proposal).where(Proposal.company_id == company_id).limit(20)
                )
            ).scalars().all()
        )
        outcomes = list(
            (
                await self.session.execute(
                    select(OpportunityOutcome)
                    .where(OpportunityOutcome.company_id == company_id)
                    .limit(20)
                )
            ).scalars().all()
        )

        attrs = company.attributes or {}
        employee_count = None
        if attrs.get("employee_count") is not None:
            try:
                employee_count = int(attrs["employee_count"])
            except (TypeError, ValueError):
                employee_count = None

        pain_texts = [f"{p.category}: {p.value}" for p in pains]
        if dossier and dossier.pain_points:
            for pp in dossier.pain_points:
                if isinstance(pp, dict):
                    pain_texts.append(str(pp.get("pain") or pp.get("name") or pp))
                else:
                    pain_texts.append(str(pp))

        funding_days = attrs.get("funding_days_ago")
        try:
            funding_days_ago = int(funding_days) if funding_days is not None else None
        except (TypeError, ValueError):
            funding_days_ago = None

        return SalesIntelligenceInput(
            company_id=company.id,
            company_name=company.name,
            opportunity_id=opportunity.id if opportunity else None,
            industry=company.industry or (dossier.industry if dossier else None) or (profile.industry if profile else None),
            country=attrs.get("country") or (dossier.country if dossier else None),
            employee_count=employee_count,
            funding_stage=attrs.get("funding_stage") or (dossier.funding_stage if dossier else None),
            funding_days_ago=funding_days_ago,
            revenue_band=attrs.get("revenue_band") or (dossier.revenue_band if dossier else None),
            technologies=[t.name for t in techs] or list((profile.technology_stack if profile else []) or []),
            pains=[str(p) for p in pain_texts if p][:30],
            goals=[f"{g.category}: {g.value}" for g in goals][:20],
            signals=list(attrs.get("signals") or [])[:20],
            hiring_roles=[j.title for j in jobs][:20],
            hiring_count=len(jobs),
            decision_makers=[
                {
                    "name": dm.name,
                    "title": dm.role,
                    "email": dm.work_email,
                }
                for dm in dms
            ],
            recommended_service=dossier.recommended_service if dossier else None,
            expected_budget=dossier.expected_budget if dossier else attrs.get("expected_budget"),
            opportunity_score=float(opportunity.opportunity_score) if opportunity else 0.0,
            priority_grade=dossier.priority_grade if dossier else None,
            probability=float(dossier.probability) if dossier else 0.0,
            website_opportunities=list((dossier.website_intelligence or {}).get("opportunities") or []) if dossier else [],
            replies=replies,
            emails=emails,
            meetings=[
                {
                    "title": m.meeting_type or "Meeting",
                    "notes": m.notes or "",
                    "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None,
                }
                for m in meetings
            ],
            proposals=[
                {
                    "title": (p.notes or "Proposal")[:120],
                    "status": p.status,
                    "sent_at": p.sent_at.isoformat() if p.sent_at else None,
                }
                for p in proposals
            ],
            objections_seen=list(attrs.get("objections") or []),
            notes=list(attrs.get("notes") or []),
            outcomes=[
                {
                    "type": o.lifecycle_stage,
                    "status": o.lifecycle_stage,
                    "detail": o.notes or o.reason or "",
                    "occurred_at": o.updated_at.isoformat() if o.updated_at else None,
                }
                for o in outcomes
            ],
            follow_ups=list(attrs.get("follow_ups") or []),
            vendors=list(attrs.get("vendors") or []),
            metadata={"source": "sales_intelligence_repository"},
            now=datetime.now(UTC),
        )

    async def store_decision(self, decision: SalesIntelligenceDecision) -> SalesIntelligenceSnapshot:
        row = SalesIntelligenceSnapshot(
            company_id=decision.company_id,
            opportunity_id=decision.opportunity_id,
            company_name=decision.company_name,
            buying_intent_score=decision.buying_intent.buying_intent_score,
            buying_stage=decision.buying_intent.buying_stage.value,
            urgency=decision.buying_intent.urgency.value,
            budget_probability=decision.buying_intent.budget_probability.value,
            decision_window_days=decision.buying_intent.decision_window_days,
            primary_offer=decision.offer.primary_offer.value,
            expected_value=decision.offer.expected_value,
            deal_probability=decision.score.deal_probability,
            close_probability=decision.score.close_probability,
            sales_health=decision.score.sales_health,
            relationship_health=decision.score.relationship_health,
            competition_risk=decision.score.competition_risk,
            payload=decision.model_dump(mode="json"),
            evidence_chain=list(decision.evidence_chain),
            scoring_version=decision.scoring_version,
            metadata_json={},
        )
        self.session.add(row)
        await self.session.flush()

        for event in decision.memory.events:
            self.session.add(
                SalesMemoryEventRow(
                    company_id=decision.company_id,
                    opportunity_id=decision.opportunity_id,
                    snapshot_id=row.id,
                    event_key=event.event_id,
                    event_type=event.event_type.value,
                    title=event.title,
                    detail=event.detail,
                    occurred_at=event.occurred_at,
                    evidence=list(event.evidence),
                    refs=dict(event.refs),
                    immutable=True,
                )
            )
        for reply in decision.reply_intelligence:
            self.session.add(
                SalesReplyIntelligenceRow(
                    company_id=decision.company_id,
                    opportunity_id=decision.opportunity_id,
                    snapshot_id=row.id,
                    reply_ref=reply.reply_ref,
                    classification=reply.classification.value,
                    best_response=reply.best_response,
                    confidence=reply.confidence,
                    reason=reply.reason,
                    evidence=list(reply.evidence),
                    reply_text="",
                )
            )
        await self.session.flush()
        return row

    async def latest_for_company(self, company_id: UUID) -> SalesIntelligenceSnapshot | None:
        return await self.session.scalar(
            select(SalesIntelligenceSnapshot)
            .where(SalesIntelligenceSnapshot.company_id == company_id)
            .order_by(SalesIntelligenceSnapshot.created_at.desc())
            .limit(1)
        )

    async def latest_for_opportunity(self, opportunity_id: UUID) -> SalesIntelligenceSnapshot | None:
        return await self.session.scalar(
            select(SalesIntelligenceSnapshot)
            .where(SalesIntelligenceSnapshot.opportunity_id == opportunity_id)
            .order_by(SalesIntelligenceSnapshot.created_at.desc())
            .limit(1)
        )

    async def companies_needing_refresh(self, *, limit: int = 50) -> list[UUID]:
        """Companies with recent inbound replies newer than latest SI snapshot."""
        latest = (
            select(
                SalesIntelligenceSnapshot.company_id,
                func.max(SalesIntelligenceSnapshot.created_at).label("created_at"),
            )
            .group_by(SalesIntelligenceSnapshot.company_id)
            .subquery()
        )
        result = await self.session.execute(
            select(CommunicationMessage.company_id)
            .outerjoin(latest, latest.c.company_id == CommunicationMessage.company_id)
            .where(CommunicationMessage.direction == "inbound")
            .where(CommunicationMessage.company_id.is_not(None))
            .where(
                (latest.c.created_at.is_(None)) | (CommunicationMessage.created_at > latest.c.created_at)
            )
            .group_by(CommunicationMessage.company_id)
            .order_by(desc(func.max(CommunicationMessage.created_at)))
            .limit(limit)
        )
        return [row[0] for row in result.all() if row[0] is not None]

    async def dashboard(self, *, limit: int = 50) -> dict[str, Any]:
        latest_ids = (
            select(
                SalesIntelligenceSnapshot.company_id,
                func.max(SalesIntelligenceSnapshot.created_at).label("created_at"),
            )
            .group_by(SalesIntelligenceSnapshot.company_id)
            .subquery()
        )
        rows = list(
            (
                await self.session.execute(
                    select(SalesIntelligenceSnapshot)
                    .join(
                        latest_ids,
                        (SalesIntelligenceSnapshot.company_id == latest_ids.c.company_id)
                        & (SalesIntelligenceSnapshot.created_at == latest_ids.c.created_at),
                    )
                    .order_by(SalesIntelligenceSnapshot.buying_intent_score.desc())
                    .limit(limit)
                )
            ).scalars().all()
        )
        hot = [r for r in rows if r.buying_intent_score >= 70]
        high_close = [r for r in rows if r.close_probability >= 60]
        return {
            "total_evaluated": len(rows),
            "hot_intent": len(hot),
            "high_close_probability": len(high_close),
            "avg_intent": round(sum(r.buying_intent_score for r in rows) / len(rows), 2) if rows else 0.0,
            "avg_deal_probability": round(sum(r.deal_probability for r in rows) / len(rows), 2) if rows else 0.0,
            "top_accounts": [
                {
                    "company_id": str(r.company_id),
                    "company_name": r.company_name,
                    "buying_intent_score": r.buying_intent_score,
                    "buying_stage": r.buying_stage,
                    "urgency": r.urgency,
                    "primary_offer": r.primary_offer,
                    "deal_probability": r.deal_probability,
                    "close_probability": r.close_probability,
                    "expected_value": r.expected_value,
                }
                for r in rows[:25]
            ],
            "scoring_version": "si-v1",
        }
