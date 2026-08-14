from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ProductionValidationSnapshot(BaseModel):
    """Append-only production validation / readiness snapshots."""

    __tablename__ = "production_validation_snapshots"
    __table_args__ = (
        Index("ix_prv_snapshots_created", "created_at"),
        Index("ix_prv_snapshots_score", "overall_score"),
    )

    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="prrv-v1")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ProductionAlertRow(BaseModel):
    __tablename__ = "production_alerts"
    __table_args__ = (
        Index("ix_prv_alerts_severity_created", "severity", "created_at"),
        Index("ix_prv_alerts_code", "code"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(String(128), nullable=False, default="founder")
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    snapshot_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("production_validation_snapshots.id")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LeadReadinessRow(BaseModel):
    __tablename__ = "lead_readiness_scores"
    __table_args__ = (
        Index("ix_prv_lead_company_created", "company_id", "created_at"),
        Index("ix_prv_lead_score", "score"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    outreach_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    checklist: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    blocking_reasons: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    snapshot_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("production_validation_snapshots.id")
    )
