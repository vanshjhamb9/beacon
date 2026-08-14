from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RevenueHunterDossierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    opportunity_id: UUID | None = None
    company_name: str
    industry: str | None = None
    country: str | None = None
    company_size_band: str | None = None
    funding_stage: str | None = None
    revenue_band: str | None = None
    filter_passed: bool
    filter_match: dict[str, Any] = Field(default_factory=dict)
    recommended_service: str
    service_confidence: float
    service_matches: list[Any] = Field(default_factory=list)
    pain_points: list[Any] = Field(default_factory=list)
    website_intelligence: dict[str, Any] = Field(default_factory=dict)
    why_now: dict[str, Any] = Field(default_factory=dict)
    dossier: dict[str, Any] = Field(default_factory=dict)
    priority_grade: str
    revenue_score: float
    expected_budget: str
    expected_timeline: str
    probability: float
    proceed_to_campaign: bool
    work_queue_eligible: bool
    score_breakdown: list[Any] = Field(default_factory=list)
    evidence_chain: list[Any] = Field(default_factory=list)
    explanations: dict[str, Any] = Field(default_factory=dict)
    scoring_version: str
    created_at: datetime | None = None


class RevenueHunterDossierListResponse(BaseModel):
    dossiers: list[RevenueHunterDossierResponse]
    total: int


class WorkQueueItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dossier_id: UUID | None = None
    company_id: UUID
    company_name: str
    priority_grade: str
    recommended_service: str
    why_today: str
    expected_budget: str
    probability: float
    primary_contact: dict[str, Any] = Field(default_factory=dict)
    status: str
    allowed_actions: list[Any] = Field(default_factory=list)
    rank: int
    action_log: list[Any] = Field(default_factory=list)
    acted_at: datetime | None = None
    created_at: datetime | None = None


class WorkQueueListResponse(BaseModel):
    items: list[WorkQueueItemResponse]
    total: int


class WorkQueueActionBody(BaseModel):
    action: str
    actor: str = "founder"


class FounderDashboardResponse(BaseModel):
    todays_targets: list[dict[str, Any]] = Field(default_factory=list)
    top_25_companies: list[dict[str, Any]] = Field(default_factory=list)
    expected_revenue: float = 0.0
    expected_pipeline: float = 0.0
    meetings_today: int = 0
    campaign_queue: int = 0
    reply_queue: int = 0
    follow_ups: int = 0
    hot_opportunities: int = 0
    generated_at: datetime | None = None


class FilterTaxonomyResponse(BaseModel):
    countries: list[str]
    company_sizes: list[str]
    industries: list[str]
    funding_stages: list[str]
    revenue_bands: list[str]
    services: list[str]
