from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.autonomous_sales_agent import (
    AutonomousSalesAgentRun,
    AutonomousSalesTimelineEvent,
    AutonomousSalesWorkQueueSnapshot,
    AutonomousSalesWorkflowTransition,
)
from app.models.campaign import Campaign
from app.models.decision import DecisionMaker
from app.models.intelligence import Company
from app.models.opportunity import Opportunity
from app.models.outcomes import Meeting, Proposal
from app.models.revenue_hunter import RevenueHunterDossier
from app.models.sales_intelligence import SalesIntelligenceSnapshot
from autonomous_sales_agent.analytics.engine import AsaAnalyticsEngine
from autonomous_sales_agent.models.types import (
    AutonomousSalesAgentDecision,
    AutonomousSalesAgentInput,
    FollowUpConfig,
)


class AutonomousSalesAgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.analytics = AsaAnalyticsEngine()

    async def build_input(self, company_id: UUID) -> AutonomousSalesAgentInput | None:
        company = await self.session.get(Company, company_id)
        if company is None:
            return None

        campaign = await self.session.scalar(
            select(Campaign).where(Campaign.company_id == company_id).order_by(Campaign.created_at.desc()).limit(1)
        )
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
        si = await self.session.scalar(
            select(SalesIntelligenceSnapshot)
            .where(SalesIntelligenceSnapshot.company_id == company_id)
            .order_by(SalesIntelligenceSnapshot.created_at.desc())
            .limit(1)
        )
        dms = list(
            (await self.session.execute(select(DecisionMaker).where(DecisionMaker.company_id == company_id).limit(10)))
            .scalars()
            .all()
        )
        meetings = list(
            (
                await self.session.execute(
                    select(Meeting).where(Meeting.company_id == company_id).order_by(Meeting.created_at.desc()).limit(5)
                )
            )
            .scalars()
            .all()
        )
        proposals = list(
            (
                await self.session.execute(
                    select(Proposal).where(Proposal.company_id == company_id).order_by(Proposal.created_at.desc()).limit(5)
                )
            )
            .scalars()
            .all()
        )

        si_payload = (si.payload if si else {}) or {}
        intent = si_payload.get("buying_intent") or {}
        offer = si_payload.get("offer") or {}
        objections = si_payload.get("objections") or []
        attrs = company.attributes or {}

        pains: list[str] = []
        if dossier and dossier.pain_points:
            for p in dossier.pain_points:
                pains.append(str(p.get("pain") if isinstance(p, dict) else p))

        today = datetime.now(UTC).date()
        meetings_today = []
        for m in meetings:
            scheduled = getattr(m, "scheduled_at", None) or getattr(m, "created_at", None)
            if scheduled and getattr(scheduled, "date", lambda: None)() == today:
                meetings_today.append(
                    {
                        "company_name": company.name,
                        "summary": f"Meeting with {company.name}",
                        "meeting_id": str(m.id),
                    }
                )

        proposal_queue = []
        for p in proposals:
            status = str(getattr(p, "status", "") or "").lower()
            if status in {"draft", "pending", "ready"}:
                proposal_queue.append(
                    {
                        "company_name": company.name,
                        "summary": f"Proposal pending: {getattr(p, 'notes', None) or 'Commercial proposal'}",
                        "proposal_id": str(p.id),
                    }
                )

        email_sent = bool(attrs.get("email_sent")) or (campaign is not None and campaign.status in {"approved", "scheduled", "completed"})
        reply_received = bool(attrs.get("reply_received")) or "reply" in str(attrs.get("recent_activity") or "").lower()
        days_since = int(attrs.get("days_since_last_touch") or (3 if email_sent and not reply_received else 0))

        pending_approvals = []
        if campaign and campaign.status in {"needs_review", "draft"}:
            pending_approvals.append(
                {
                    "company_name": company.name,
                    "summary": f"Approve campaign for {company.name}",
                    "campaign_id": str(campaign.id),
                }
            )

        high_intent = []
        buying = float(intent.get("buying_intent_score") or (si.buying_intent_score if si else 0) or 0)
        if reply_received and buying >= 70:
            high_intent.append(
                {
                    "company_name": company.name,
                    "summary": "High-intent reply awaiting founder response",
                    "intent": buying,
                }
            )

        return AutonomousSalesAgentInput(
            company_id=company.id,
            company_name=company.name,
            industry=company.industry or (dossier.industry if dossier else None),
            company_size=str(attrs.get("company_size") or "") or None,
            stage_hint=str(attrs.get("stage_hint") or "") or None,
            priority_grade=dossier.priority_grade if dossier else None,
            probability=float(dossier.probability) if dossier else float(getattr(opportunity, "opportunity_score", 0) or 0),
            buying_intent_score=buying,
            days_since_last_touch=days_since,
            last_touch_channel=str(attrs.get("last_touch_channel") or "") or None,
            has_decision_makers=bool(dms),
            has_sales_package=bool(attrs.get("has_sales_package")),
            has_campaign=campaign is not None,
            campaign_approved=bool(campaign and campaign.status in {"approved", "scheduled", "completed"}),
            email_sent=email_sent,
            whatsapp_sent=bool(attrs.get("whatsapp_sent")),
            reply_received=reply_received,
            meeting_requested=bool(attrs.get("meeting_requested")),
            meeting_booked=bool(attrs.get("meeting_booked")) or bool(meetings),
            meeting_completed=bool(attrs.get("meeting_completed")) or any(bool(m.completed) for m in meetings),
            proposal_pending=bool(proposal_queue) or bool(attrs.get("proposal_pending")),
            proposal_sent=bool(attrs.get("proposal_sent")) or any(
                str(getattr(p, "status", "")).lower() == "sent" for p in proposals
            ),
            negotiation=bool(attrs.get("negotiation")),
            won=bool(attrs.get("won")),
            lost=bool(attrs.get("lost")),
            decision_makers=[{"name": dm.name, "title": dm.role, "email": dm.work_email} for dm in dms],
            pains=[p for p in pains if p][:10],
            technologies=list(attrs.get("technologies") or [])[:12],
            vendors=list(attrs.get("vendors") or [])[:8],
            objections_seen=[str(o.get("objection") if isinstance(o, dict) else o) for o in objections[:8]],
            recent_activity=list(attrs.get("recent_activity") or [])[:12],
            recommended_service=(dossier.recommended_service if dossier else None) or offer.get("primary_offer"),
            expected_budget=dossier.expected_budget if dossier else offer.get("expected_value"),
            founder_notes=list(attrs.get("founder_notes") or []),
            meetings_today=meetings_today,
            pending_approvals=pending_approvals,
            high_intent_replies=high_intent,
            proposal_queue=proposal_queue,
            negotiation_queue=list(attrs.get("negotiation_queue") or []),
            follow_up_config=FollowUpConfig(),
            memory_signals=dict(attrs.get("memory_signals") or {}),
            pipeline_value=float(attrs.get("pipeline_value") or (buying * 500.0)),
            now=datetime.now(UTC),
        )

    async def store_decision(self, decision: AutonomousSalesAgentDecision) -> AutonomousSalesAgentRun:
        row = AutonomousSalesAgentRun(
            company_id=decision.company_id,
            company_name=decision.company_name,
            stage=decision.stage.value,
            next_action=decision.next_best_action.action.value,
            confidence=float(decision.next_best_action.confidence),
            payload=decision.model_dump(mode="json"),
            evidence_chain=list(decision.evidence_chain),
            scoring_version=decision.scoring_version,
            metadata_json={},
        )
        self.session.add(row)
        await self.session.flush()

        for t in decision.transitions:
            self.session.add(
                AutonomousSalesWorkflowTransition(
                    company_id=decision.company_id,
                    run_id=row.id,
                    from_stage=t.from_stage.value if t.from_stage else None,
                    to_stage=t.to_stage.value,
                    reason=t.reason,
                    evidence=list(t.evidence),
                    actor=t.actor,
                    next_action=t.next_action,
                    occurred_at=t.timestamp,
                    immutable=True,
                )
            )
        for e in decision.timeline:
            self.session.add(
                AutonomousSalesTimelineEvent(
                    company_id=decision.company_id,
                    run_id=row.id,
                    event_type=e.event_type,
                    title=e.title,
                    detail=e.detail or "",
                    actor=e.actor,
                    occurred_at=e.occurred_at or datetime.now(UTC),
                    evidence=list(e.evidence),
                    immutable=True,
                )
            )
        await self.session.flush()
        return row

    async def store_work_queue_snapshot(
        self,
        *,
        kind: str,
        payload: dict[str, Any],
        item_count: int,
        revenue_forecast: float,
        evidence: list[Any] | None = None,
    ) -> AutonomousSalesWorkQueueSnapshot:
        row = AutonomousSalesWorkQueueSnapshot(
            kind=kind,
            payload=payload,
            item_count=item_count,
            revenue_forecast=revenue_forecast,
            scoring_version="asa-v1",
            evidence_chain=evidence or [],
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def latest_for_company(self, company_id: UUID) -> AutonomousSalesAgentRun | None:
        return await self.session.scalar(
            select(AutonomousSalesAgentRun)
            .where(AutonomousSalesAgentRun.company_id == company_id)
            .order_by(AutonomousSalesAgentRun.created_at.desc())
            .limit(1)
        )

    async def timeline_for_company(self, company_id: UUID, *, limit: int = 100) -> list[AutonomousSalesTimelineEvent]:
        return list(
            (
                await self.session.execute(
                    select(AutonomousSalesTimelineEvent)
                    .where(AutonomousSalesTimelineEvent.company_id == company_id)
                    .order_by(AutonomousSalesTimelineEvent.occurred_at.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def recent_runs(self, *, limit: int = 50) -> list[AutonomousSalesAgentRun]:
        return list(
            (
                await self.session.execute(
                    select(AutonomousSalesAgentRun).order_by(AutonomousSalesAgentRun.created_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def latest_brief(self) -> AutonomousSalesWorkQueueSnapshot | None:
        return await self.session.scalar(
            select(AutonomousSalesWorkQueueSnapshot)
            .where(AutonomousSalesWorkQueueSnapshot.kind == "morning_brief")
            .order_by(AutonomousSalesWorkQueueSnapshot.created_at.desc())
            .limit(1)
        )

    async def dashboard(self) -> dict[str, Any]:
        total = await self.session.scalar(select(func.count()).select_from(AutonomousSalesAgentRun)) or 0
        stages = (
            await self.session.execute(
                select(AutonomousSalesAgentRun.stage, func.count())
                .group_by(AutonomousSalesAgentRun.stage)
                .order_by(func.count().desc())
            )
        ).all()
        recent = await self.recent_runs(limit=12)
        return {
            "total_runs": int(total),
            "by_stage": {str(s): int(c) for s, c in stages},
            "recent_runs": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "company_name": r.company_name,
                    "stage": r.stage,
                    "next_action": r.next_action,
                    "confidence": r.confidence,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in recent
            ],
            "scoring_version": "asa-v1",
        }

    async def company_ids_for_refresh(self, *, limit: int = 40) -> list[UUID]:
        cutoff = datetime.now(UTC) - timedelta(days=90)
        rows = (
            await self.session.execute(
                select(Company.id).where(Company.created_at >= cutoff).order_by(Company.updated_at.desc()).limit(limit)
            )
        ).scalars().all()
        return list(rows)
