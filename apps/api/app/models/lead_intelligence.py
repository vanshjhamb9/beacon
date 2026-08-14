"""SQLAlchemy models for Lead Intelligence Explorer (LIX v1) — append-only."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LeadEvent(BaseModel):
    __tablename__ = "lead_events"
    __table_args__ = (
        Index("ix_lead_events_company_occurred", "company_id", "occurred_at"),
        Index("ix_lead_events_dedupe_key", "dedupe_key", unique=True),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    lead_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    stage: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str | None] = mapped_column(String(32))
    headline: Mapped[str] = mapped_column(Text, default="", nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="", nullable=False)
    connector: Mapped[str | None] = mapped_column(String(64))
    provider: Mapped[str | None] = mapped_column(String(64))
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    dedupe_key: Mapped[str] = mapped_column(String(191), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class LeadStageHistory(BaseModel):
    __tablename__ = "lead_stage_history"
    __table_args__ = (
        Index("ix_lead_stage_history_company_stage", "company_id", "stage"),
        Index("ix_lead_stage_history_dedupe_key", "dedupe_key", unique=True),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    lead_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="passed", nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    entered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    exited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    filters_passed: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    filters_failed: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(191), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class LeadProviderHistory(BaseModel):
    __tablename__ = "lead_provider_history"
    __table_args__ = (
        Index("ix_lead_provider_history_dedupe_key", "dedupe_key", unique=True),
    )

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    lead_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    latency_ms: Mapped[float | None] = mapped_column(Float)
    fields_added: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    credits_used: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float | None] = mapped_column(Float)
    detail: Mapped[str] = mapped_column(Text, default="", nullable=False)
    revenue_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(191), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class LeadScoreBreakdown(BaseModel):
    __tablename__ = "lead_score_breakdown"
    __table_args__ = (
        Index("ix_lead_score_breakdown_dedupe_key", "dedupe_key", unique=True),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    lead_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    component_key: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    points: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    present: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    total_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(191), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class LeadFieldHistory(BaseModel):
    __tablename__ = "lead_field_history"
    __table_args__ = (
        Index("ix_lead_field_history_company_field", "company_id", "field_name"),
        Index("ix_lead_field_history_dedupe_key", "dedupe_key", unique=True),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    lead_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    field_name: Mapped[str] = mapped_column(String(128), nullable=False)
    field_value: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(64), default="internal", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024))
    evidence_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(191), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class LeadEvidenceChain(BaseModel):
    __tablename__ = "lead_evidence_chain"
    __table_args__ = (
        Index("ix_lead_evidence_chain_dedupe_key", "dedupe_key", unique=True),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    lead_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    url: Mapped[str | None] = mapped_column(String(1024))
    snippet: Mapped[str] = mapped_column(Text, default="", nullable=False)
    provider: Mapped[str | None] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(191), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
