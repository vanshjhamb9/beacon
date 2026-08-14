"""SQLAlchemy models for Beacon Operations Center (BOC v1)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class PipelineStageMetric(BaseModel):
    __tablename__ = "pipeline_stage_metrics"
    __table_args__ = (
        Index("ix_pipeline_stage_metrics_stage_created", "stage", "created_at"),
    )

    stage: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hour: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ConnectorHealthRow(BaseModel):
    __tablename__ = "connector_health"
    __table_args__ = (
        Index("ix_connector_health_connector", "connector", unique=True),
        {"extend_existing": True},
    )

    connector: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    healthy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    success_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_runtime: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rate_limited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="", nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class WorkerHealthRow(BaseModel):
    __tablename__ = "worker_health"
    __table_args__ = (
        Index("ix_worker_health_worker_name", "worker_name", unique=True),
    )

    worker_name: Mapped[str] = mapped_column(String(64), nullable=False)
    running: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    queue_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    jobs_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    jobs_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_execution: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class OperationSnapshot(BaseModel):
    __tablename__ = "operation_snapshots"
    __table_args__ = (
        Index("ix_operation_snapshots_created_at", "created_at"),
    )

    signals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified_companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    emails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    decision_makers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sales_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class IngestionEvent(BaseModel):
    __tablename__ = "ingestion_events"
    __table_args__ = (
        Index("ix_ingestion_events_collector_created", "collector", "created_at"),
        Index("ix_ingestion_events_status_created", "status", "created_at"),
    )

    collector: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    company: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    duration: Mapped[float | None] = mapped_column(Float)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
