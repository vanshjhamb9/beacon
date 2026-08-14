"""SQLAlchemy models for Beacon Validation & Continuous Learning Platform (BVCL v1)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ValidationEvent(BaseModel):
    __tablename__ = "validation_events"
    __table_args__ = (
        Index("ix_validation_events_company_stage", "company_id", "stage"),
        Index("ix_validation_events_stage_created", "stage", "created_at"),
        Index("ix_validation_events_source_created", "source", "created_at"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class LeadOutcome(BaseModel):
    __tablename__ = "lead_outcomes"
    __table_args__ = (
        Index("ix_lead_outcomes_company_id", "company_id"),
        Index("ix_lead_outcomes_status_created", "status", "created_at"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    expected_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    service_sold: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ReplyEvent(BaseModel):
    __tablename__ = "reply_events"
    __table_args__ = (
        Index("ix_reply_events_company_id", "company_id"),
        Index("ix_reply_events_reply_type_created", "reply_type", "created_at"),
        Index("ix_reply_events_source_created", "source", "created_at"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    reply_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    reply_time_seconds: Mapped[float | None] = mapped_column(Float)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class MeetingEvent(BaseModel):
    __tablename__ = "meeting_events"
    __table_args__ = (
        Index("ix_meeting_events_company_id", "company_id"),
        Index("ix_meeting_events_meeting_type_created", "meeting_type", "created_at"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    meeting_type: Mapped[str] = mapped_column(String(64), nullable=False)
    duration_minutes: Mapped[float | None] = mapped_column(Float)
    calendar_link: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    next_action: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ProposalEvent(BaseModel):
    __tablename__ = "proposal_events"
    __table_args__ = (
        Index("ix_proposal_events_company_id", "company_id"),
        Index("ix_proposal_events_status_created", "status", "created_at"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class DealEvent(BaseModel):
    __tablename__ = "deal_events"
    __table_args__ = (
        Index("ix_deal_events_company_id", "company_id"),
        Index("ix_deal_events_status_created", "status", "created_at"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    expected_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    service_sold: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ValidationTimeline(BaseModel):
    __tablename__ = "validation_timelines"
    __table_args__ = (
        Index("ix_validation_timelines_company_stage", "company_id", "stage"),
        Index("ix_validation_timelines_company_created", "company_id", "created_at"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ConnectorRoiRow(BaseModel):
    __tablename__ = "connector_roi"
    __table_args__ = (
        Index("ix_connector_roi_connector", "connector", unique=True),
    )

    connector: Mapped[str] = mapped_column(String(64), nullable=False)
    signals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    companies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue_ready: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    replies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meetings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reply_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    meeting_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ServiceRoiRow(BaseModel):
    __tablename__ = "service_roi"
    __table_args__ = (
        Index("ix_service_roi_service", "service", unique=True),
    )

    service: Mapped[str] = mapped_column(String(255), nullable=False)
    companies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    replies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meetings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reply_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    meeting_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    proposal_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class IndustryRoiRow(BaseModel):
    __tablename__ = "industry_roi"
    __table_args__ = (
        Index("ix_industry_roi_industry", "industry", unique=True),
    )

    industry: Mapped[str] = mapped_column(String(128), nullable=False)
    companies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue_ready: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    replies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meetings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reply_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    meeting_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class PersonaRoiRow(BaseModel):
    __tablename__ = "persona_roi"
    __table_args__ = (
        Index("ix_persona_roi_persona", "persona", unique=True),
    )

    persona: Mapped[str] = mapped_column(String(128), nullable=False)
    contacted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    replies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meetings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reply_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    meeting_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class TriggerRoiRow(BaseModel):
    __tablename__ = "trigger_roi"
    __table_args__ = (
        Index("ix_trigger_roi_trigger", "trigger", unique=True),
    )

    trigger: Mapped[str] = mapped_column(String(64), nullable=False)
    companies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    replies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meetings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reply_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    meeting_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    revenue_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ObjectionEvent(BaseModel):
    __tablename__ = "objection_events"
    __table_args__ = (
        Index("ix_objection_events_company_id", "company_id"),
        Index("ix_objection_events_category_created", "category", "created_at"),
        Index("ix_objection_events_industry_created", "industry", "created_at"),
        Index("ix_objection_events_service_created", "service", "created_at"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    industry: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    service: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    connector: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    persona: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ValidationSnapshot(BaseModel):
    __tablename__ = "validation_snapshots"
    __table_args__ = (
        Index("ix_validation_snapshots_created_at", "created_at"),
    )

    total_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_deal_size: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reply_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    meeting_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    proposal_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_won: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_lost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_replies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_meetings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_proposals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
