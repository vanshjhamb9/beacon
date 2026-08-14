from __future__ import annotations

from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RqpSnapshotRow(BaseModel):
    __tablename__ = "rqp_snapshots"
    __table_args__ = (
        Index("ix_rqp_snapshots_company_created", "company_id", "created_at"),
        Index("ix_rqp_snapshots_verdict", "verdict"),
        Index("ix_rqp_snapshots_surface", "surface_admitted"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    surface_admitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    surface_status: Mapped[str | None] = mapped_column(String(64))
    identity_accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sales_ready_badge: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), default="rqp-v1", nullable=False)


class RqpDailyKpiRow(BaseModel):
    __tablename__ = "rqp_daily_kpis"
    __table_args__ = (Index("ix_rqp_daily_kpis_created", "created_at"),)

    collected_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recovered_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    identity_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    website_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    contacts_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    decision_makers_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sales_ready_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    enterprise_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    duplicates: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fake_companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), default="rqp-v1", nullable=False)


class RqpAcceptanceRow(BaseModel):
    __tablename__ = "rqp_acceptance_gates"
    __table_args__ = (Index("ix_rqp_acceptance_created", "created_at"),)

    production_unlocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failures: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), default="rqp-v1", nullable=False)


class RqpGoldenDatasetRow(BaseModel):
    __tablename__ = "rqp_golden_dataset"
    __table_args__ = (Index("ix_rqp_golden_company", "company_id"),)

    company_id: Mapped[str] = mapped_column(String(64), nullable=False)
    company_name: Mapped[str] = mapped_column(String(512), nullable=False)
    website: Mapped[str] = mapped_column(String(512), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    linkedin_company: Mapped[str] = mapped_column(String(512), nullable=False)
    industry: Mapped[str] = mapped_column(String(128), nullable=False)
    country: Mapped[str] = mapped_column(String(64), nullable=False)
    employee_estimate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    benchmark_version: Mapped[str] = mapped_column(String(64), default="beacon-gold-v1", nullable=False)
