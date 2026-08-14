from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ICPProfileRow(BaseModel):
    __tablename__ = "icp_profiles"
    __table_args__ = (
        UniqueConstraint("key", name="uq_icp_profiles_key"),
        Index("ix_icp_profiles_priority_active", "priority", "is_active"),
    )

    key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    service_match: Mapped[str] = mapped_column(String(128), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    company_size_min: Mapped[int | None] = mapped_column(Integer)
    company_size_max: Mapped[int | None] = mapped_column(Integer)
    employee_count_min: Mapped[int | None] = mapped_column(Integer)
    employee_count_max: Mapped[int | None] = mapped_column(Integer)
    industries: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    revenue_bands: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    countries: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    funding_stages: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    hiring_signals: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    technology_stack: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    business_models: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    growth_signals: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    decision_makers: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    pain_points: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    buying_signals: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    negative_signals: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class TargetAccount(BaseModel):
    __tablename__ = "target_accounts"
    __table_args__ = (
        Index("ix_target_accounts_score", "revenue_opportunity_score"),
        Index("ix_target_accounts_tier_score", "tier", "revenue_opportunity_score"),
        Index("ix_target_accounts_company", "company_id"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    icp_profile_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("icp_profiles.id"))
    matched_icp_key: Mapped[str | None] = mapped_column(String(128))
    matched_icp_name: Mapped[str | None] = mapped_column(String(255))
    service_match: Mapped[str | None] = mapped_column(String(128))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(128))
    country: Mapped[str | None] = mapped_column(String(128))
    fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    intent_score: Mapped[float] = mapped_column(Float, nullable=False)
    budget_score: Mapped[float] = mapped_column(Float, nullable=False)
    budget_band: Mapped[str | None] = mapped_column(String(32))
    urgency_score: Mapped[float] = mapped_column(Float, nullable=False)
    accessibility_score: Mapped[float] = mapped_column(Float, nullable=False)
    competition_score: Mapped[float] = mapped_column(Float, nullable=False)
    revenue_opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)
    tier: Mapped[str] = mapped_column(String(32), nullable=False)
    why_now: Mapped[str] = mapped_column(Text, nullable=False)
    buying_signals: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    negative_signals: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    score_breakdown: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    explanations: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    hunter_triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hunter_tasks: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    proceed_to_copilot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class HunterJobRow(BaseModel):
    __tablename__ = "hunter_jobs"
    __table_args__ = (Index("ix_hunter_jobs_status", "status", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    target_account_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("target_accounts.id"))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    tasks: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    completed_tasks: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class TAIImprovementRecommendation(BaseModel):
    __tablename__ = "tai_improvement_recommendations"

    target_account_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("target_accounts.id"))
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    area: Mapped[str] = mapped_column(String(64), nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    expected_impact: Mapped[float] = mapped_column(Float, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="proposed")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
