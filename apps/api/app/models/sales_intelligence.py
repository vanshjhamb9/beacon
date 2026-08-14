from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SalesIntelligenceSnapshot(BaseModel):
    """Append-only sales intelligence evaluation snapshot."""

    __tablename__ = "sales_intelligence_snapshots"
    __table_args__ = (
        Index("ix_si_snapshots_company_created", "company_id", "created_at"),
        Index("ix_si_snapshots_opportunity", "opportunity_id"),
        Index("ix_si_snapshots_intent", "buying_intent_score"),
        Index("ix_si_snapshots_deal", "deal_probability"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    buying_intent_score: Mapped[float] = mapped_column(Float, nullable=False)
    buying_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    urgency: Mapped[str] = mapped_column(String(32), nullable=False)
    budget_probability: Mapped[str] = mapped_column(String(32), nullable=False)
    decision_window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    primary_offer: Mapped[str] = mapped_column(String(128), nullable=False)
    expected_value: Mapped[str] = mapped_column(String(64), nullable=False)
    deal_probability: Mapped[float] = mapped_column(Float, nullable=False)
    close_probability: Mapped[float] = mapped_column(Float, nullable=False)
    sales_health: Mapped[float] = mapped_column(Float, nullable=False)
    relationship_health: Mapped[float] = mapped_column(Float, nullable=False)
    competition_risk: Mapped[float] = mapped_column(Float, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="si-v1")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SalesMemoryEventRow(BaseModel):
    """Append-only sales memory events (emails, replies, meetings, etc.)."""

    __tablename__ = "sales_memory_events"
    __table_args__ = (
        Index("ix_si_memory_company_occurred", "company_id", "occurred_at"),
        Index("ix_si_memory_type", "event_type"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    snapshot_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales_intelligence_snapshots.id")
    )
    event_key: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    refs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class SalesReplyIntelligenceRow(BaseModel):
    """Append-only reply classifications."""

    __tablename__ = "sales_reply_intelligence"
    __table_args__ = (
        Index("ix_si_reply_company_created", "company_id", "created_at"),
        Index("ix_si_reply_class", "classification"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    snapshot_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales_intelligence_snapshots.id")
    )
    reply_ref: Mapped[str | None] = mapped_column(String(128))
    classification: Mapped[str] = mapped_column(String(64), nullable=False)
    best_response: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    reply_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
