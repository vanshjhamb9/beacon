from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RevenueOperationSnapshot(BaseModel):
    __tablename__ = "revenue_operation_snapshots"
    __table_args__ = (Index("ix_roc_snapshots_created", "created_at"),)

    revenue_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pipeline_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    expected_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roc-v1")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RevenueAlertRow(BaseModel):
    __tablename__ = "revenue_alerts"
    __table_args__ = (
        Index("ix_roc_alerts_lifecycle_created", "lifecycle", "created_at"),
        Index("ix_roc_alerts_dedupe", "dedupe_key"),
    )

    alert_id: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    company_name: Mapped[str | None] = mapped_column(String(255))
    recommendation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    lifecycle: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    dedupe_key: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    snapshot_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("revenue_operation_snapshots.id"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RevenueForecastRow(BaseModel):
    __tablename__ = "revenue_forecasts"
    __table_args__ = (Index("ix_roc_forecasts_created", "created_at"),)

    this_week: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    this_month: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    quarter: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    annual: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pipeline_health: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roc-v1")


class RevenueMemoryRow(BaseModel):
    __tablename__ = "revenue_memory"
    __table_args__ = (
        Index("ix_roc_memory_type_created", "record_type", "created_at"),
        Index("ix_roc_memory_company", "company_id"),
    )

    record_type: Mapped[str] = mapped_column(String(64), nullable=False)
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    company_name: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    searchable_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class RevenueReplayRow(BaseModel):
    __tablename__ = "revenue_replays"
    __table_args__ = (
        Index("ix_roc_replays_company", "company_id"),
        Index("ix_roc_replays_opportunity", "opportunity_id"),
    )

    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(32))
    events: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roc-v1")


class RevenueMetricRow(BaseModel):
    __tablename__ = "revenue_operation_metrics"
    __table_args__ = (Index("ix_roc_metrics_created", "created_at"),)

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    close_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reply_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    meeting_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roc-v1")


class LearningRecommendationRow(BaseModel):
    __tablename__ = "revenue_operation_learning"
    __table_args__ = (
        Index("ix_roc_learning_status_created", "status", "created_at"),
        Index("ix_roc_learning_rec_id", "recommendation_id"),
    )

    recommendation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_approval")
    modifies_production: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[str | None] = mapped_column(String(128))


class AgencyStatisticRow(BaseModel):
    __tablename__ = "agency_statistics"
    __table_args__ = (Index("ix_roc_agency_stats_created", "created_at"),)

    kind: Mapped[str] = mapped_column(String(64), nullable=False, default="daily")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roc-v1")
