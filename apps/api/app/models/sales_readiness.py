from __future__ import annotations

from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SalesReadinessSnapshotRow(BaseModel):
    __tablename__ = "sales_readiness_snapshots"
    __table_args__ = (
        Index("ix_sales_readiness_snapshots_company_created", "company_id", "created_at"),
        Index("ix_sales_readiness_snapshots_status", "status"),
        Index("ix_sales_readiness_snapshots_rh", "eligible_for_revenue_hunter"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    stars: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    eligible_for_revenue_hunter: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    visible_in_founder_queue: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), default="sre-v1", nullable=False)


class SalesIdentityScoreRow(BaseModel):
    __tablename__ = "sales_identity_scores"

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    snapshot_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_readiness_snapshots.id"))
    identity_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    missing_fields: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SalesContactReadinessRow(BaseModel):
    __tablename__ = "sales_contact_readiness"

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    snapshot_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_readiness_snapshots.id"))
    coverage_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    verified_email_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified_phone_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SalesIntentScoreRow(BaseModel):
    __tablename__ = "sales_intent_scores"

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    snapshot_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_readiness_snapshots.id"))
    level: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SalesServiceMatchV2Row(BaseModel):
    __tablename__ = "sales_service_matches_v2"

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    snapshot_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_readiness_snapshots.id"))
    recommended_service: Mapped[str] = mapped_column(String(255), nullable=False)
    estimated_value: Mapped[str | None] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reason: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class SalesRevenuePotentialRow(BaseModel):
    __tablename__ = "sales_revenue_potential"

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    snapshot_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_readiness_snapshots.id"))
    deal_size: Mapped[str] = mapped_column(String(32), nullable=False)
    probability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sales_cycle: Mapped[str | None] = mapped_column(String(32))
    recommended_founder_time: Mapped[str | None] = mapped_column(String(32))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SalesTrustScoreRow(BaseModel):
    __tablename__ = "sales_trust_scores"

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    snapshot_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_readiness_snapshots.id"))
    overall: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
