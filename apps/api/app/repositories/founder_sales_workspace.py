"""Founder Sales Workspace (FSW) repository — Sprint 38."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Sequence

from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.founder_sales_workspace import (
    LeadAction,
    LeadNote,
    LeadStage,
    LeadTask,
    LeadTimeline,
)


class FSWRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Lead Stages ──

    async def list_leads(
        self,
        *,
        stage: str | None = None,
        owner: str | None = None,
        industry: str | None = None,
        country: str | None = None,
        service: str | None = None,
        connector: str | None = None,
        trigger: str | None = None,
        manual_status: str | None = None,
        score_min: float | None = None,
        score_max: float | None = None,
        revenue_min: float | None = None,
        revenue_max: float | None = None,
        age_days_max: int | None = None,
        search: str | None = None,
        include_garbage: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[LeadStage]:
        stmt = select(LeadStage).where(LeadStage.deleted_at.is_(None))

        if not include_garbage:
            stmt = stmt.where(LeadStage.stage != "garbage")
        if stage:
            stmt = stmt.where(LeadStage.stage == stage)
        if owner:
            stmt = stmt.where(LeadStage.owner == owner)
        if industry:
            stmt = stmt.where(LeadStage.industry.ilike(f"%{industry}%"))
        if country:
            stmt = stmt.where(LeadStage.country.ilike(f"%{country}%"))
        if service:
            stmt = stmt.where(LeadStage.service_match.ilike(f"%{service}%"))
        if connector:
            stmt = stmt.where(LeadStage.source_connector == connector)
        if trigger:
            stmt = stmt.where(LeadStage.trigger == trigger)
        if manual_status:
            stmt = stmt.where(LeadStage.manual_status == manual_status)
        if score_min is not None:
            stmt = stmt.where(LeadStage.revenue_opportunity_score >= score_min)
        if score_max is not None:
            stmt = stmt.where(LeadStage.revenue_opportunity_score <= score_max)
        if revenue_min is not None:
            stmt = stmt.where(LeadStage.revenue_opportunity_score >= revenue_min)
        if revenue_max is not None:
            stmt = stmt.where(LeadStage.revenue_opportunity_score <= revenue_max)
        if age_days_max is not None:
            cutoff = datetime.now(UTC) - __import__("datetime").timedelta(days=age_days_max)
            stmt = stmt.where(LeadStage.created_at >= cutoff)
        if search:
            stmt = stmt.where(
                or_(
                    LeadStage.company_name.ilike(f"%{search}%"),
                    LeadStage.industry.ilike(f"%{search}%"),
                    LeadStage.why_now.ilike(f"%{search}%"),
                )
            )

        stmt = stmt.order_by(LeadStage.stage, LeadStage.sort_order, desc(LeadStage.created_at))
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_lead(self, lead_id: uuid.UUID) -> LeadStage | None:
        result = await self.session.execute(
            select(LeadStage).where(LeadStage.id == lead_id, LeadStage.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def create_lead(self, data: dict[str, Any]) -> LeadStage:
        lead = LeadStage(**data)
        self.session.add(lead)
        await self.session.flush()
        return lead

    async def update_lead(self, lead_id: uuid.UUID, data: dict[str, Any]) -> LeadStage | None:
        lead = await self.get_lead(lead_id)
        if not lead:
            return None
        for key, value in data.items():
            if hasattr(lead, key):
                setattr(lead, key, value)
        await self.session.flush()
        return lead

    async def move_lead(self, lead_id: uuid.UUID, new_stage: str, sort_order: int | None = None) -> LeadStage | None:
        lead = await self.get_lead(lead_id)
        if not lead:
            return None
        old_stage = lead.stage
        lead.stage = new_stage
        if sort_order is not None:
            lead.sort_order = sort_order
        if new_stage == "garbage":
            lead.garbage_at = datetime.now(UTC)
        elif new_stage == "archived":
            lead.archived_at = datetime.now(UTC)
        await self.session.flush()
        return lead

    async def bulk_move(self, lead_ids: list[uuid.UUID], new_stage: str) -> int:
        stmt = (
            update(LeadStage)
            .where(LeadStage.id.in_(lead_ids), LeadStage.deleted_at.is_(None))
            .values(stage=new_stage)
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def bulk_delete(self, lead_ids: list[uuid.UUID]) -> int:
        now = datetime.now(UTC)
        stmt = (
            update(LeadStage)
            .where(LeadStage.id.in_(lead_ids))
            .values(deleted_at=now)
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def get_stage_counts(self) -> dict[str, int]:
        stmt = (
            select(LeadStage.stage, func.count(LeadStage.id))
            .where(LeadStage.deleted_at.is_(None), LeadStage.stage != "garbage")
            .group_by(LeadStage.stage)
        )
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    async def get_unique_values(self, field: str) -> list[str]:
        col = getattr(LeadStage, field, None)
        if col is None:
            return []
        stmt = (
            select(col)
            .where(LeadStage.deleted_at.is_(None), col.isnot(None))
            .distinct()
            .order_by(col)
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all() if row[0]]

    # ── Actions ──

    async def record_action(self, data: dict[str, Any]) -> LeadAction:
        action = LeadAction(**data)
        self.session.add(action)
        await self.session.flush()
        return action

    async def list_actions(self, lead_id: uuid.UUID, limit: int = 50) -> Sequence[LeadAction]:
        result = await self.session.execute(
            select(LeadAction)
            .where(LeadAction.lead_stage_id == lead_id)
            .order_by(desc(LeadAction.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    # ── Notes ──

    async def add_note(self, data: dict[str, Any]) -> LeadNote:
        note = LeadNote(**data)
        self.session.add(note)
        await self.session.flush()
        return note

    async def list_notes(self, lead_id: uuid.UUID, limit: int = 100) -> Sequence[LeadNote]:
        result = await self.session.execute(
            select(LeadNote)
            .where(LeadNote.lead_stage_id == lead_id, LeadNote.deleted_at.is_(None))
            .order_by(desc(LeadNote.is_pinned), desc(LeadNote.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def delete_note(self, note_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            update(LeadNote).where(LeadNote.id == note_id).values(deleted_at=datetime.now(UTC))
        )
        return result.rowcount > 0

    # ── Tasks ──

    async def add_task(self, data: dict[str, Any]) -> LeadTask:
        task = LeadTask(**data)
        self.session.add(task)
        await self.session.flush()
        return task

    async def list_tasks(self, lead_id: uuid.UUID, include_completed: bool = True) -> Sequence[LeadTask]:
        stmt = select(LeadTask).where(LeadTask.lead_stage_id == lead_id, LeadTask.deleted_at.is_(None))
        if not include_completed:
            stmt = stmt.where(LeadTask.completed == False)
        stmt = stmt.order_by(LeadTask.due_date, desc(LeadTask.priority))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def complete_task(self, task_id: uuid.UUID) -> LeadTask | None:
        result = await self.session.execute(
            select(LeadTask).where(LeadTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.completed = True
            task.completed_at = datetime.now(UTC)
            await self.session.flush()
        return task

    async def delete_task(self, task_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            update(LeadTask).where(LeadTask.id == task_id).values(deleted_at=datetime.now(UTC))
        )
        return result.rowcount > 0

    # ── Timeline ──

    async def add_timeline_event(self, data: dict[str, Any]) -> LeadTimeline:
        event = LeadTimeline(**data)
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_timeline(self, lead_id: uuid.UUID, limit: int = 100) -> Sequence[LeadTimeline]:
        result = await self.session.execute(
            select(LeadTimeline)
            .where(LeadTimeline.lead_stage_id == lead_id)
            .order_by(desc(LeadTimeline.created_at))
            .limit(limit)
        )
        return result.scalars().all()
