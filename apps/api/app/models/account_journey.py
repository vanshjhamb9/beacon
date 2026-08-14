from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AccountJourneyRow(BaseModel):
    __tablename__ = "account_journeys"
    __table_args__ = (
        Index("ix_goi_journeys_company_created", "company_id", "created_at"),
        Index("ix_goi_journeys_stage", "stage"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    health_category: Mapped[str] = mapped_column(String(32), nullable=False, default="cold")
    overall_engagement: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="goi-v1")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class EngagementScoreRow(BaseModel):
    __tablename__ = "engagement_scores"
    __table_args__ = (Index("ix_goi_engagement_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    journey_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("account_journeys.id"))
    open_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reply_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    intent_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    meeting_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    relationship_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    account_temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overall_engagement: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class AccountHealthSnapshot(BaseModel):
    __tablename__ = "account_health_snapshots"
    __table_args__ = (Index("ix_goi_health_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    journey_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("account_journeys.id"))
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class BuyingCommitteeRow(BaseModel):
    __tablename__ = "buying_committees"
    __table_args__ = (Index("ix_goi_committee_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    journey_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("account_journeys.id"))
    coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    members: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    missing_roles: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class FollowUpPlanRow(BaseModel):
    __tablename__ = "followup_plans"
    __table_args__ = (Index("ix_goi_followup_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    journey_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("account_journeys.id"))
    next_action: Mapped[str] = mapped_column(String(128), nullable=False)
    channel: Mapped[str] = mapped_column(String(64), nullable=False)
    message_type: Mapped[str] = mapped_column(String(64), nullable=False)
    urgency: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    best_timing_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    requires_founder_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class ReplyClassificationRow(BaseModel):
    __tablename__ = "reply_classifications"
    __table_args__ = (Index("ix_goi_reply_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    journey_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("account_journeys.id"))
    classification: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    structured_outcome: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class AccountTimelineRow(BaseModel):
    __tablename__ = "account_timelines"
    __table_args__ = (Index("ix_goi_timeline_company_occurred", "company_id", "occurred_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    journey_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("account_journeys.id"))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    actor: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CampaignAnalyticsSnapshot(BaseModel):
    __tablename__ = "campaign_analytics_snapshots"
    __table_args__ = (Index("ix_goi_analytics_created", "created_at"),)

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="goi-v1")
