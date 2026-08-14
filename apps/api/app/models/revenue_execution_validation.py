from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RevEvaluationRow(BaseModel):
    __tablename__ = "rev_evaluations"

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    is_revenue_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="rev-v1", nullable=False)


class RevRejectionRecordRow(BaseModel):
    __tablename__ = "rev_rejection_records"

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    company_name: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str | None] = mapped_column(String(64), index=True)
    industry: Mapped[str | None] = mapped_column(String(128))
    reasons: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RevFunnelSnapshotRow(BaseModel):
    __tablename__ = "rev_funnel_snapshots"

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    founder_queue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="rev-v1", nullable=False)


class RevConnectorScoreRow(BaseModel):
    __tablename__ = "rev_connector_scores"

    connector: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    grade: Mapped[str] = mapped_column(String(32), nullable=False)
    revenue_ready_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RevFounderQueueCardRow(BaseModel):
    __tablename__ = "rev_founder_queue_cards"

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="rev-v1", nullable=False)


class RevManualQaRow(BaseModel):
    __tablename__ = "rev_manual_qa"

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    company_name: Mapped[str | None] = mapped_column(String(255))
    rating: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reviewer: Mapped[str | None] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RevDailyReportRow(BaseModel):
    __tablename__ = "rev_daily_reports"

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="rev-v1", nullable=False)


class RevAcceptanceGateRow(BaseModel):
    __tablename__ = "rev_acceptance_gates"

    production_unlocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failures: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="rev-v1", nullable=False)
