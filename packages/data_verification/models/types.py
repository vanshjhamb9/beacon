from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FreshnessStatus(StrEnum):
    FRESH = "fresh"
    AGEING = "ageing"
    STALE = "stale"
    EXPIRED = "expired"


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    UNVERIFIED = "unverified"
    CONFLICTING = "conflicting"
    MISSING = "missing"
    FLAGGED = "flagged"


class AutomaticAction(StrEnum):
    NONE = "none"
    SCHEDULE_ENRICHMENT_REFRESH = "schedule_enrichment_refresh"
    QUEUE_REENRICHMENT = "queue_reenrichment"
    FLAG_FOR_REVIEW = "flag_for_review"


class ReadinessDecision(StrEnum):
    READY = "ready"
    NEEDS_REFRESH = "needs_refresh"
    NEEDS_REVIEW = "needs_review"
    INCOMPLETE = "incomplete"


class FieldObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    field_name: str
    value: Any
    source: str
    source_url: str | None = None
    confidence: float = Field(ge=0.0, le=100.0)
    collected_at: datetime | None = None
    connector: str | None = None


class FieldVerificationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    field_name: str
    value: Any
    source: str
    source_url: str | None = None
    connector: str
    verified_at: datetime
    confidence: float = Field(ge=0.0, le=100.0)
    freshness_score: float = Field(ge=0.0, le=100.0)
    freshness_status: FreshnessStatus
    trust_score: float = Field(ge=0.0, le=100.0)
    verification_status: VerificationStatus
    confirmed_by: list[str] = Field(default_factory=list)
    conflicting_sources: list[str] = Field(default_factory=list)
    is_canonical: bool = False
    conflict_explanation: str | None = None
    category: str = "general"


class CompletenessScores(BaseModel):
    model_config = ConfigDict(frozen=True)

    overall_completeness: float = Field(ge=0.0, le=100.0)
    company_profile_completeness: float = Field(ge=0.0, le=100.0)
    contact_completeness: float = Field(ge=0.0, le=100.0)
    leadership_completeness: float = Field(ge=0.0, le=100.0)
    technology_completeness: float = Field(ge=0.0, le=100.0)
    revenue_completeness: float = Field(ge=0.0, le=100.0)
    hiring_completeness: float = Field(ge=0.0, le=100.0)
    social_profile_completeness: float = Field(ge=0.0, le=100.0)
    evidence_completeness: float = Field(ge=0.0, le=100.0)
    timeline_completeness: float = Field(ge=0.0, le=100.0)


class CoverageBreakdown(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: str
    present_fields: int
    expected_fields: int
    score: float = Field(ge=0.0, le=100.0)
    missing_fields: list[str] = Field(default_factory=list)


class ConnectorStatistic(BaseModel):
    model_config = ConfigDict(frozen=True)

    connector: str
    success_rate: float = Field(ge=0.0, le=100.0)
    average_latency_ms: float = 0.0
    failure_rate: float = Field(ge=0.0, le=100.0)
    coverage: float = Field(ge=0.0, le=100.0)
    fields_returned: int = 0
    average_confidence: float = Field(ge=0.0, le=100.0)
    companies_enriched: int = 0


class LeadReadinessChecklist(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_profile: bool
    technology: bool
    leadership: bool
    public_business_email: bool
    public_phone: bool
    hiring: bool
    funding: bool
    timeline: bool


class VerificationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    opportunity_id: UUID
    enrichment_report_id: UUID
    company_name: str
    completeness: CompletenessScores
    coverage: list[CoverageBreakdown]
    field_verifications: list[FieldVerificationResult]
    freshness_score: float = Field(ge=0.0, le=100.0)
    freshness_status: FreshnessStatus
    trust_score: float = Field(ge=0.0, le=100.0)
    verification_percent: float = Field(ge=0.0, le=100.0)
    coverage_percent: float = Field(ge=0.0, le=100.0)
    overall_data_quality: float = Field(ge=0.0, le=100.0)
    overall_readiness: float = Field(ge=0.0, le=100.0)
    readiness_checklist: LeadReadinessChecklist
    decision: ReadinessDecision
    automatic_actions: list[AutomaticAction]
    reason_codes: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    connector_statistics: list[ConnectorStatistic] = Field(default_factory=list)
    explanation: dict[str, Any] = Field(default_factory=dict)
    processing_latency_ms: float = 0.0


class VerificationInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    opportunity_id: UUID
    enrichment_report_id: UUID
    company_name: str
    enriched_at: datetime
    lead_profile: dict[str, Any]
    source_rows: list[dict[str, Any]] = Field(default_factory=list)
    timeline_event_count: int = 0
    enrichment_latency_ms: float = 0.0
    force_refresh: bool = False


class DashboardMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    overall_data_quality: float
    coverage_percent: float
    verification_percent: float
    freshness_percent: float
    average_profile_completeness: float
    connector_leaderboard: list[ConnectorStatistic]
    missing_field_distribution: dict[str, int]
    top_missing_fields: list[str]
    profiles_needing_refresh: int
    flagged_for_review: int
    total_verified_profiles: int
