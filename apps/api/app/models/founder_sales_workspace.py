"""Founder Sales Workspace (FSW) models — Sprint 38."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LeadStage(BaseModel):
    """Pipeline stage for a lead in the FSW Kanban board."""
    __tablename__ = "fsw_lead_stages"
    __table_args__ = (
        Index("ix_fsw_lead_stages_company", "company_id"),
        Index("ix_fsw_lead_stages_stage", "stage"),
        Index("ix_fsw_lead_stages_owner", "owner"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    target_account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("target_accounts.id"))

    # Pipeline stage
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="revenue_ready")
    # revenue_ready | contacted | replied | meeting | proposal | negotiation | won | lost | archived | garbage

    # Manual status (independent of pipeline)
    manual_status: Mapped[str | None] = mapped_column(String(64))
    # hot | warm | cold | follow_up | waiting | done

    # Ownership
    owner: Mapped[str | None] = mapped_column(String(128))
    assigned_by: Mapped[str | None] = mapped_column(String(128))

    # Scores
    revenue_opportunity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    fit_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    intent_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    # Context
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(128))
    country: Mapped[str | None] = mapped_column(String(128))
    service_match: Mapped[str | None] = mapped_column(String(128))
    source_connector: Mapped[str | None] = mapped_column(String(64))
    trigger: Mapped[str | None] = mapped_column(String(64))
    why_now: Mapped[str | None] = mapped_column(Text)
    buying_signals: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)

    # Garbage
    garbage_reason: Mapped[str | None] = mapped_column(String(64))
    garbage_note: Mapped[str | None] = mapped_column(Text)
    garbage_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Snooze
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    snooze_reason: Mapped[str | None] = mapped_column(Text)

    # Archive
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Drag order within column
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Metadata
    tags: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class LeadAction(BaseModel):
    """Action taken on a lead (email, call, meeting, etc.)."""
    __tablename__ = "fsw_lead_actions"
    __table_args__ = (
        Index("ix_fsw_lead_actions_lead", "lead_stage_id"),
        Index("ix_fsw_lead_actions_type", "action_type"),
    )

    lead_stage_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fsw_lead_stages.id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # view | open_company | generate_email | generate_whatsapp | generate_proposal | schedule_meeting | add_note | assign | snooze | archive | move | delete | garbage

    performed_by: Mapped[str | None] = mapped_column(String(128))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    previous_stage: Mapped[str | None] = mapped_column(String(32))
    new_stage: Mapped[str | None] = mapped_column(String(32))


class LeadNote(BaseModel):
    """Unlimited timestamped notes on a lead."""
    __tablename__ = "fsw_lead_notes"
    __table_args__ = (
        Index("ix_fsw_lead_notes_lead", "lead_stage_id"),
    )

    lead_stage_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fsw_lead_stages.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(128))
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class LeadTask(BaseModel):
    """Follow-up tasks on a lead."""
    __tablename__ = "fsw_lead_tasks"
    __table_args__ = (
        Index("ix_fsw_lead_tasks_lead", "lead_stage_id"),
        Index("ix_fsw_lead_tasks_due", "due_date"),
        Index("ix_fsw_lead_tasks_completed", "completed"),
    )

    lead_stage_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fsw_lead_stages.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    # low | medium | high | urgent
    owner: Mapped[str | None] = mapped_column(String(128))
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LeadTimeline(BaseModel):
    """Append-only activity log for a lead."""
    __tablename__ = "fsw_lead_timeline"
    __table_args__ = (
        Index("ix_fsw_lead_timeline_lead", "lead_stage_id"),
        Index("ix_fsw_lead_timeline_created", "created_at"),
    )

    lead_stage_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fsw_lead_stages.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # stage_change | note_added | task_created | task_completed | action_performed | email_sent | meeting_scheduled | garbage | restored | assigned | status_change
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    actor: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
