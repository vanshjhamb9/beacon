from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


SCORING_VERSION = "tai-v1"


class AccountTier(StrEnum):
    TOP = "top"
    MID = "mid"
    LOW = "low"
    EXCLUDED = "excluded"


class BudgetBand(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class HunterStatus(StrEnum):
    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScoreComponent(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    value: float = Field(ge=0.0, le=100.0)
    weight: float = Field(ge=0.0, le=1.0)
    explanation: str
    evidence: list[str] = Field(default_factory=list)


class ICPProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    name: str
    service_match: str
    priority: int = 100
    company_size_min: int | None = None
    company_size_max: int | None = None
    industries: list[str] = Field(default_factory=list)
    revenue_bands: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    employee_count_min: int | None = None
    employee_count_max: int | None = None
    funding_stages: list[str] = Field(default_factory=list)
    hiring_signals: list[str] = Field(default_factory=list)
    technology_stack: list[str] = Field(default_factory=list)
    business_models: list[str] = Field(default_factory=list)
    growth_signals: list[str] = Field(default_factory=list)
    decision_makers: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    buying_signals: list[str] = Field(default_factory=list)
    negative_signals: list[str] = Field(default_factory=list)
    # Lead Engine / Apollo-style COMPANY filters
    headquarters_cities: list[str] = Field(default_factory=list)
    specialties: list[str] = Field(default_factory=list)
    company_types: list[str] = Field(default_factory=list)  # d2c_brand | agency_partner | saas_product
    year_founded_min: int | None = None
    year_founded_max: int | None = None
    linkedin_url_required: bool = False
    company_name_contains: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    lists: list[str] = Field(default_factory=list)  # saved ICP preset labels
    metadata: dict[str, Any] = Field(default_factory=dict)


class TargetAccountInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    opportunity_id: UUID | None = None
    industry: str | None = None
    country: str | None = None
    domain: str | None = None
    website: str | None = None
    employee_count: int | None = None
    revenue_band: str | None = None
    funding_stage: str | None = None
    funding_amount: float | None = None
    funding_days_ago: int | None = None
    technologies: list[str] = Field(default_factory=list)
    hiring_roles: list[str] = Field(default_factory=list)
    hiring_count: int = 0
    pains: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    business_model: str | None = None
    growth_signals: list[str] = Field(default_factory=list)
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    contacts: list[dict[str, Any]] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)
    vendors: list[str] = Field(default_factory=list)
    opportunity_score: float = 0.0
    verification_score: float = 0.0
    enrichment: dict[str, Any] = Field(default_factory=dict)
    website_metrics: dict[str, Any] = Field(default_factory=dict)
    reviews: list[str] = Field(default_factory=list)
    social_profiles: list[str] = Field(default_factory=list)
    news: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    customers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EngineScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: float = Field(ge=0.0, le=100.0)
    band: str | None = None
    explanation: str
    evidence: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class TargetAccountDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    opportunity_id: UUID | None = None
    matched_icp_key: str | None = None
    matched_icp_name: str | None = None
    service_match: str | None = None
    fit: EngineScore
    intent: EngineScore
    budget: EngineScore
    urgency: EngineScore
    accessibility: EngineScore
    competition: EngineScore
    revenue_opportunity_score: float
    tier: AccountTier
    why_now: str
    buying_signals: list[str] = Field(default_factory=list)
    negative_signals: list[str] = Field(default_factory=list)
    score_breakdown: list[ScoreComponent] = Field(default_factory=list)
    hunter_triggered: bool = False
    hunter_tasks: list[str] = Field(default_factory=list)
    proceed_to_copilot: bool = False
    scoring_version: str = SCORING_VERSION
    explanations: dict[str, str] = Field(default_factory=dict)
    evidence_chain: list[str] = Field(default_factory=list)
    improvement_recommendations: list[str] = Field(default_factory=list)


class HunterJob(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    target_account_id: UUID | None = None
    status: HunterStatus = HunterStatus.QUEUED
    tasks: list[str] = Field(default_factory=list)
    completed_tasks: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] = Field(default_factory=dict)


class ImprovementRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    area: str
    recommendation: str
    reason: str
    expected_impact: float
    requires_approval: bool = True
