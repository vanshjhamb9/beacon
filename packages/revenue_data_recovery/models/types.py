from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

UNKNOWN = "UNKNOWN"


class RecoveryStage(StrEnum):
    NEW = "NEW"
    IDENTITY_RECOVERY = "IDENTITY_RECOVERY"
    WEBSITE_RECOVERY = "WEBSITE_RECOVERY"
    CONTACT_RECOVERY = "CONTACT_RECOVERY"
    INTENT_ANALYSIS = "INTENT_ANALYSIS"
    SERVICE_MATCH = "SERVICE_MATCH"
    TRUST = "TRUST"
    SALES_READY = "SALES_READY"
    REVENUE_HUNTER = "REVENUE_HUNTER"
    REJECTED = "REJECTED"


class SalesReadyStatus(StrEnum):
    NOT_READY = "NOT_READY"
    PARTIAL = "PARTIAL"
    SALES_READY = "SALES_READY"


class AttributedValue(BaseModel):
    """Evidence-first field — never fabricate."""

    value: Any = UNKNOWN
    source: str = UNKNOWN
    collected_at: datetime | str | None = None
    confidence: float | None = None
    evidence: list[str] = Field(default_factory=list)

    @classmethod
    def unknown(cls, *, reason: str = "not_observed") -> AttributedValue:
        return cls(value=UNKNOWN, source=UNKNOWN, confidence=None, evidence=[reason])

    @classmethod
    def of(
        cls,
        value: Any,
        *,
        source: str,
        collected_at: datetime | str | None = None,
        confidence: float | None = None,
        evidence: list[str] | None = None,
    ) -> AttributedValue:
        if value is None or value == "" or value == UNKNOWN:
            return cls.unknown()
        return cls(
            value=value,
            source=source or UNKNOWN,
            collected_at=collected_at,
            confidence=confidence,
            evidence=list(evidence or []),
        )


class IdentityRecoveryResult(BaseModel):
    legal_name: AttributedValue = Field(default_factory=AttributedValue.unknown)
    website: AttributedValue = Field(default_factory=AttributedValue.unknown)
    domain: AttributedValue = Field(default_factory=AttributedValue.unknown)
    country: AttributedValue = Field(default_factory=AttributedValue.unknown)
    industry: AttributedValue = Field(default_factory=AttributedValue.unknown)
    business_category: AttributedValue = Field(default_factory=AttributedValue.unknown)
    description: AttributedValue = Field(default_factory=AttributedValue.unknown)
    linkedin_company_url: AttributedValue = Field(default_factory=AttributedValue.unknown)
    employee_estimate: AttributedValue = Field(default_factory=AttributedValue.unknown)
    identity_complete: bool = False
    confidence: float = 0.0
    missing_fields: list[str] = Field(default_factory=list)
    sources_tried: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class WebsiteRecoveryResult(BaseModel):
    verified_website: AttributedValue = Field(default_factory=AttributedValue.unknown)
    canonical_domain: AttributedValue = Field(default_factory=AttributedValue.unknown)
    website_verified: bool = False
    rejected_reason: str | None = None
    confidence: float = 0.0
    candidates_tried: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class FakeEliminationResult(BaseModel):
    is_fake: bool = False
    is_business: bool = False
    reasons: list[str] = Field(default_factory=list)
    entity_type: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class RecoveredContact(BaseModel):
    name: str = UNKNOWN
    role: str = UNKNOWN
    email: AttributedValue = Field(default_factory=AttributedValue.unknown)
    phone: AttributedValue = Field(default_factory=AttributedValue.unknown)
    linkedin: AttributedValue = Field(default_factory=AttributedValue.unknown)
    public_profile: AttributedValue = Field(default_factory=AttributedValue.unknown)
    source: str = UNKNOWN
    confidence: float = 0.0
    last_verified: datetime | str | None = None
    evidence: list[str] = Field(default_factory=list)


class ContactRecoveryResult(BaseModel):
    contacts: list[RecoveredContact] = Field(default_factory=list)
    coverage_percent: float = 0.0
    verified_email_count: int = 0
    verified_phone_count: int = 0
    verified_decision_maker_count: int = 0
    evidence: list[str] = Field(default_factory=list)


class OpportunityValidationResult(BaseModel):
    accepted: bool = False
    why_collected: str = UNKNOWN
    buying_signal: AttributedValue = Field(default_factory=AttributedValue.unknown)
    technology_signal: AttributedValue = Field(default_factory=AttributedValue.unknown)
    business_signal: AttributedValue = Field(default_factory=AttributedValue.unknown)
    hiring_signal: AttributedValue = Field(default_factory=AttributedValue.unknown)
    funding_signal: AttributedValue = Field(default_factory=AttributedValue.unknown)
    growth_signal: AttributedValue = Field(default_factory=AttributedValue.unknown)
    pain_point: AttributedValue = Field(default_factory=AttributedValue.unknown)
    recommended_service: AttributedValue = Field(default_factory=AttributedValue.unknown)
    estimated_project_value: AttributedValue = Field(default_factory=AttributedValue.unknown)
    confidence: float = 0.0
    rejection_reasons: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class IntentScore(BaseModel):
    signal: str
    weight: float
    matched: bool = False
    evidence: list[str] = Field(default_factory=list)


