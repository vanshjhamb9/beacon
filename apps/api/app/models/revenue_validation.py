from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ClrOutcomeEvent(BaseModel):
    __tablename__ = "clr_outcome_events"

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    outreach_record_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    outcome: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_timestamp: Mapped[Any] = mapped_column(DateTime(timezone=True), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), default="founder", nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="clr", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ClrDailyBrief(BaseModel):
    __tablename__ = "clr_daily_briefs"

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    today_action: Mapped[str] = mapped_column(Text, default="", nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="clr-v1", nullable=False)


class ClrWeeklyReview(BaseModel):
    __tablename__ = "clr_weekly_reviews"

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="clr-v1", nullable=False)


class ClrRevenueEvent(BaseModel):
    __tablename__ = "clr_revenue_events"

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    service_sold: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    revenue_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    close_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sales_cycle_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    proposal_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expected_revenue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    actual_revenue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    founder: Mapped[str] = mapped_column(String(128), default="Vansh", nullable=False)
    source_connector: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    revenue_ready_snapshot_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ClrPredictionValidation(BaseModel):
    __tablename__ = "clr_prediction_validation"

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    interested: Mapped[str] = mapped_column(String(16), default="UNKNOWN", nullable=False)
    decision_maker_correct: Mapped[str] = mapped_column(String(16), default="UNKNOWN", nullable=False)
    why_now_accurate: Mapped[str] = mapped_column(String(16), default="UNKNOWN", nullable=False)
    service_accepted: Mapped[str] = mapped_column(String(16), default="UNKNOWN", nullable=False)
    confidence_realistic: Mapped[str] = mapped_column(String(16), default="UNKNOWN", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ClrLearningMetric(BaseModel):
    __tablename__ = "clr_learning_metrics"

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="clr-v1", nullable=False)


class ClrPipelineSnapshot(BaseModel):
    __tablename__ = "clr_pipeline_snapshots"

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="clr-v1", nullable=False)


class ClrFounderAction(BaseModel):
    __tablename__ = "clr_founder_actions"

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
