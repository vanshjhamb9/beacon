"""rev-v1 types — Revenue Ready definition, funnel, QA, gates."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

UNKNOWN = "UNKNOWN"


class RejectionReason(StrEnum):
    NO_WEBSITE = "No website"
    FAKE_COMPANY = "Fake company"
    NO_BUYING_INTENT = "No buying intent"
    NO_SERVICE_MATCH = "No service match"
    NO_BUSINESS_EMAIL = "No business email"
    DUPLICATE = "Duplicate"
    WEAK_EVIDENCE = "Weak evidence"
    UNSUPPORTED_COUNTRY = "Unsupported country"
    NEWS_ARTICLE = "News article"
    PLATFORM_PAGE = "Platform page"
    REPOSITORY_ONLY = "Repository only"
    MARKETPLACE_LISTING = "Marketplace listing"
    CONFIDENCE_TOO_LOW = "Confidence too low"
    IDENTITY_INCOMPLETE = "Identity incomplete"
    NOT_EROWD_ADMITTED = "Not EROWD admitted"
    STALE_SIGNAL = "Stale signal (>48h)"
    DIRECTORY_SOURCE = "Directory source (not a trigger)"
    INSUFFICIENT_WHY_NOW = "Insufficient why-now evidence"
    LEAD_QUALITY_TOO_LOW = "Lead quality below outbound bar"


class ConnectorGrade(StrEnum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    WEAK = "Weak"
    DISABLE_CANDIDATE = "Disable Candidate"


class ManualQaRating(StrEnum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    AVERAGE = "Average"
    WRONG_COMPANY = "Wrong company"
    WRONG_INTENT = "Wrong intent"
    WRONG_SERVICE = "Wrong service"
    WRONG_CONTACT = "Wrong contact"
    DUPLICATE = "Duplicate"
    FAKE = "Fake"


class EvidenceItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str = UNKNOWN
    timestamp: datetime | str | None = None
    url: str = UNKNOWN
    why_qualifies: str = UNKNOWN
    why_now: str = UNKNOWN
    confidence: float = 0.0


class RevenueReadyCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    is_revenue_ready: bool = False
    identity_complete: bool = False
    website_verified: bool = False
    intent_detected: bool = False
    service_match: bool = False
    business_email: bool = False
    decision_maker: bool = False
    evidence_ok: bool = False
    company_name: str = UNKNOWN
    website: str = UNKNOWN
    domain: str = UNKNOWN
    country: str = UNKNOWN
    industry: str = UNKNOWN
    description: str = UNKNOWN
    email: str = UNKNOWN
    decision_maker_name: str = UNKNOWN
    best_service: str = UNKNOWN
    why_now: str = UNKNOWN
    opportunity: str = UNKNOWN
    confidence: float = 0.0
    source: str = UNKNOWN
    rejection_reasons: list[RejectionReason] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    checks: dict[str, Any] = Field(default_factory=dict)


class FunnelStage(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    count: int = 0
    percent: float = 0.0
    top_failure_reasons: list[dict[str, Any]] = Field(default_factory=list)
    avg_processing_ms: float = 0.0
    top_sources: list[dict[str, Any]] = Field(default_factory=list)


class RealityFunnel(BaseModel):
    model_config = ConfigDict(frozen=True)

    stages: list[FunnelStage] = Field(default_factory=list)
    total_signals: int = 0
    revenue_ready: int = 0
    founder_queue: int = 0
    evidence: list[str] = Field(default_factory=list)


class ConnectorScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    connector: str
    signals: int = 0
    companies_admitted: int = 0
    revenue_ready: int = 0
    decision_makers: int = 0
    emails: int = 0
    duplicate_rate: float = 0.0
    manual_qa_score: float = 0.0
    average_quality: float = 0.0
    revenue_ready_pct: float = 0.0
    grade: ConnectorGrade = ConnectorGrade.WEAK
    evidence: list[str] = Field(default_factory=list)


class FounderQueueCardV3(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: str
    company: str = UNKNOWN
    logo_url: str = UNKNOWN
    website: str = UNKNOWN
    industry: str = UNKNOWN
    country: str = UNKNOWN
    why_now: str = UNKNOWN
    opportunity: str = UNKNOWN
    service_match: str = UNKNOWN
    verified_email: str = UNKNOWN
    decision_maker: str = UNKNOWN
    confidence: float = 0.0
    source: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)
    contact_readiness: str = UNKNOWN
    dossier_url: str = UNKNOWN
    revenue_ready: bool = True


class AcceptanceGateResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    revenue_ready_count: int = 0
    verified_emails: int = 0
    named_decision_makers: int = 0
    manual_qa_accuracy: float = 0.0
    duplicate_rate: float = 100.0
    fabricated_contacts: int = 0
    fake_in_founder_queue: int = 0
    production_unlocked: bool = False
    gmail_enabled: bool = False
    whatsapp_enabled: bool = False
    campaigns_enabled: bool = False
    failures: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class DailyRevenueReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    signals_collected: int = 0
    companies_verified: int = 0
    revenue_ready: int = 0
    decision_makers_found: int = 0
    business_emails_found: int = 0
    founder_queue: int = 0
    new_high_intent: int = 0
    connectors_improved: list[str] = Field(default_factory=list)
    connectors_declining: list[str] = Field(default_factory=list)
    top_5_opportunities: list[dict[str, Any]] = Field(default_factory=list)
    biggest_failure: str = UNKNOWN
    recommendation: str = UNKNOWN
    generated_at: datetime | str | None = None
    evidence: list[str] = Field(default_factory=list)


class RevSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: str
    company_name: str = UNKNOWN
    source: str = UNKNOWN
    check: RevenueReadyCheck = Field(default_factory=RevenueReadyCheck)
    rejection_reasons: list[RejectionReason] = Field(default_factory=list)
    processing_ms: float = 0.0
    scoring_version: str = "rev-v1"
    evidence: list[str] = Field(default_factory=list)


class RevRebuildReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_evaluated: int = 0
    revenue_ready: int = 0
    founder_queue: int = 0
    funnel: RealityFunnel = Field(default_factory=RealityFunnel)
    connector_scores: list[ConnectorScore] = Field(default_factory=list)
    rejection_top: list[dict[str, Any]] = Field(default_factory=list)
    acceptance: AcceptanceGateResult = Field(default_factory=AcceptanceGateResult)
    daily: DailyRevenueReport = Field(default_factory=DailyRevenueReport)
    elapsed_ms: float = 0.0
    evidence: list[str] = Field(default_factory=list)
