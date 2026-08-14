from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.communication import ConversationThreadRow
from app.models.founder_os import (
    FounderAnalyticsEventRow,
    FounderDailyBriefRow,
    FounderRevenueTaskRow,
    FounderTimelineEventRow,
)
from app.models.intelligence import Company
from app.models.opportunity import Opportunity
from app.models.outcomes import Deal, Meeting, OpportunityOutcome, Proposal
from app.models.revenue_hunter import RevenueHunterDossier, RevenueHunterWorkQueueItem
from founder_os.models.types import AnalyticsEvent, FounderOsDecision, FounderOsInput, RevenueTask, TimelineEvent


class FounderOsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def build_input(self) -> FounderOsInput:
        now = datetime.now(UTC)
        since = now - timedelta(hours=24)

        new_companies = await self.session.scalar(
            select(func.count()).select_from(Company).where(Company.created_at >= since)
        ) or 0
        new_opps = (
            await self.session.execute(
                select(Opportunity).where(Opportunity.created_at >= since).limit(500)
            )
        ).scalars().all()
        buying_signals = len(new_opps)

        dossiers = list(
            (
                await self.session.execute(
                    select(RevenueHunterDossier).order_by(RevenueHunterDossier.revenue_score.desc()).limit(200)
                )
            ).scalars().all()
        )
        a_plus = sum(1 for d in dossiers if d.priority_grade == "A+")
        sales_ready = sum(1 for d in dossiers if d.proceed_to_campaign)
        qualified = sum(1 for d in dossiers if d.filter_passed)

        campaigns_waiting = await self.session.scalar(
            select(func.count()).select_from(Campaign).where(Campaign.status.in_(["needs_review", "draft"]))
        ) or 0
        pending_campaigns = list(
            (
                await self.session.execute(
                    select(Campaign)
                    .where(Campaign.status.in_(["needs_review", "draft"]))
                    .order_by(Campaign.created_at.desc())
                    .limit(50)
                )
            ).scalars().all()
        )

        replies_waiting = await self.session.scalar(
            select(func.coalesce(func.sum(ConversationThreadRow.unread_count), 0))
        ) or 0
        replies_waiting = int(replies_waiting)

        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        meetings_today_rows = list(
            (
                await self.session.execute(
                    select(Meeting)
                    .where(Meeting.scheduled_at >= day_start)
                    .where(Meeting.scheduled_at < day_end)
                    .order_by(Meeting.scheduled_at.asc())
                    .limit(50)
                )
            ).scalars().all()
        )
        proposals_pending = await self.session.scalar(
            select(func.count()).select_from(Proposal).where(Proposal.status.in_(["sent", "draft", "pending"]))
        ) or 0

        outcomes = list((await self.session.execute(select(OpportunityOutcome).limit(2000))).scalars().all())
        won = sum(1 for o in outcomes if o.lifecycle_stage == "won")
        lost = sum(1 for o in outcomes if o.lifecycle_stage == "lost")
        contacted = sum(1 for o in outcomes if o.contacted_at is not None or o.lifecycle_stage in {"contacted", "replied", "meeting_scheduled", "proposal_sent", "won", "lost"})
        replied = sum(1 for o in outcomes if o.replied_at is not None or o.lifecycle_stage in {"replied", "meeting_scheduled", "proposal_sent", "won"})
        meeting_count = sum(1 for o in outcomes if o.meeting_at is not None or o.lifecycle_stage in {"meeting_scheduled", "proposal_sent", "won"})
        proposal_count = sum(1 for o in outcomes if o.proposal_at is not None or o.lifecycle_stage in {"proposal_sent", "negotiation", "won"})

        deals = list((await self.session.execute(select(Deal).limit(1000))).scalars().all())
        won_deals = [d for d in deals if d.status == "won"]
        avg_deal = (sum(d.value for d in won_deals) / len(won_deals)) if won_deals else 0.0

        industry_wins: Counter[str] = Counter()
        service_wins: Counter[str] = Counter()
        country_wins: Counter[str] = Counter()
        for o in outcomes:
            if o.lifecycle_stage != "won":
                continue
            if o.industry:
                industry_wins[o.industry] += 1
            if o.recommended_service:
                service_wins[o.recommended_service] += 1

        for d in dossiers:
            if d.country and d.proceed_to_campaign:
                country_wins[d.country] += 1

        pipeline = sum(float(d.probability or 0) / 100.0 * self._mid_budget(d.expected_budget) for d in dossiers if d.proceed_to_campaign)
        expected = sum(
            float(d.probability or 0) / 100.0 * self._mid_budget(d.expected_budget)
            for d in dossiers
            if d.priority_grade in {"A+", "A"}
        )

        work_queue = list(
            (
                await self.session.execute(
                    select(RevenueHunterWorkQueueItem)
                    .where(RevenueHunterWorkQueueItem.status == "pending")
                    .order_by(RevenueHunterWorkQueueItem.rank.asc())
                    .limit(50)
                )
            ).scalars().all()
        )

        top_companies = [
            {
                "company_id": str(d.company_id),
                "company_name": d.company_name,
                "priority_grade": d.priority_grade,
                "recommended_service": d.recommended_service,
                "expected_budget": d.expected_budget,
                "probability": d.probability,
                "why_today": (d.why_now or {}).get("why_today") if isinstance(d.why_now, dict) else None,
                "why_them": (d.why_now or {}).get("why_this_company") if isinstance(d.why_now, dict) else None,
                "evidence": d.evidence_chain or [],
                "proceed_to_campaign": d.proceed_to_campaign,
                "revenue_score": d.revenue_score,
            }
            for d in dossiers[:25]
        ]

        proposal_candidates = [
            {
                "company_id": str(d.company_id),
                "company_name": d.company_name,
                "recommended_service": d.recommended_service,
                "budget_range": d.expected_budget,
                "estimated_timeline": d.expected_timeline,
                "proposal_status": "needed",
                "case_studies": (d.dossier or {}).get("case_studies") if isinstance(d.dossier, dict) else [],
            }
            for d in dossiers
            if d.proceed_to_campaign and d.priority_grade in {"A+", "A"}
        ][:30]

        meetings_payload = []
        for m in meetings_today_rows:
            dossier = next((d for d in dossiers if d.company_id == m.company_id), None)
            meetings_payload.append(
                {
                    "id": str(m.id),
                    "company_id": str(m.company_id),
                    "company_name": dossier.company_name if dossier else "Company",
                    "scheduled_at": m.scheduled_at.isoformat(),
                    "recommended_service": dossier.recommended_service if dossier else None,
                    "pain_points": [
                        p.get("problem") for p in ((dossier.pain_points or []) if dossier else []) if isinstance(p, dict)
                    ],
                    "buying_signals": (dossier.dossier or {}).get("buying_signals") if dossier and isinstance(dossier.dossier, dict) else [],
                    "decision_makers": (dossier.dossier or {}).get("decision_makers") if dossier and isinstance(dossier.dossier, dict) else [],
                    "priority_grade": dossier.priority_grade if dossier else None,
                    "expected_timeline": dossier.expected_timeline if dossier else None,
                }
            )

        missing_contacts = [
            {"company_id": str(d.company_id), "company_name": d.company_name}
            for d in dossiers
            if d.proceed_to_campaign
            and isinstance(d.dossier, dict)
            and not (d.dossier.get("emails") or d.dossier.get("phones"))
        ][:20]

        website_audit_needed = []
        for d in dossiers:
            wi = d.website_intelligence or {}
            ops = wi.get("opportunities") if isinstance(wi, dict) else []
            if any(isinstance(o, dict) and o.get("severity") == "high" for o in (ops or [])):
                website_audit_needed.append(
                    {
                        "company_id": str(d.company_id),
                        "company_name": d.company_name,
                        "evidence": [f"severity:high"],
                    }
                )

        verification_failed = [
            {
                "company_id": str(d.company_id),
                "company_name": d.company_name,
                "verification_score": (d.explanations or {}).get("verification_score", 0),
            }
            for d in dossiers
            if isinstance(d.explanations, dict) and float(d.explanations.get("verification_score") or 100) < 40
        ][:20]

        timeline_seeds = []
        for d in dossiers[:40]:
            timeline_seeds.append(
                {
                    "company_id": str(d.company_id),
                    "company_name": d.company_name,
                    "stage": "discovery",
                    "occurred_at": d.created_at.isoformat() if d.created_at else now.isoformat(),
                    "summary": f"Revenue hunter dossier created ({d.priority_grade})",
                    "evidence": [f"grade:{d.priority_grade}", f"score:{d.revenue_score}"],
                }
            )
        for o in outcomes[:100]:
            stage_map = {
                "contacted": "email",
                "replied": "reply",
                "meeting_scheduled": "meeting",
                "proposal_sent": "proposal",
                "negotiation": "negotiation",
                "won": "won",
                "lost": "lost",
            }
            stage = stage_map.get(o.lifecycle_stage)
            if not stage:
                continue
            timeline_seeds.append(
                {
                    "company_id": str(o.company_id),
                    "company_name": o.recommended_service or "Account",
                    "stage": stage,
                    "occurred_at": (o.updated_at or now).isoformat(),
                    "summary": f"Lifecycle → {o.lifecycle_stage}",
                    "evidence": [f"lifecycle:{o.lifecycle_stage}"],
                    "actor": o.owner or "system",
                }
            )

        return FounderOsInput(
            new_companies_found=int(new_companies),
            new_buying_signals=int(buying_signals),
            qualified_companies=qualified,
            sales_ready_accounts=sales_ready,
            a_plus_opportunities=a_plus,
            campaigns_waiting_approval=int(campaigns_waiting),
            replies_waiting=int(replies_waiting),
            meetings_today=len(meetings_today_rows),
            proposals_pending=int(proposals_pending),
            estimated_pipeline=round(pipeline, 2),
            expected_revenue=round(expected, 2),
            lost_opportunities=lost,
            won_opportunities=won,
            industry_wins=dict(industry_wins),
            service_wins=dict(service_wins),
            outreach_style_wins={"funding": max(1, a_plus // 2), "hiring": max(0, a_plus // 3)},
            subject_line_wins={},
            cta_wins={},
            contacted_count=contacted,
            replied_count=replied,
            meeting_count=meeting_count,
            proposal_count=proposal_count,
            average_deal_size=avg_deal,
            average_sales_cycle_days=30.0,
            country_wins=dict(country_wins),
            campaign_sends=int(await self.session.scalar(select(func.count()).select_from(Campaign)) or 0),
            campaign_replies=replied,
            top_companies=top_companies,
            work_queue_items=[self._queue_dict(q) for q in work_queue],
            follow_ups=[self._queue_dict(q) for q in work_queue if q.priority_grade in {"A+", "A"}],
            pending_campaigns=[
                {
                    "id": str(c.id),
                    "company_id": str(c.company_id),
                    "company_name": c.company_name,
                    "status": c.status,
                }
                for c in pending_campaigns
            ],
            pending_replies=[],
            meetings=meetings_payload,
            proposal_candidates=proposal_candidates,
            missing_contacts=missing_contacts,
            website_audit_needed=website_audit_needed[:20],
            verification_failed=verification_failed,
            timeline_seeds=timeline_seeds,
            now=now,
        )

    async def store_decision(self, decision: FounderOsDecision) -> FounderDailyBriefRow:
        brief = decision.brief
        row = FounderDailyBriefRow(
            executive_summary=brief.executive_summary,
            new_companies_found=brief.new_companies_found,
            new_buying_signals=brief.new_buying_signals,
            qualified_companies=brief.qualified_companies,
            sales_ready_accounts=brief.sales_ready_accounts,
            a_plus_opportunities=brief.a_plus_opportunities,
            campaigns_waiting_approval=brief.campaigns_waiting_approval,
            replies_waiting=brief.replies_waiting,
            meetings_today=brief.meetings_today,
            proposals_pending=brief.proposals_pending,
            estimated_pipeline=brief.estimated_pipeline,
            expected_revenue=brief.expected_revenue,
            lost_opportunities=brief.lost_opportunities,
            won_opportunities=brief.won_opportunities,
            top_performing_industry=brief.top_performing_industry,
            top_performing_service=brief.top_performing_service,
            top_performing_outreach_style=brief.top_performing_outreach_style,
            top_performing_subject_line=brief.top_performing_subject_line,
            top_performing_cta=brief.top_performing_cta,
            evidence=list(brief.evidence),
            payload=decision.model_dump(mode="json"),
            scoring_version=decision.scoring_version,
        )
        self.session.add(row)
        await self._upsert_tasks(decision.tasks)
        await self._append_timeline(decision.timeline_events)
        await self.session.flush()
        return row

    async def latest_brief(self) -> FounderDailyBriefRow | None:
        return await self.session.scalar(
            select(FounderDailyBriefRow).order_by(FounderDailyBriefRow.created_at.desc()).limit(1)
        )

    async def list_tasks(self, *, status: str | None = "open", limit: int = 50) -> list[FounderRevenueTaskRow]:
        stmt = select(FounderRevenueTaskRow).order_by(FounderRevenueTaskRow.priority.asc()).limit(limit)
        if status:
            stmt = select(FounderRevenueTaskRow).where(FounderRevenueTaskRow.status == status).order_by(
                FounderRevenueTaskRow.priority.asc()
            ).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def complete_task(self, task_id: UUID) -> FounderRevenueTaskRow | None:
        row = await self.session.get(FounderRevenueTaskRow, task_id)
        if row is None:
            return None
        row.status = "done"
        await self.session.flush()
        return row

    async def company_timeline(self, company_id: UUID, *, limit: int = 100) -> list[FounderTimelineEventRow]:
        stmt = (
            select(FounderTimelineEventRow)
            .where(FounderTimelineEventRow.company_id == company_id)
            .order_by(FounderTimelineEventRow.occurred_at.asc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def append_analytics(self, event: AnalyticsEvent) -> FounderAnalyticsEventRow:
        row = FounderAnalyticsEventRow(
            event_type=event.event_type.value,
            action=event.action,
            actor=event.actor,
            company_id=event.company_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            payload=dict(event.payload),
            occurred_at=event.occurred_at or datetime.now(UTC),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def _upsert_tasks(self, tasks: list[RevenueTask]) -> None:
        for task in tasks:
            existing = await self.session.scalar(
                select(FounderRevenueTaskRow)
                .where(FounderRevenueTaskRow.task_key == task.task_id)
                .limit(1)
            )
            if existing:
                continue
            self.session.add(
                FounderRevenueTaskRow(
                    task_key=task.task_id,
                    kind=task.kind.value,
                    title=task.title,
                    priority=task.priority.value,
                    deadline=task.deadline,
                    owner=task.owner,
                    status=task.status.value,
                    reason=task.reason,
                    evidence=list(task.evidence),
                    company_id=task.company_id,
                    company_name=task.company_name,
                    related_id=task.related_id,
                    metadata_json={},
                )
            )

    async def _append_timeline(self, events: list[TimelineEvent]) -> None:
        for event in events:
            # Never mutate — skip if event_key already stored
            exists = await self.session.scalar(
                select(FounderTimelineEventRow.id)
                .where(FounderTimelineEventRow.event_key == event.event_id)
                .limit(1)
            )
            if exists:
                continue
            self.session.add(
                FounderTimelineEventRow(
                    event_key=event.event_id,
                    company_id=event.company_id,
                    company_name=event.company_name,
                    stage=event.stage.value,
                    occurred_at=event.occurred_at,
                    summary=event.summary,
                    evidence=list(event.evidence),
                    actor=event.actor,
                    metadata_json=dict(event.metadata),
                    immutable=True,
                )
            )

    def _queue_dict(self, row: RevenueHunterWorkQueueItem) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "company_id": str(row.company_id),
            "company_name": row.company_name,
            "priority_grade": row.priority_grade,
            "recommended_service": row.recommended_service,
            "why_today": row.why_today,
            "expected_budget": row.expected_budget,
            "probability": row.probability,
            "status": row.status,
            "rank": row.rank,
        }

    def _mid_budget(self, text: str | None) -> float:
        if not text:
            return 40_000.0
        cleaned = text.replace("$", "").replace(",", "").lower().replace("–", "-")
        parts = cleaned.split("-")
        nums: list[float] = []
        for part in parts:
            part = part.strip()
            mult = 1.0
            if part.endswith("k"):
                mult = 1_000.0
                part = part[:-1]
            try:
                nums.append(float(part) * mult)
            except ValueError:
                continue
        return sum(nums) / len(nums) if nums else 40_000.0
