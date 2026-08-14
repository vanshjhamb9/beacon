from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignStep
from app.models.decision import DecisionMaker
from app.models.intelligence import Company
from app.models.live_revenue import (
    LiveRevenueLifecycleEvent,
    LiveRevenueProposalVersion,
    LiveRevenueRun,
    LiveRevenueTrackingEvent,
)
from app.models.opportunity import Opportunity
from app.models.revenue_hunter import RevenueHunterDossier
from app.models.sales_intelligence import SalesIntelligenceSnapshot
from live_revenue_execution.models.types import LREDecision, LREInput


class LiveRevenueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def build_input(self, company_id: UUID, *, campaign_id: UUID | None = None) -> LREInput | None:
        company = await self.session.get(Company, company_id)
        if company is None:
            return None

        campaign = None
        if campaign_id:
            campaign = await self.session.get(Campaign, campaign_id)
        if campaign is None:
            campaign = await self.session.scalar(
                select(Campaign)
                .where(Campaign.company_id == company_id)
                .order_by(Campaign.created_at.desc())
                .limit(1)
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
            (
                await self.session.execute(
                    select(DecisionMaker).where(DecisionMaker.company_id == company_id).limit(10)
                )
            ).scalars().all()
        )

        email_subject = None
        email_body = None
        to_email = None
        if campaign:
            step = await self.session.scalar(
                select(CampaignStep)
                .where(CampaignStep.campaign_id == campaign.id)
                .order_by(CampaignStep.sequence.asc())
                .limit(1)
            )
            if step:
                email_subject = step.subject_preview or None
                email_body = step.body_preview or None
            email_body = email_body or (
                campaign.plan_payload.get("body") if isinstance(campaign.plan_payload, dict) else None
            )
            email_subject = email_subject or (
                campaign.plan_payload.get("subject") if isinstance(campaign.plan_payload, dict) else None
            )

        si_payload = (si.payload if si else {}) or {}
        intent = si_payload.get("buying_intent") or {}
        offer = si_payload.get("offer") or {}
        meeting = si_payload.get("meeting_coach") or {}
        objections = si_payload.get("objections") or []

        pains: list[str] = []
        if dossier and dossier.pain_points:
            for p in dossier.pain_points:
                pains.append(str(p.get("pain") if isinstance(p, dict) else p))
        pains.extend(list(meeting.get("business_pain") or [])[:6])

        return LREInput(
            company_id=company.id,
            company_name=company.name,
            campaign_id=campaign.id if campaign else None,
            opportunity_id=opportunity.id if opportunity else None,
            industry=company.industry or (dossier.industry if dossier else None),
            priority_grade=dossier.priority_grade if dossier else None,
            probability=float(dossier.probability) if dossier else float(getattr(opportunity, "opportunity_score", 0) or 0),
            risk_score=float((company.attributes or {}).get("risk_score") or 0),
            decision_makers=[
                {"name": dm.name, "title": dm.role, "email": dm.work_email} for dm in dms
            ],
            pain_points=[p for p in pains if p][:10],
            evidence=list((dossier.evidence_chain if dossier else []) or [])[:20],
            email_subject=email_subject,
            email_body=email_body or "Personalized outreach ready for founder approval.",
            to_email=to_email or (dms[0].work_email if dms else None),
            from_email=(company.attributes or {}).get("from_email"),
            calendly_url=(company.attributes or {}).get("calendly_url") or "https://calendly.com/inowix/discovery",
            attachments=list((company.attributes or {}).get("attachments") or []),
            recommended_service=(dossier.recommended_service if dossier else None)
            or offer.get("primary_offer")
            or None,
            expected_budget=dossier.expected_budget if dossier else offer.get("expected_value"),
            buying_intent_score=float(intent.get("buying_intent_score") or (si.buying_intent_score if si else 0) or 0),
            dossier_highlights=[
                f"grade:{dossier.priority_grade}" if dossier else "grade:n/a",
                f"service:{dossier.recommended_service}" if dossier else "service:n/a",
            ],
            objections=[
                str(o.get("objection") if isinstance(o, dict) else o) for o in objections[:8]
            ],
            case_studies=[str(c.get("title")) for c in (si_payload.get("trust") or {}).get("case_studies", []) if isinstance(c, dict)],
            funnel_counts=dict((company.attributes or {}).get("funnel_counts") or {}),
            pipeline_value=float((company.attributes or {}).get("pipeline_value") or 0),
            revenue_closed=float((company.attributes or {}).get("revenue_closed") or 0),
            now=datetime.now(UTC),
        )

    async def store_decision(self, decision: LREDecision) -> LiveRevenueRun:
        risk = decision.approval_card.risk_score if decision.approval_card else 0.0
        row = LiveRevenueRun(
            company_id=decision.company_id,
            campaign_id=decision.campaign_id,
            opportunity_id=None,
            company_name=decision.company_name,
            stage=decision.stage.value,
            probability=decision.approval_card.probability if decision.approval_card else 0.0,
            risk_score=risk,
            payload=decision.model_dump(mode="json"),
            evidence_chain=list(decision.evidence_chain),
            scoring_version=decision.scoring_version,
            metadata_json={},
        )
        self.session.add(row)
        await self.session.flush()

        for event in decision.lifecycle_events:
            occurred = event.get("occurred_at")
            occurred_at = datetime.fromisoformat(occurred.replace("Z", "+00:00")) if isinstance(occurred, str) else datetime.now(UTC)
            self.session.add(
                LiveRevenueLifecycleEvent(
                    company_id=decision.company_id,
                    campaign_id=decision.campaign_id,
                    run_id=row.id,
                    stage=str(event.get("stage") or decision.stage.value),
                    detail=str(event.get("detail") or ""),
                    actor=str(event.get("actor") or "system"),
                    occurred_at=occurred_at,
                    evidence=[],
                    immutable=True,
                )
            )

        if decision.proposal:
            self.session.add(
                LiveRevenueProposalVersion(
                    company_id=decision.company_id,
                    campaign_id=decision.campaign_id,
                    title=decision.proposal.title,
                    version=decision.proposal.version,
                    tracking_id=decision.proposal.tracking_id,
                    pricing=decision.proposal.pricing,
                    payload=decision.proposal.model_dump(mode="json"),
                    pdf_base64=decision.proposal.pdf_base64,
                    status="ready",
                )
            )
        await self.session.flush()
        return row

    async def latest_for_company(self, company_id: UUID) -> LiveRevenueRun | None:
        return await self.session.scalar(
            select(LiveRevenueRun)
            .where(LiveRevenueRun.company_id == company_id)
            .order_by(LiveRevenueRun.created_at.desc())
            .limit(1)
        )

    async def list_approval_queue(self, *, limit: int = 50) -> list[dict[str, Any]]:
        pending = list(
            (
                await self.session.execute(
                    select(Campaign)
                    .where(Campaign.status.in_(["needs_review", "draft"]))
                    .order_by(Campaign.created_at.desc())
                    .limit(limit)
                )
            ).scalars().all()
        )
        cards: list[dict[str, Any]] = []
        for campaign in pending:
            data = await self.build_input(campaign.company_id, campaign_id=campaign.id)
            if data is None:
                continue
            from live_revenue_execution import LiveRevenueExecutionService

            decision = LiveRevenueExecutionService().evaluate(data)
            if decision.approval_card:
                cards.append(decision.approval_card.model_dump(mode="json"))
        return cards

    async def record_tracking(
        self,
        *,
        tracking_id: str,
        event_type: str,
        company_id: UUID | None = None,
        campaign_id: UUID | None = None,
        target_url: str | None = None,
        provider_response: dict | None = None,
    ) -> LiveRevenueTrackingEvent:
        row = LiveRevenueTrackingEvent(
            tracking_id=tracking_id,
            event_type=event_type,
            company_id=company_id,
            campaign_id=campaign_id,
            target_url=target_url,
            provider_response=provider_response or {},
            metadata_json={},
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_proposals(self, *, limit: int = 50) -> list[LiveRevenueProposalVersion]:
        return list(
            (
                await self.session.execute(
                    select(LiveRevenueProposalVersion)
                    .order_by(LiveRevenueProposalVersion.created_at.desc())
                    .limit(limit)
                )
            ).scalars().all()
        )

    async def dashboard(self) -> dict[str, Any]:
        total_runs = await self.session.scalar(select(func.count()).select_from(LiveRevenueRun)) or 0
        awaiting = await self.session.scalar(
            select(func.count()).select_from(Campaign).where(Campaign.status.in_(["needs_review", "draft"]))
        ) or 0
        proposals = await self.session.scalar(select(func.count()).select_from(LiveRevenueProposalVersion)) or 0
        opens = await self.session.scalar(
            select(func.count())
            .select_from(LiveRevenueTrackingEvent)
            .where(LiveRevenueTrackingEvent.event_type == "open")
        ) or 0
        clicks = await self.session.scalar(
            select(func.count())
            .select_from(LiveRevenueTrackingEvent)
            .where(LiveRevenueTrackingEvent.event_type == "click")
        ) or 0
        latest = list(
            (
                await self.session.execute(
                    select(LiveRevenueRun).order_by(LiveRevenueRun.created_at.desc()).limit(20)
                )
            ).scalars().all()
        )
        return {
            "total_runs": int(total_runs),
            "awaiting_approval": int(awaiting),
            "proposals": int(proposals),
            "opens": int(opens),
            "clicks": int(clicks),
            "recent_runs": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "company_name": r.company_name,
                    "stage": r.stage,
                    "probability": r.probability,
                    "risk_score": r.risk_score,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in latest
            ],
            "scoring_version": "lre-v1",
        }
