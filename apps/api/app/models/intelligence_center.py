"""SQLAlchemy models for Beacon Intelligence Center (BIC v1)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Date, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class DiscoveryEvent(BaseModel):
    __tablename__ = "discovery_events"
    __table_args__ = (
        Index("ix_discovery_events_created_at", "created_at"),
        Index("ix_discovery_events_event_type_created", "event_type", "created_at"),
        Index("ix_discovery_events_company_id", "company_id"),
        Index("ix_discovery_events_dedupe_key", "dedupe_key", unique=True),
    )

    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(128))
    collector: Mapped[str | None] = mapped_column(String(64), index=True)
    connector: Mapped[str | None] = mapped_column(String(64), index=True)
    status: Mapped[str | None] = mapped_column(String(64))
    headline: Mapped[str] = mapped_column(Text, default="", nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="", nullable=False)
    score: Mapped[float | None] = mapped_column(Float)
    is_error: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_revenue_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    dedupe_key: Mapped[str] = mapped_column(String(191), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class CompanyJourneyEvent(BaseModel):
    __tablename__ = "company_journey_events"
    __table_args__ = (
        Index("ix_company_journey_events_company_stage", "company_id", "stage"),
        Index("ix_company_journey_events_dedupe_key", "dedupe_key", unique=True),
        Index("ix_company_journey_events_occurred_at", "occurred_at"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    connector: Mapped[str | None] = mapped_column(String(64))
    worker: Mapped[str | None] = mapped_column(String(64))
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failures: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="", nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(191), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ConnectorRoiDaily(BaseModel):
    __tablename__ = "connector_roi_daily"
    __table_args__ = (
        Index("ix_connector_roi_daily_connector_date", "connector", "report_date", unique=True),
    )

    connector: Mapped[str] = mapped_column(String(64), nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    healthy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    signals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    emails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    decision_makers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    meetings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    win_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    api_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    quota_used_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    success_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class DatasetStatisticsDaily(BaseModel):
    __tablename__ = "dataset_statistics_daily"
    __table_args__ = (
        Index("ix_dataset_statistics_daily_report_date", "report_date", unique=True),
    )

    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    signals_collected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicates: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spam: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dead_websites: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    working_websites: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    emails_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified_emails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generic_emails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    founder_emails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    decision_makers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    outreach_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    spam_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    verification_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    enrichment_coverage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class PipelineReplayFrame(BaseModel):
    __tablename__ = "pipeline_replay_frames"
    __table_args__ = (
        Index("ix_pipeline_replay_frames_hour_key", "hour_key", unique=True),
        Index("ix_pipeline_replay_frames_frame_at", "frame_at"),
    )

    hour_key: Mapped[str] = mapped_column(String(32), nullable=False)
    frame_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    signals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    websites: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    emails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    decision_makers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sales_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contacted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    movements: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
