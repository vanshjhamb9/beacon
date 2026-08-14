from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CompletenessScoresResponse(BaseModel):
    overall_completeness: float
    company_profile_completeness: float
    contact_completeness: float
    leadership_completeness: float
    technology_completeness: float
    revenue_completeness: float
    hiring_completeness: float
    social_profile_completeness: float
    evidence_completeness: float
    timeline_completeness: float


class LeadReadinessChecklistResponse(BaseModel):
    company_profile: bool
    technology: bool
    leadership: bool
    public_business_email: bool
    public_phone: bool
    hiring: bool
    funding: bool
    timeline: bool


class FieldVerificationResponse(BaseModel):
    field_name: str
    value: Any = None
    source: str
    source_url: str | None = None
    connector: str
    verified_at: datetime
    confidence: float
    freshness_score: float
    freshness_status: str
    trust_score: float
    verification_status: str
    confirmed_by: list[str] = Field(default_factory=list)
    conflicting_sources: list[str] = Field(default_factory=list)
    is_canonical: bool = False
    conflict_explanation: str | None = None
    category: str = "general"


class CoverageBreakdownResponse(BaseModel):
    category: str
    present_fields: int
    expected_fields: int
    score: float
    missing_fields: list[str] = Field(default_factory=list)


class ConnectorStatisticResponse(BaseModel):
    connector: str
    success_rate: float
    average_latency_ms: float
    failure_rate: float
    coverage: float
    fields_returned: int
    average_confidence: float
    companies_enriched: int


class VerificationCompanyResponse(BaseModel):
    company_id: UUID
    opportunity_id: UUID
    enrichment_report_id: UUID
    company_name: str
    completeness: CompletenessScoresResponse
    coverage: list[CoverageBreakdownResponse]
    field_verifications: list[FieldVerificationResponse] = Field(default_factory=list)
    freshness_score: float
    freshness_status: str
    trust_score: float
    verification_percent: float
    coverage_percent: float
    overall_data_quality: float
    overall_readiness: float
    readiness_checklist: LeadReadinessChecklistResponse
    decision: str
    automatic_actions: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    connector_statistics: list[ConnectorStatisticResponse] = Field(default_factory=list)
    verification_report_id: UUID | None = None
    created_at: datetime | None = None
    processing_latency_ms: float = 0.0


class VerificationDashboardResponse(BaseModel):
    overall_data_quality: float
    coverage_percent: float
    verification_percent: float
    freshness_percent: float
    average_profile_completeness: float
    connector_leaderboard: list[ConnectorStatisticResponse]
    missing_field_distribution: dict[str, int]
    top_missing_fields: list[str]
    profiles_needing_refresh: int
    flagged_for_review: int
    total_verified_profiles: int


class VerificationConnectorsResponse(BaseModel):
    connectors: list[ConnectorStatisticResponse]


class VerificationRefreshResponse(BaseModel):
    refreshed: bool
    profile: VerificationCompanyResponse
