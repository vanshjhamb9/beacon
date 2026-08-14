from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class FounderDailyBriefRow(BaseModel):
    __tablename__ = "founder_daily_briefs"
    __table_args__ = (Index("ix_founder_daily_briefs_created", "created_at"),)

    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    new_companies_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_buying_signals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    qualified_companies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sales_ready_accounts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    a_plus_opportunities: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    campaigns_waiting_approval: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    replies_waiting: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meetings_today: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    proposals_pending: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_pipeline: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    expected_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    lost_opportunities: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    won_opportunities: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    top_performing_industry: Mapped[str | None] = mapped_column(String(128))
    top_performing_service: Mapped[str | None] = mapped_column(String(128))
    top_performing_outreach_style: Mapped[str | None] = mapped_column(String(128))
    top_performing_subject_line: Mapped[str | None] = mapped_column(String(255))
    top_performing_cta: Mapped[str | None] = mapped_column(String(255))
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="fos-v1")


class FounderRevenueTaskRow(BaseModel):
    __tablename__ = "founder_revenue_tasks"
    __table_args__ = (
        Index("ix_founder_tasks_status_priority", "status", "priority"),
        Index("ix_founder_tasks_company", "company_id"),
    )

    task_key: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(8), nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    owner: Mapped[str] = mapped_column(String(128), nullable=False, default="founder")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    company_name: Mapped[str | None] = mapped_column(String(255))
    related_id: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class FounderTimelineEventRow(BaseModel):
    """Append-only immutable revenue timeline events."""

    __tablename__ = "founder_timeline_events"
    __table_args__ = (
        Index("ix_founder_timeline_company_occurred", "company_id", "occurred_at"),
        Index("ix_founder_timeline_stage", "stage"),
    )

    event_key: Mapped[str] = mapped_column(String(64), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FounderAnalyticsEventRow(BaseModel):
    """Append-only founder action analytics."""

    __tablename__ = "founder_analytics_events"
    __table_args__ = (
        Index("ix_founder_analytics_type_created", "event_type", "created_at"),
        Index("ix_founder_analytics_company", "company_id"),
    )

    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False, default="founder")
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    entity_type: Mapped[str | None] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(128))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
