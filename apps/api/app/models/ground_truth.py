from __future__ import annotations

from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class GtSnapshotRow(BaseModel):
    __tablename__ = "gt_snapshots"
    __table_args__ = (
        Index("ix_gt_snapshots_company_created", "company_id", "created_at"),
        Index("ix_gt_snapshots_verdict", "verdict"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    trust: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    readiness: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    lock_unlocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    questions_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), default="alpha-plus-v1", nullable=False)


class GtDailyReportRow(BaseModel):
    __tablename__ = "gt_daily_reports"
    __table_args__ = (Index("ix_gt_daily_reports_date", "report_date"),)

    report_date: Mapped[str] = mapped_column(String(32), nullable=False)
    collected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sales_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_quality: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), default="alpha-plus-v1", nullable=False)


class GtAcceptanceRow(BaseModel):
    __tablename__ = "gt_acceptance_gates"
    __table_args__ = (Index("ix_gt_acceptance_created", "created_at"),)

    production_unlocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failures: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), default="alpha-plus-v1", nullable=False)


class GtFounderQueueRow(BaseModel):
    __tablename__ = "gt_founder_queue"
    __table_args__ = (Index("ix_gt_fq_rank", "rank"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    trust: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), default="alpha-plus-v1", nullable=False)
