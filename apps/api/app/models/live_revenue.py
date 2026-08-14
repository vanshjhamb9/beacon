from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LiveRevenueRun(BaseModel):
    """Append-only LRE evaluation / execution snapshot."""

    __tablename__ = "live_revenue_runs"
    __table_args__ = (
        Index("ix_lre_runs_company_created", "company_id", "created_at"),
        Index("ix_lre_runs_campaign", "campaign_id"),
        Index("ix_lre_runs_stage", "stage"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    campaign_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="lre-v1")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class LiveRevenueLifecycleEvent(BaseModel):
    """Append-only campaign/LRE lifecycle transitions."""

    __tablename__ = "live_revenue_lifecycle_events"
    __table_args__ = (
        Index("ix_lre_lifecycle_company_occurred", "company_id", "occurred_at"),
        Index("ix_lre_lifecycle_stage", "stage"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    campaign_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    run_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("live_revenue_runs.id"))
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    actor: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class LiveRevenueTrackingEvent(BaseModel):
    """Open / click / bounce / unsubscribe tracking events."""

    __tablename__ = "live_revenue_tracking_events"
    __table_args__ = (
        Index("ix_lre_tracking_id_created", "tracking_id", "created_at"),
        Index("ix_lre_tracking_type", "event_type"),
    )

    tracking_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    campaign_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    target_url: Mapped[str | None] = mapped_column(Text)
    provider_response: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class LiveRevenueProposalVersion(BaseModel):
    """Append-only proposal versions with tracking."""

    __tablename__ = "live_revenue_proposal_versions"
    __table_args__ = (
        Index("ix_lre_proposal_company_version", "company_id", "version"),
        Index("ix_lre_proposal_tracking", "tracking_id"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    campaign_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    tracking_id: Mapped[str] = mapped_column(String(64), nullable=False)
    pricing: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    pdf_base64: Mapped[str | None] = mapped_column(Text)
    opens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    downloads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
