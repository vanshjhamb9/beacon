"""SQLAlchemy models for Opportunity Connector Platform (OCP v1)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ConnectorRegistryRow(BaseModel):
    __tablename__ = "connector_registry"
    __table_args__ = (
        Index("ix_connector_registry_connector_id", "connector_id", unique=True),
    )

    connector_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    configured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    healthy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    capabilities: Mapped[dict[str, Any]] = mapped_column(JSONB, default=list, nullable=False)
    average_latency: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    failure_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rate_limit_remaining: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    events_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    events_accepted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    events_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ConnectorRunRow(BaseModel):
    __tablename__ = "connector_runs"
    __table_args__ = (
        Index("ix_connector_runs_connector_id", "connector_id"),
        Index("ix_connector_runs_status", "status"),
    )

    connector_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    total_collected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_accepted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ConnectorEventRow(BaseModel):
    __tablename__ = "connector_events"
    __table_args__ = (
        Index("ix_connector_events_connector_id", "connector_id"),
        Index("ix_connector_events_event_type", "event_type"),
        Index("ix_connector_events_published_at", "published_at"),
        Index("ix_connector_events_accepted", "accepted"),
    )

    event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    connector_id: Mapped[str] = mapped_column(String(128), nullable=False)
    connector_version: Mapped[str] = mapped_column(String(32), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    headline: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    event_category: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    country: Mapped[str | None] = mapped_column(String(16), nullable=True)
    language: Mapped[str] = mapped_column(String(16), default="unknown", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    collector: Mapped[str] = mapped_column(String(128), nullable=False)
    routed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    route: Mapped[str] = mapped_column(String(128), default="live_opportunity_discovery", nullable=False)


class ConnectorStatisticsRow(BaseModel):
    __tablename__ = "connector_statistics"
    __table_args__ = (
        Index("ix_connector_statistics_connector_id", "connector_id"),
        Index("ix_connector_statistics_period", "period"),
        {"extend_existing": True},
    )

    connector_id: Mapped[str] = mapped_column(String(128), nullable=False)
    period: Mapped[str] = mapped_column(String(32), nullable=False)
    signals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accepted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    identity_matched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified_companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sales_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contacted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    replies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    meetings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    won: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    acceptance_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    signal_yield: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    revenue_yield: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    meeting_yield: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    revenue_per_signal: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ConnectorHealthRow(BaseModel):
    __tablename__ = "connector_health"
    __table_args__ = (
        Index("ix_connector_health_connector_id", "connector_id", unique=True),
        {"extend_existing": True},
    )

    connector_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    authenticated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rate_limit_remaining: Mapped[int | None] = mapped_column(Integer, nullable=True)
    queue_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    freshness_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_success: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ConnectorYieldRow(BaseModel):
    __tablename__ = "connector_yield"
    __table_args__ = (
        Index("ix_connector_yield_connector_id", "connector_id", unique=True),
    )

    connector_id: Mapped[str] = mapped_column(String(128), nullable=False)
    signals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accepted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    identity_matched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified_companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sales_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contacted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    replies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    meetings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    won: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    signal_yield: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    revenue_yield: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    meeting_yield: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    acceptance_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    revenue_per_signal: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ConnectorConfigurationRow(BaseModel):
    __tablename__ = "connector_configuration"
    __table_args__ = (
        Index("ix_connector_configuration_connector_id", "connector_id", unique=True),
    )

    connector_id: Mapped[str] = mapped_column(String(128), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    interval: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), default="normal", nullable=False)
    rate_limit: Mapped[str] = mapped_column(String(128), default="unknown", nullable=False)
    authentication: Mapped[str] = mapped_column(String(32), default="none", nullable=False)
    timeout: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    max_concurrency: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    dependencies: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    retry_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_backoff_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    config_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, nullable=False)


class ConnectorFailureRow(BaseModel):
    __tablename__ = "connector_failures"
    __table_args__ = (
        Index("ix_connector_failures_connector_id", "connector_id"),
        Index("ix_connector_failures_error_type", "error_type"),
    )

    connector_id: Mapped[str] = mapped_column(String(128), nullable=False)
    error_type: Mapped[str] = mapped_column(String(128), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    run_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ConnectorRateLimitRow(BaseModel):
    __tablename__ = "connector_rate_limits"
    __table_args__ = (
        Index("ix_connector_rate_limits_connector_id", "connector_id", unique=True),
    )

    connector_id: Mapped[str] = mapped_column(String(128), nullable=False)
    limit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    remaining: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ConnectorCapabilityRow(BaseModel):
    __tablename__ = "connector_capabilities"
    __table_args__ = (
        Index("ix_connector_capabilities_connector_id", "connector_id", unique=True),
    )

    connector_id: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    event_types: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    emits_evidence_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_incremental_sync: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_historical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_batch_size: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    requires_authentication: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
