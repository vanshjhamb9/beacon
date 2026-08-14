from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EnrichmentScoresResponse(BaseModel):
    profile_completeness: float
    contact_availability: float
    technology_confidence: float
    decision_maker_confidence: float
    overall_enrichment_confidence: float


class EnrichedCompanyProfileResponse(BaseModel):
    company_name: str
    website: str | None = None
    domain: str | None = None
    industry: str | None = None
    sub_industry: str | None = None
    description: str | None = None
    location: str | None = None
    country: str | None = None
    founded_year: int | None = None
    employee_count_estimate: int | None = None
    company_size_range: str | None = None
    revenue_estimate: str | None = None
    attributions: list[dict[str, Any]] = Field(default_factory=list)


class TechnologyEntryResponse(BaseModel):
    name: str
    category: str
    confidence: float
    source: str
    source_url: str | None = None
    signal: str | None = None


class PersonEntryResponse(BaseModel):
    name: str
    role: str
    department: str | None = None
    linkedin_url: str | None = None
    work_email: str | None = None
    business_phone: str | None = None
    confidence: float
    source: str
    source_url: str | None = None


class ContactEntryResponse(BaseModel):
    kind: str
    value: str
    label: str | None = None
    confidence: float
    source: str
    source_url: str | None = None
    is_public: bool = True


class SocialProfileResponse(BaseModel):
    platform: str
    url: str
    handle: str | None = None
    confidence: float
    source: str


class TeamInsightsResponse(BaseModel):
    leadership_team_size: int | None = None
    engineering_team_estimate: int | None = None
    support_team_estimate: int | None = None
    operations_team_estimate: int | None = None
    recent_hires: list[str] = Field(default_factory=list)
    open_positions: list[str] = Field(default_factory=list)
    hiring_trends: str | None = None


class JobEntryResponse(BaseModel):
    title: str
    department: str | None = None
    location: str | None = None
    url: str | None = None
    confidence: float
    source: str
    source_url: str | None = None


class EvidenceChainItemResponse(BaseModel):
    category: str
    summary: str
    source: str
    source_url: str | None = None
    confidence: float
    reference_id: str | None = None


class SourceAttributionResponse(BaseModel):
    source: str
    source_url: str | None = None
    fields: list[str] = Field(default_factory=list)
    confidence: float
    licensed: bool = False
    notes: str = ""


class SalesReadyLeadProfileResponse(BaseModel):
    company_id: UUID
    opportunity_id: UUID
    company_name: str
    opportunity_score: float
    business_pain: str
    recommended_service: str
    buyer_persona: str
    company_profile: EnrichedCompanyProfileResponse
    technology_stack: list[TechnologyEntryResponse]
    decision_makers: list[PersonEntryResponse]
    public_contact_information: list[ContactEntryResponse]
    team_insights: TeamInsightsResponse
    social_profiles: list[SocialProfileResponse]
    open_jobs: list[JobEntryResponse] = Field(default_factory=list)
    estimated_budget: str | None = None
    priority: str | None = None
    why_now: str
    best_outreach_angle: str
    evidence_chain: list[EvidenceChainItemResponse]
    source_attribution: list[SourceAttributionResponse]
    enrichment_confidence: EnrichmentScoresResponse
    enrichment_report_id: UUID | None = None
    created_at: datetime | None = None
    processing_latency_ms: float = 0.0


class EnrichmentRefreshResponse(BaseModel):
    refreshed: bool
    profile: SalesReadyLeadProfileResponse
