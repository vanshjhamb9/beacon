"""Core DQE schemas, enums, and domain models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ImmutableModel(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)


class QualityDecision(StrEnum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    HOLD = "HOLD"


class QualityGate(StrEnum):
    FRESHNESS = "FRESHNESS"
    BUYING_SIGNAL = "BUYING_SIGNAL"
    WEBSITE_QUALITY = "WEBSITE_QUALITY"
    COMPANY_VALIDATION = "COMPANY_VALIDATION"
    SOURCE_TRUST = "SOURCE_TRUST"
    DUPLICATE_CHECK = "DUPLICATE_CHECK"
    COMPETITOR_CHECK = "COMPETITOR_CHECK"
    ACTIVITY_CHECK = "ACTIVITY_CHECK"
    INDUSTRY_RULES = "INDUSTRY_RULES"
    REGION_RULES = "REGION_RULES"
    AI_COMPANY_FILTER = "AI_COMPANY_FILTER"
    ICP_FILTER = "ICP_FILTER"


class SignalType(StrEnum):
    HIRING = "HIRING"
    FUNDING = "FUNDING"
    PRODUCT_LAUNCH = "PRODUCT_LAUNCH"
    TECHNOLOGY_ADOPTION = "TECHNOLOGY_ADOPTION"
    PARTNERSHIP = "PARTNERSHIP"
    EXPANSION = "EXPANSION"
    CONFERENCE = "CONFERENCE"
    AWARD = "AWARD"
    PRESS_RELEASE = "PRESS_RELEASE"
    GOVERNMENT_TENDER = "GOVERNMENT_TENDER"
    EXECUTIVE_HIRING = "EXECUTIVE_HIRING"
    OFFICE_EXPANSION = "OFFICE_EXPANSION"
    ACQUISITION = "ACQUISITION"
    INFRASTRUCTURE_UPGRADE = "INFRASTRUCTURE_UPGRADE"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"
    API_RELEASE = "API_RELEASE"
    MARKETPLACE_EXPANSION = "MARKETPLACE_EXPANSION"
    COMPLIANCE = "COMPLIANCE"


class RejectionReason(StrEnum):
    STALE_SIGNAL = "STALE_SIGNAL"
    NO_BUYING_SIGNAL = "NO_BUYING_SIGNAL"
    PARKED_DOMAIN = "PARKED_DOMAIN"
    COMING_SOON = "COMING_SOON"
    NOT_FOUND_404 = "NOT_FOUND_404"
    MAINTENANCE = "MAINTENANCE"
    SPAM_WEBSITE = "SPAM_WEBSITE"
    NO_HTTPS = "NO_HTTPS"
    LOW_CONTENT = "LOW_CONTENT"
    DOMAIN_FOR_SALE = "DOMAIN_FOR_SALE"
    INACTIVE_WEBSITE = "INACTIVE_WEBSITE"
    DUPLICATE_DOMAIN = "DUPLICATE_DOMAIN"
    DUPLICATE_COMPANY = "DUPLICATE_COMPANY"
    DUPLICATE_OPPORTUNITY = "DUPLICATE_OPPORTUNITY"
    DUPLICATE_EVIDENCE = "DUPLICATE_EVIDENCE"
    DUPLICATE_SIGNAL = "DUPLICATE_SIGNAL"
    COMPETITOR = "COMPETITOR"
    EXISTING_CLIENT = "EXISTING_CLIENT"
    DEMO_COMPANY = "DEMO_COMPANY"
    AI_COMPANY = "AI_COMPANY"
    UNSUPPORTED_REGION = "UNSUPPORTED_REGION"
    OUTSIDE_ICP = "OUTSIDE_ICP"
    LOW_SOURCE_TRUST = "LOW_SOURCE_TRUST"
    NO_RECENT_ACTIVITY = "NO_RECENT_ACTIVITY"
    EXPIRED_OPPORTUNITY = "EXPIRED_OPPORTUNITY"
    UNKNOWN = "UNKNOWN"


class OpportunityExpiry(ImmutableModel):
    signal_type: SignalType
    max_age_days: int


DEFAULT_EXPIRY: list[OpportunityExpiry] = [
    OpportunityExpiry(signal_type=SignalType.HIRING, max_age_days=30),
    OpportunityExpiry(signal_type=SignalType.FUNDING, max_age_days=90),
    OpportunityExpiry(signal_type=SignalType.PRODUCT_LAUNCH, max_age_days=30),
    OpportunityExpiry(signal_type=SignalType.TECHNOLOGY_ADOPTION, max_age_days=60),
    OpportunityExpiry(signal_type=SignalType.PARTNERSHIP, max_age_days=45),
    OpportunityExpiry(signal_type=SignalType.EXPANSION, max_age_days=90),
    OpportunityExpiry(signal_type=SignalType.CONFERENCE, max_age_days=15),
    OpportunityExpiry(signal_type=SignalType.AWARD, max_age_days=30),
    OpportunityExpiry(signal_type=SignalType.PRESS_RELEASE, max_age_days=30),
    OpportunityExpiry(signal_type=SignalType.GOVERNMENT_TENDER, max_age_days=9999),
    OpportunityExpiry(signal_type=SignalType.EXECUTIVE_HIRING, max_age_days=30),
    OpportunityExpiry(signal_type=SignalType.OFFICE_EXPANSION, max_age_days=45),
    OpportunityExpiry(signal_type=SignalType.ACQUISITION, max_age_days=60),
    OpportunityExpiry(signal_type=SignalType.INFRASTRUCTURE_UPGRADE, max_age_days=60),
    OpportunityExpiry(signal_type=SignalType.SECURITY_INCIDENT, max_age_days=30),
    OpportunityExpiry(signal_type=SignalType.API_RELEASE, max_age_days=30),
    OpportunityExpiry(signal_type=SignalType.MARKETPLACE_EXPANSION, max_age_days=45),
    OpportunityExpiry(signal_type=SignalType.COMPLIANCE, max_age_days=60),
]


class FreshnessLimit(ImmutableModel):
    signal_type: str
    max_age_days: int


DEFAULT_FRESHNESS_LIMITS: list[FreshnessLimit] = [
    FreshnessLimit(signal_type="HIRING", max_age_days=30),
    FreshnessLimit(signal_type="FUNDING", max_age_days=90),
    FreshnessLimit(signal_type="PRODUCT_LAUNCH", max_age_days=30),
    FreshnessLimit(signal_type="TECHNOLOGY_ADOPTION", max_age_days=60),
    FreshnessLimit(signal_type="PARTNERSHIP", max_age_days=45),
    FreshnessLimit(signal_type="EXPANSION", max_age_days=90),
    FreshnessLimit(signal_type="CONFERENCE", max_age_days=15),
    FreshnessLimit(signal_type="AWARD", max_age_days=30),
    FreshnessLimit(signal_type="PRESS_RELEASE", max_age_days=30),
    FreshnessLimit(signal_type="GOVERNMENT_TENDER", max_age_days=9999),
]


DEFAULT_SOURCE_TRUST: dict[str, float] = {
    "linkedin": 98.0,
    "company_website": 97.0,
    "crunchbase": 95.0,
    "government": 95.0,
    "sec_edgar": 95.0,
    "github": 88.0,
    "twitter": 82.0,
    "product_hunt": 80.0,
    "rss": 71.0,
    "unknown_blog": 42.0,
}

DEFAULT_MIN_SOURCE_TRUST: float = 60.0


DEFAULT_SUPPORTED_REGIONS: list[str] = [
    "US",
    "CA",
    "UK",
    "GB",
    "EU",
    "DE",
    "FR",
    "NL",
    "SE",
    "NO",
    "DK",
    "FI",
    "IE",
    "ES",
    "IT",
    "AU",
    "AE",
    "SA",
    "IN",
    "SG",
]


DEFAULT_AI_KEYWORDS: list[str] = [
    "ai model",
    "llm",
    "ai startup",
    "open source ai",
    "ai developer tools",
    "ai infrastructure",
    "llm sdk",
    "model hosting",
    "prompt engineering",
    "inference platform",
    "ai framework",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural network",
    "generative ai",
    "foundation model",
    "language model",
    "transformer model",
    "ai chip",
    "gpu cloud",
    "ai as a service",
    "mlops",
    "aiops",
    "nlp platform",
    "computer vision platform",
]


class QualityEvent(ImmutableModel):
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID
    company_name: str
    signal_type: str
    source: str
    decision: QualityDecision
    gates_passed: list[str] = Field(default_factory=list)
    gates_failed: list[str] = Field(default_factory=list)
    rejection_reasons: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class QualitySnapshot(ImmutableModel):
    id: UUID = Field(default_factory=uuid4)
    signals_collected: int = 0
    signals_accepted: int = 0
    signals_rejected: int = 0
    acceptance_rate: float = 0.0
    freshness_failures: int = 0
    duplicate_failures: int = 0
    competitor_failures: int = 0
    website_failures: int = 0
    buying_signal_failures: int = 0
    ai_company_failures: int = 0
    icp_failures: int = 0
    region_failures: int = 0
    source_trust_failures: int = 0
    activity_failures: int = 0
    expired_opportunities: int = 0
    connector_quality: dict[str, float] = Field(default_factory=dict)
    top_rejection_reasons: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
