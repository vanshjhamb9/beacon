from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RevenueHunterDossier(BaseModel):
    __tablename__ = "revenue_hunter_dossiers"
    __table_args__ = (
        Index("ix_rh_dossiers_grade_score", "priority_grade", "revenue_score"),
        Index("ix_rh_dossiers_company", "company_id"),
        Index("ix_rh_dossiers_campaign", "proceed_to_campaign", "priority_grade"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(128))
    country: Mapped[str | None] = mapped_column(String(128))
    company_size_band: Mapped[str | None] = mapped_column(String(32))
    funding_stage: Mapped[str | None] = mapped_column(String(64))
    revenue_band: Mapped[str | None] = mapped_column(String(64))
    filter_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    filter_match: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    recommended_service: Mapped[str] = mapped_column(String(128), nullable=False)
    service_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    service_matches: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    pain_points: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    website_intelligence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    why_now: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    dossier: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    priority_grade: Mapped[str] = mapped_column(String(8), nullable=False)
    revenue_score: Mapped[float] = mapped_column(Float, nullable=False)
    expected_budget: Mapped[str] = mapped_column(String(64), nullable=False)
    expected_timeline: Mapped[str] = mapped_column(String(255), nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    proceed_to_campaign: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    work_queue_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    score_breakdown: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    explanations: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RevenueHunterWorkQueueItem(BaseModel):
    __tablename__ = "revenue_hunter_work_queue"
    __table_args__ = (
        Index("ix_rh_work_queue_status_rank", "status", "rank"),
        Index("ix_rh_work_queue_company", "company_id"),
    )

    dossier_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("revenue_hunter_dossiers.id")
    )
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority_grade: Mapped[str] = mapped_column(String(8), nullable=False)
    recommended_service: Mapped[str] = mapped_column(String(128), nullable=False)
    why_today: Mapped[str] = mapped_column(Text, nullable=False)
    expected_budget: Mapped[str] = mapped_column(String(64), nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    primary_contact: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    allowed_actions: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    action_log: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    acted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RevenueHunterDailyBrief(BaseModel):
    __tablename__ = "revenue_hunter_daily_briefs"
    __table_args__ = (Index("ix_rh_daily_briefs_created", "created_at"),)

    expected_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    expected_pipeline: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    meetings_today: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    campaign_queue: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reply_queue: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    follow_ups: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hot_opportunities: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    top_25: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    todays_targets: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
