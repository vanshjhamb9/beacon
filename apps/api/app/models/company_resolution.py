from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CreSnapshotRow(BaseModel):
    __tablename__ = "cre_snapshots"

    signal_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    raw_event_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"))
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    company_name: Mapped[str | None] = mapped_column(String(255))
    company_domain: Mapped[str | None] = mapped_column(String(255), index=True)
    identity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    website_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    admitted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rejection_explanation: Mapped[str | None] = mapped_column(Text)
    attribution_url: Mapped[str | None] = mapped_column(String(1024))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), nullable=False, default="cre-v1")


class CreAdmissionDecisionRow(BaseModel):
    __tablename__ = "cre_admission_decisions"

    signal_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    raw_event_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"))
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    admitted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reasons: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), nullable=False, default="cre-v1")


class CreRebuildReportRow(BaseModel):
    __tablename__ = "cre_rebuild_reports"

    total_raw_signals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resolved_companies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verified_companies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sales_ready: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    companies_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    companies_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resolution_success_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rejection_reasons: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    identity_confidence_distribution: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    source_precision: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    top_verified: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    rejected_examples: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), nullable=False, default="cre-v1")
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