class IntentIntelligenceResult(BaseModel):
    score: float = 0.0
    level: str = "Low"
    signals: list[IntentScore] = Field(default_factory=list)
    matched_count: int = 0
    evidence: list[str] = Field(default_factory=list)


class ServiceRecommendation(BaseModel):
    recommended_service: str
    reason: list[str] = Field(default_factory=list)
    estimated_value: str = UNKNOWN
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class RevenueRecommendationResult(BaseModel):
    recommendations: list[ServiceRecommendation] = Field(default_factory=list)
    primary_service: str = UNKNOWN
    primary_estimate: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class QualityGateResult(BaseModel):
    passed: bool = False
    identity_complete: bool = False
    website_verified: bool = False
    business_verified: bool = False
    intent_above_threshold: bool = False
    trust_above_threshold: bool = False
    contact_path_ok: bool = False
    contact_paths: list[str] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class RecoveryQueueItem(BaseModel):
    company_id: str
    company_name: str = UNKNOWN
    stage: RecoveryStage = RecoveryStage.NEW
    priority: float = 0.0
    progress_percent: float = 0.0
    next_action: str = UNKNOWN
    blocked_reasons: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class RevenueDossier(BaseModel):
    company_id: str
    company_name: str = UNKNOWN
    stars: int = 0
    status: SalesReadyStatus = SalesReadyStatus.NOT_READY
    identity: IdentityRecoveryResult = Field(default_factory=IdentityRecoveryResult)
    industry: Any = UNKNOWN
    country: Any = UNKNOWN
    website: Any = UNKNOWN
    employees: Any = UNKNOWN
    technology: list[str] = Field(default_factory=list)
    intent: IntentIntelligenceResult = Field(default_factory=IntentIntelligenceResult)
    decision_makers: list[RecoveredContact] = Field(default_factory=list)
    verified_contacts: list[RecoveredContact] = Field(default_factory=list)
    buying_signals: list[str] = Field(default_factory=list)
    recommended_services: list[ServiceRecommendation] = Field(default_factory=list)
    estimated_deal: str = UNKNOWN
    evidence_timeline: list[AttributedValue] = Field(default_factory=list)
    trust_score: float = 0.0
    next_action: str = UNKNOWN
    recovery_stage: RecoveryStage = RecoveryStage.NEW
    eligible_for_revenue_hunter: bool = False
    visible_in_founder_queue: bool = False
    quality_gate: QualityGateResult = Field(default_factory=QualityGateResult)
    scoring_version: str = "rdi-v1"
    evidence: list[str] = Field(default_factory=list)


class RecoveryMetrics(BaseModel):
    companies: int = 0
    identity_complete: int = 0
    identity_percent: float = 0.0
    website_verified: int = 0
    website_percent: float = 0.0
    intent_above_threshold: int = 0
    intent_percent: float = 0.0
    contacts_with_path: int = 0
    contacts_percent: float = 0.0
    sales_ready: int = 0
    sales_ready_percent: float = 0.0
    recovery_percent: float = 0.0
    recovery_failures: int = 0
    unknown_fields: int = 0
    fake_companies: int = 0
    duplicate_percent: float = 0.0
    recovery_time_ms: float = 0.0
    recovery_success: int = 0
    founder_queue: int = 0
    scoring_version: str = "rdi-v1"


class DailyRecoveryReport(BaseModel):
    processed: int = 0
    recovered: int = 0
    failed: int = 0
    fake_eliminated: int = 0
    sales_ready: int = 0
    stages: dict[str, int] = Field(default_factory=dict)
    duration_ms: float = 0.0
    scoring_version: str = "rdi-v1"


class RdiSnapshot(BaseModel):
    company_id: str
    company_name: str = UNKNOWN
    identity: IdentityRecoveryResult = Field(default_factory=IdentityRecoveryResult)
    website: WebsiteRecoveryResult = Field(default_factory=WebsiteRecoveryResult)
    fake: FakeEliminationResult = Field(default_factory=FakeEliminationResult)
    contacts: ContactRecoveryResult = Field(default_factory=ContactRecoveryResult)
    opportunity: OpportunityValidationResult = Field(default_factory=OpportunityValidationResult)
    intent: IntentIntelligenceResult = Field(default_factory=IntentIntelligenceResult)
    recommendations: RevenueRecommendationResult = Field(default_factory=RevenueRecommendationResult)
    quality_gate: QualityGateResult = Field(default_factory=QualityGateResult)
    queue_item: RecoveryQueueItem | None = None
    dossier: RevenueDossier | None = None
    trust_score: float = 0.0
    recovery_stage: RecoveryStage = RecoveryStage.NEW
    status: SalesReadyStatus = SalesReadyStatus.NOT_READY
    eligible_for_revenue_hunter: bool = False
    visible_in_founder_queue: bool = False
    scoring_version: str = "rdi-v1"
    evidence: list[str] = Field(default_factory=list)
