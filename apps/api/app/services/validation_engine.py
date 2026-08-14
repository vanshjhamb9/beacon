"""App service for Beacon Validation & Continuous Learning Platform."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.intelligence import Company
from app.models.validation_engine import (
    ConnectorRoiRow,
    DealEvent,
    IndustryRoiRow,
    LeadOutcome,
    MeetingEvent,
    ObjectionEvent,
    PersonaRoiRow,
    ProposalEvent,
    ReplyEvent,
    ServiceRoiRow,
    TriggerRoiRow,
    ValidationEvent,
    ValidationSnapshot,
    ValidationTimeline,
)


class ValidationService:
    """Service layer for validation engine API endpoints."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        settings: Settings | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()

    async def dashboard(self) -> dict[str, Any]:
        now = datetime.now(UTC)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total_revenue = await self._get_total_revenue()
        total_won = await self._count_deals_by_status("won")
        total_lost = await self._count_deals_by_status("lost")
        total_replies = await self._count(ReplyEvent)
        total_meetings = await self._count(MeetingEvent)
        total_proposals = await self._count(ProposalEvent)

        today_replies = await self._count_since(ReplyEvent, day_start)
        today_meetings = await self._count_since(MeetingEvent, day_start)
        today_proposals = await self._count_since(ProposalEvent, day_start)
        today_wins = await self._count_deals_by_status_since("won", day_start)
        today_revenue = await self._get_revenue_since(day_start)

        win_rate = (total_won / max(total_won + total_lost, 1)) * 100.0
        reply_rate = (total_replies / max(total_replies + 1, 1)) * 100.0
        meeting_rate = (total_meetings / max(total_replies, 1)) * 100.0
        proposal_rate = (total_proposals / max(total_meetings, 1)) * 100.0

        funnel = await self._build_funnel()
        connector_roi = await self._get_connector_roi()

        return {
            "generated_at": now.isoformat(),
            "today_replies": today_replies,
            "today_meetings": today_meetings,
            "today_proposals": today_proposals,
            "today_wins": today_wins,
            "today_revenue": today_revenue,
            "reply_rate": round(reply_rate, 2),
            "meeting_rate": round(meeting_rate, 2),
            "proposal_rate": round(proposal_rate, 2),
            "win_rate": round(win_rate, 2),
            "total_revenue": total_revenue,
            "avg_deal_size": 0.0,
            "funnel": funnel,
            "connector_roi": connector_roi,
        }

    async def replies(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(ReplyEvent)
                .where(ReplyEvent.deleted_at.is_(None))
                .order_by(ReplyEvent.created_at.desc())
                .limit(100)
            )
        ).scalars().all()
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "reply_type": r.reply_type,
                    "source": r.source,
                    "confidence": r.confidence,
                    "reply_time_seconds": r.reply_time_seconds,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows
            ],
        }

    async def meetings(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(MeetingEvent)
                .where(MeetingEvent.deleted_at.is_(None))
                .order_by(MeetingEvent.created_at.desc())
                .limit(100)
            )
        ).scalars().all()
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "meeting_type": r.meeting_type,
                    "duration_minutes": r.duration_minutes,
                    "notes": r.notes,
                    "next_action": r.next_action,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows
            ],
        }

    async def proposals(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(ProposalEvent)
                .where(ProposalEvent.deleted_at.is_(None))
                .order_by(ProposalEvent.created_at.desc())
                .limit(100)
            )
        ).scalars().all()
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "status": r.status,
                    "value": r.value,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows
            ],
        }

    async def deals(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(DealEvent)
                .where(DealEvent.deleted_at.is_(None))
                .order_by(DealEvent.created_at.desc())
                .limit(100)
            )
        ).scalars().all()
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "status": r.status,
                    "revenue": r.revenue,
                    "expected_revenue": r.expected_revenue,
                    "service_sold": r.service_sold,
                    "reason": r.reason,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows
            ],
        }

    async def connectors(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(ConnectorRoiRow)
                .where(ConnectorRoiRow.deleted_at.is_(None))
                .order_by(ConnectorRoiRow.revenue.desc())
            )
        ).scalars().all()
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": [
                {
                    "connector": r.connector,
                    "signals": r.signals,
                    "companies": r.companies,
                    "revenue_ready": r.revenue_ready,
                    "replies": r.replies,
                    "meetings": r.meetings,
                    "deals": r.deals,
                    "revenue": r.revenue,
                    "reply_rate": r.reply_rate,
                    "meeting_rate": r.meeting_rate,
                    "win_rate": r.win_rate,
                }
                for r in rows
            ],
        }

    async def industries(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(IndustryRoiRow)
                .where(IndustryRoiRow.deleted_at.is_(None))
                .order_by(IndustryRoiRow.revenue.desc())
            )
        ).scalars().all()
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": [
                {
                    "industry": r.industry,
                    "companies": r.companies,
                    "revenue_ready": r.revenue_ready,
                    "replies": r.replies,
                    "meetings": r.meetings,
                    "deals": r.deals,
                    "revenue": r.revenue,
                    "reply_rate": r.reply_rate,
                    "meeting_rate": r.meeting_rate,
                    "win_rate": r.win_rate,
                }
                for r in rows
            ],
        }

    async def services(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(ServiceRoiRow)
                .where(ServiceRoiRow.deleted_at.is_(None))
                .order_by(ServiceRoiRow.revenue.desc())
            )
        ).scalars().all()
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": [
                {
                    "service": r.service,
                    "companies": r.companies,
                    "replies": r.replies,
                    "meetings": r.meetings,
                    "deals": r.deals,
                    "revenue": r.revenue,
                    "reply_rate": r.reply_rate,
                    "meeting_rate": r.meeting_rate,
                    "proposal_rate": r.proposal_rate,
                    "win_rate": r.win_rate,
                }
                for r in rows
            ],
        }

    async def personas(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(PersonaRoiRow)
                .where(PersonaRoiRow.deleted_at.is_(None))
                .order_by(PersonaRoiRow.revenue.desc())
            )
        ).scalars().all()
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": [
                {
                    "persona": r.persona,
                    "contacted": r.contacted,
                    "replies": r.replies,
                    "meetings": r.meetings,
                    "deals": r.deals,
                    "revenue": r.revenue,
                    "reply_rate": r.reply_rate,
                    "meeting_rate": r.meeting_rate,
                }
                for r in rows
            ],
        }

    async def triggers(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(TriggerRoiRow)
                .where(TriggerRoiRow.deleted_at.is_(None))
                .order_by(TriggerRoiRow.revenue.desc())
            )
        ).scalars().all()
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "items": [
                {
                    "trigger": r.trigger,
                    "companies": r.companies,
                    "replies": r.replies,
                    "meetings": r.meetings,
                    "deals": r.deals,
                    "revenue": r.revenue,
                    "reply_rate": r.reply_rate,
                    "meeting_rate": r.meeting_rate,
                    "revenue_rate": r.revenue_rate,
                }
                for r in rows
            ],
        }

    async def revenue(self) -> dict[str, Any]:
        total_revenue = await self._get_total_revenue()
        won_deals = await self._count_deals_by_status("won")
        lost_deals = await self._count_deals_by_status("lost")
        avg_deal_size = total_revenue / max(won_deals, 1)
        win_rate = (won_deals / max(won_deals + lost_deals, 1)) * 100.0
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "total_revenue": total_revenue,
            "won_deals": won_deals,
            "lost_deals": lost_deals,
            "avg_deal_size": round(avg_deal_size, 2),
            "win_rate": round(win_rate, 2),
        }

    async def report_daily(self) -> dict[str, Any]:
        now = datetime.now(UTC)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return {
            "report_date": now.strftime("%Y-%m-%d"),
            "signals": 0,
            "companies": 0,
            "revenue_ready": 0,
            "emails_sent": await self._count_since(ValidationEvent, day_start),
            "replies": await self._count_since(ReplyEvent, day_start),
            "meetings": await self._count_since(MeetingEvent, day_start),
            "proposals": await self._count_since(ProposalEvent, day_start),
            "won": await self._count_deals_by_status_since("won", day_start),
            "lost": await self._count_deals_by_status_since("lost", day_start),
            "revenue": await self._get_revenue_since(day_start),
            "best_connector": "",
            "worst_connector": "",
            "best_industry": "",
            "worst_industry": "",
            "top_objections": [],
            "biggest_bottleneck": "",
        }

    async def report_weekly(self) -> dict[str, Any]:
        now = datetime.now(UTC)
        return {
            "week_start": "",
            "week_end": now.strftime("%Y-%m-%d"),
            "revenue": await self._get_total_revenue(),
            "meetings": await self._count(MeetingEvent),
            "deals": await self._count(DealEvent),
            "connector_ranking": [],
            "industry_ranking": [],
            "service_ranking": [],
            "persona_ranking": [],
            "trigger_ranking": [],
        }

    async def report_monthly(self) -> dict[str, Any]:
        now = datetime.now(UTC)
        return {
            "month": now.strftime("%Y-%m"),
            "revenue": await self._get_total_revenue(),
            "avg_deal_size": 0.0,
            "avg_sales_cycle_days": 0.0,
            "reply_rate": 0.0,
            "meeting_rate": 0.0,
            "proposal_rate": 0.0,
            "win_rate": 0.0,
            "revenue_per_connector": {},
            "revenue_per_industry": {},
            "revenue_per_service": {},
        }

    async def _build_funnel(self) -> list[dict[str, Any]]:
        stages = [
            ("REVENUE_READY", ValidationEvent),
            ("CONTACTED", ValidationEvent),
            ("EMAIL_OPENED", ValidationEvent),
            ("REPLIED", ReplyEvent),
            ("MEETING_BOOKED", MeetingEvent),
            ("PROPOSAL_SENT", ProposalEvent),
            ("WON", DealEvent),
        ]
        funnel = []
        previous = 0
        for stage_name, model in stages:
            count = await self._count(model)
            conversion = 0.0
            drop_off = 0.0
            if previous > 0:
                conversion = (count / previous) * 100.0
                drop_off = 100.0 - conversion
            funnel.append({
                "stage": stage_name,
                "count": count,
                "conversion_from_previous": round(conversion, 2),
                "drop_off": round(drop_off, 2),
            })
            previous = count
        return funnel

    async def _get_connector_roi(self) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(ConnectorRoiRow)
                .where(ConnectorRoiRow.deleted_at.is_(None))
                .order_by(ConnectorRoiRow.revenue.desc())
            )
        ).scalars().all()
        return [
            {
                "connector": r.connector,
                "signals": r.signals,
                "revenue_ready": r.revenue_ready,
                "replies": r.replies,
                "meetings": r.meetings,
                "deals": r.deals,
                "revenue": r.revenue,
            }
            for r in rows
        ]

    async def _get_total_revenue(self) -> float:
        result = await self.session.scalar(
            select(func.coalesce(func.sum(DealEvent.revenue), 0.0)).where(
                DealEvent.deleted_at.is_(None),
                DealEvent.status == "won",
            )
        )
        return float(result or 0.0)

    async def _get_revenue_since(self, since: datetime) -> float:
        result = await self.session.scalar(
            select(func.coalesce(func.sum(DealEvent.revenue), 0.0)).where(
                DealEvent.deleted_at.is_(None),
                DealEvent.status == "won",
                DealEvent.created_at >= since,
            )
        )
        return float(result or 0.0)

    async def _count_deals_by_status(self, status: str) -> int:
        return await self._count(DealEvent, DealEvent.status == status)

    async def _count_deals_by_status_since(self, status: str, since: datetime) -> int:
        return await self._count(DealEvent, DealEvent.status == status, DealEvent.created_at >= since)

    async def _count(self, model: type[Any], *clauses: Any) -> int:
        stmt = select(func.count()).select_from(model)
        filters = [model.deleted_at.is_(None), *clauses]
        stmt = stmt.where(and_(*filters))
        return int(await self.session.scalar(stmt) or 0)

    async def _count_since(self, model: type[Any], since: datetime, *clauses: Any) -> int:
        return await self._count(model, model.created_at >= since, *clauses)
