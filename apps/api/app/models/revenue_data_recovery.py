from __future__ import annotations

from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RdiSnapshotRow(BaseModel):
    __tablename__ = "rdi_snapshots"
    __table_args__ = (
        Index("ix_rdi_snapshots_company_created", "company_id", "created_at"),
        Index("ix_rdi_snapshots_stage", "recovery_stage"),
        Index("ix_rdi_snapshots_rh", "eligible_for_revenue_hunter"),
        Index("ix_rdi_snapshots_sales_ready", "status"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    recovery_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    stars: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    identity_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    website_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_fake: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    eligible_for_revenue_hunter: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    visible_in_founder_queue: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), default="rdi-v1", nullable=False)


class RdiRecoveryQueueRow(BaseModel):
    __tablename__ = "rdi_recovery_queue"
    __table_args__ = (
        Index("ix_rdi_recovery_queue_stage_priority", "stage", "priority"),
        Index("ix_rdi_recovery_queue_company", "company_id"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    snapshot_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("rdi_snapshots.id"))
    company_name: Mapped[str] = mapped_column(String(512), nullable=False, default="UNKNOWN")
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    priority: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    next_action: Mapped[str] = mapped_column(String(512), nullable=False, default="UNKNOWN")
    blocked_reasons: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class RdiDossierRow(BaseModel):
    __tablename__ = "rdi_dossiers"
    __table_args__ = (Index("ix_rdi_dossiers_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    snapshot_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("rdi_snapshots.id"))
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    stars: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    estimated_deal: Mapped[str | None] = mapped_column(String(64))
    primary_service: Mapped[str | None] = mapped_column(String(255))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class RdiMetricsSnapshotRow(BaseModel):
    __tablename__ = "rdi_metrics_snapshots"
    __table_args__ = (Index("ix_rdi_metrics_created", "created_at"),)

    companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    identity_complete: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    website_verified: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sales_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fake_companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    founder_queue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recovery_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    duplicate_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), default="rdi-v1", nullable=False)
