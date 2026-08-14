from __future__ import annotations

from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AlphaSnapshotRow(BaseModel):
    __tablename__ = "alpha_snapshots"
    __table_args__ = (
        Index("ix_alpha_snapshots_company_created", "company_id", "created_at"),
        Index("ix_alpha_snapshots_verdict", "verdict"),
        Index("ix_alpha_snapshots_score", "score_total"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    score_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    founder_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    best_service: Mapped[str | None] = mapped_column(String(255))
    primary_bucket: Mapped[str | None] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), default="alpha-v1", nullable=False)


class AlphaQaDecisionRow(BaseModel):
    __tablename__ = "alpha_qa_decisions"
    __table_args__ = (
        Index("ix_alpha_qa_company", "company_id"),
        Index("ix_alpha_qa_rating", "rating"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    rating: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    reviewer: Mapped[str | None] = mapped_column(String(128))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class AlphaAcceptanceRow(BaseModel):
    __tablename__ = "alpha_acceptance_gates"
    __table_args__ = (Index("ix_alpha_acceptance_created", "created_at"),)

    live_outreach_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failures: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), default="alpha-v1", nullable=False)


class AlphaFounderQueueRow(BaseModel):
    __tablename__ = "alpha_founder_queue"
    __table_args__ = (Index("ix_alpha_fq_score", "score"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), default="alpha-v1", nullable=False)
