from __future__ import annotations

from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class PhAdmissionDecision(BaseModel):
    __tablename__ = "ph_admission_decisions"
    __table_args__ = (
        Index("ix_ph_admission_decisions_verdict_created", "verdict", "created_at"),
        Index("ix_ph_admission_decisions_company", "company_id"),
    )

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    reasons: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class PhContactReadiness(BaseModel):
    __tablename__ = "ph_contact_readiness"
    __table_args__ = (
        Index("ix_ph_contact_readiness_company_created", "company_id", "created_at"),
        Index("ix_ph_contact_readiness_status", "status"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    lead_quality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    founder_queue_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class PhCompanyMerge(BaseModel):
    __tablename__ = "ph_company_merges"
    __table_args__ = (Index("ix_ph_company_merges_canonical", "canonical_company_id"),)

    canonical_company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    merged_company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    match_keys: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class PhTrustSnapshot(BaseModel):
    __tablename__ = "ph_trust_snapshots"

    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), default="ph1-v1", nullable=False)
