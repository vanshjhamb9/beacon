from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_journey import (
    AccountHealthSnapshot,
    AccountJourneyRow,
    AccountTimelineRow,
    BuyingCommitteeRow,
    CampaignAnalyticsSnapshot,
    EngagementScoreRow,
    FollowUpPlanRow,
    ReplyClassificationRow,
)
from app.models.campaign import Campaign
from app.models.decision import DecisionMaker
from app.models.intelligence import Company
from app.models.opportunity import Opportunity
from app.models.revenue_hunter import RevenueHunterDossier
from app.models.sales_intelligence import SalesIntelligenceSnapshot
from account_journey.models.types import AccountJourneyDecision, AccountJourneyInput


class AccountJourneyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def build_input(self, company_id: UUID) -> AccountJourneyInput | None:
        company = await self.session.get(Company, company_id)
        if company is None:
            return None
        attrs = company.attributes or {}
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
        opportunity = await self.session.scalar(
            select(Opportunity)
            .where(Opportunity.company_id == company_id)
            .order_by(Opportunity.opportunity_score.desc())
            .limit(1)
        )
        campaign = await self.session.scalar(
            select(Campaign).where(Campaign.company_id == company_id).order_by(Campaign.created_at.desc()).limit(1)
        )
        dms = list(
            (await self.session.execute(select(DecisionMaker).where(DecisionMaker.company_id == company_id).limit(10)))
            .scalars()
            .all()
        )
        si_payload = (si.payload if si else {}) or {}
        intent = float(
            (si_payload.get("buying_intent") or {}).get("buying_intent_score")
            or (si.buying_intent_score if si else 0)
            or 0
        )
        return AccountJourneyInput(
            company_id=company.id,
            company_name=company.name,
            industry=company.industry or (dossier.industry if dossier else None),
            country=str(attrs.get("country") or "") or None,
            company_size=str(attrs.get("company_size") or "") or None,
            technologies=list(attrs.get("technologies") or [])[:12],
            service=(dossier.recommended_service if dossier else None),
            campaign_name=campaign.company_name if campaign else None,
            probability=float(dossier.probability if dossier else getattr(opportunity, "opportunity_score", 0) or 0),
            buying_intent=intent,
            qualified=bool(dossier and dossier.priority_grade in {"A+", "A", "B"}) or bool(attrs.get("qualified")),
            enriched=bool(attrs.get("enriched")) or bool(attrs.get("technologies")),
            has_decision_makers=bool(dms),
            outreach_ready=bool(attrs.get("outreach_ready")) or bool(dms and dossier),
            campaign_active=bool(campaign and campaign.status in {"approved", "scheduled", "running"}),
            emailed=bool(attrs.get("emailed")) or bool(campaign and campaign.status in {"approved", "scheduled", "completed"}),
            whatsapp_sent=bool(attrs.get("whatsapp_sent")),
            opened=bool(attrs.get("opened")),
            clicked=bool(attrs.get("clicked")),
            replied=bool(attrs.get("replied")),
            no_reply_days=int(attrs.get("no_reply_days") or 0),
            cta_clicks=int(attrs.get("cta_clicks") or 0),
            video_watched=bool(attrs.get("video_watched")),
            calendly_opened=bool(attrs.get("calendly_opened")),
            calendar_booked=bool(attrs.get("calendar_booked")),
            meeting_scheduled=bool(attrs.get("meeting_scheduled")),
            proposal_requested=bool(attrs.get("proposal_requested")),
            negotiation=bool(attrs.get("negotiation")),
            won=bool(attrs.get("won")),
            lost=bool(attrs.get("lost")),
            dormant_days=int(attrs.get("dormant_days") or 0),
            reactivated=bool(attrs.get("reactivated")),
            reply_text=str(attrs.get("reply_text") or ""),
            decision_makers=[{"name": dm.name, "title": dm.role, "email": dm.work_email} for dm in dms],
            founder_notes=list(attrs.get("founder_notes") or []),
            now=datetime.now(UTC),
        )

    async def store_decision(self, decision: AccountJourneyDecision) -> AccountJourneyRow:
        row = AccountJourneyRow(
            company_id=decision.company_id,
            company_name=decision.company_name,
            stage=decision.stage.value,
            health_category=decision.health.category.value,
            overall_engagement=float(decision.engagement.overall_engagement),
            payload=decision.model_dump(mode="json"),
            evidence_chain=list(decision.evidence_chain),
            scoring_version=decision.scoring_version,
            metadata_json={},
        )
        self.session.add(row)
        await self.session.flush()

        self.session.add(
            EngagementScoreRow(
                company_id=decision.company_id,
                journey_id=row.id,
                open_score=decision.engagement.open_score,
                reply_score=decision.engagement.reply_score,
                intent_score=decision.engagement.intent_score,
                meeting_score=decision.engagement.meeting_score,
                relationship_score=decision.engagement.relationship_score,
                account_temperature=decision.engagement.account_temperature,
                overall_engagement=decision.engagement.overall_engagement,
                payload=decision.engagement.model_dump(mode="json"),
                evidence=list(decision.engagement.evidence),
            )
        )
        self.session.add(
            AccountHealthSnapshot(
                company_id=decision.company_id,
                journey_id=row.id,
                category=decision.health.category.value,
                score=decision.health.score,
                reason=decision.health.reason,
                evidence=list(decision.health.evidence),
            )
        )
        self.session.add(
            BuyingCommitteeRow(
                company_id=decision.company_id,
                journey_id=row.id,
                coverage=decision.buying_committee.coverage,
                members=[m.model_dump(mode="json") for m in decision.buying_committee.members],
                missing_roles=list(decision.buying_committee.missing_roles),
                evidence=list(decision.buying_committee.evidence),
            )
        )
        self.session.add(
            FollowUpPlanRow(
                company_id=decision.company_id,
                journey_id=row.id,
                next_action=decision.follow_up.next_action,
                channel=decision.follow_up.channel.value,
                message_type=decision.follow_up.message_type,
                urgency=decision.follow_up.urgency,
                best_timing_hours=decision.follow_up.best_timing_hours,
                reason=decision.follow_up.reason,
                requires_founder_approval=decision.follow_up.requires_founder_approval,
                payload=decision.follow_up.model_dump(mode="json"),
                evidence=list(decision.follow_up.evidence),
            )
        )
        if decision.reply:
            self.session.add(
                ReplyClassificationRow(
                    company_id=decision.company_id,
                    journey_id=row.id,
                    classification=decision.reply.classification.value,
                    confidence=decision.reply.confidence,
                    structured_outcome=dict(decision.reply.structured_outcome),
                    evidence=list(decision.reply.evidence),
                )
            )
        for event in decision.timeline:
            self.session.add(
                AccountTimelineRow(
                    company_id=decision.company_id,
                    journey_id=row.id,
                    event_type=event.event_type,
                    title=event.title,
                    detail=event.detail or "",
                    actor=event.actor,
                    occurred_at=event.occurred_at or datetime.now(UTC),
                    evidence=list(event.evidence),
                    immutable=True,
                )
            )
        await self.session.flush()
        return row

    async def store_analytics(self, decision: AccountJourneyDecision) -> CampaignAnalyticsSnapshot:
        row = CampaignAnalyticsSnapshot(
            payload=decision.analytics.model_dump(mode="json"),
            evidence_chain=list(decision.analytics.evidence),
            scoring_version=decision.scoring_version,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def latest_for_company(self, company_id: UUID) -> AccountJourneyRow | None:
        return await self.session.scalar(
            select(AccountJourneyRow)
            .where(AccountJourneyRow.company_id == company_id)
            .order_by(AccountJourneyRow.created_at.desc())
            .limit(1)
        )

    async def recent_journeys(self, *, limit: int = 50) -> list[AccountJourneyRow]:
        return list(
            (await self.session.execute(select(AccountJourneyRow).order_by(AccountJourneyRow.created_at.desc()).limit(limit)))
            .scalars()
            .all()
        )

    async def recent_followups(self, *, limit: int = 50) -> list[FollowUpPlanRow]:
        return list(
            (await self.session.execute(select(FollowUpPlanRow).order_by(FollowUpPlanRow.created_at.desc()).limit(limit)))
            .scalars()
            .all()
        )

    async def recent_replies(self, *, limit: int = 50) -> list[ReplyClassificationRow]:
        return list(
            (
                await self.session.execute(
                    select(ReplyClassificationRow).order_by(ReplyClassificationRow.created_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def recent_health(self, *, limit: int = 50) -> list[AccountHealthSnapshot]:
        return list(
            (
                await self.session.execute(
                    select(AccountHealthSnapshot).order_by(AccountHealthSnapshot.created_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def latest_analytics(self) -> CampaignAnalyticsSnapshot | None:
        return await self.session.scalar(
            select(CampaignAnalyticsSnapshot).order_by(CampaignAnalyticsSnapshot.created_at.desc()).limit(1)
        )

    async def company_ids(self, *, limit: int = 40) -> list[UUID]:
        return list((await self.session.execute(select(Company.id).order_by(Company.updated_at.desc()).limit(limit))).scalars().all())

    async def dashboard_counts(self) -> dict[str, Any]:
        total = await self.session.scalar(select(func.count()).select_from(AccountJourneyRow)) or 0
        by_health = (
            await self.session.execute(
                select(AccountJourneyRow.health_category, func.count()).group_by(AccountJourneyRow.health_category)
            )
        ).all()
        by_stage = (
            await self.session.execute(select(AccountJourneyRow.stage, func.count()).group_by(AccountJourneyRow.stage))
        ).all()
        return {
            "total_journeys": int(total),
            "by_health": {str(k): int(v) for k, v in by_health},
            "by_stage": {str(k): int(v) for k, v in by_stage},
            "scoring_version": "goi-v1",
        }
