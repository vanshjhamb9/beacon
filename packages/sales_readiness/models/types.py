from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

UNKNOWN = "UNKNOWN"


class WebsiteGrade(StrEnum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    F = "F"


class BuyingIntentLevel(StrEnum):
    VERY_HIGH = "Very High"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class OutreachReadinessStatus(StrEnum):
    NO = "NO"
    NEEDS_MORE_RESEARCH = "Needs More Research"
    EMAIL_READY = "Email Ready"
    PHONE_READY = "Phone Ready"
    LINKEDIN_READY = "LinkedIn Ready"
    MULTI_CHANNEL_READY = "Multi-channel Ready"


class SalesReadinessStatus(StrEnum):
    NOT_READY = "NOT READY"
    RESEARCH_REQUIRED = "RESEARCH REQUIRED"
    CONTACT_READY = "CONTACT READY"
    SALES_READY = "SALES READY"
    ENTERPRISE_READY = "ENTERPRISE READY"


class DealSizeBand(StrEnum):
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"
    ENTERPRISE = "Enterprise"


class AttributedField(BaseModel):
    """Evidence-first field — never fabricate; use UNKNOWN when missing."""

    value: Any = UNKNOWN
    source: str = UNKNOWN
    collected_at: datetime | str | None = None
    confidence: float | None = None
    evidence: list[str] = Field(default_factory=list)

    @classmethod
    def unknown(cls, *, reason: str = "not_observed") -> AttributedField:
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
    ) -> AttributedField:
        if value is None or value == "" or value == UNKNOWN:
            return cls.unknown()
        return cls(
            value=value,
            source=source or UNKNOWN,
            collected_at=collected_at,
            confidence=confidence,
            evidence=list(evidence or []),
        )


class IdentityCompleteness(BaseModel):
    identity_complete: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    fields: dict[str, AttributedField] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class WebsiteIntelligence(BaseModel):
    grade: WebsiteGrade = WebsiteGrade.F
    company_maturity: str = UNKNOWN
    product_maturity: str = UNKNOWN
    trust: str = UNKNOWN
    pricing: str = UNKNOWN
    is_saas: bool | None = None
    is_services: bool | None = None
    enterprise_readiness: str = UNKNOWN
    score: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class TechnologyReadiness(BaseModel):
    categories: dict[str, list[AttributedField]] = Field(default_factory=dict)
    maturity_score: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class BuyingIntent(BaseModel):
    level: BuyingIntentLevel = BuyingIntentLevel.LOW
    score: float = 0.0
    signals: list[AttributedField] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ServiceRecommendation(BaseModel):
    recommended_service: str
    reason: list[str] = Field(default_factory=list)
    estimated_value: str = UNKNOWN
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class RoleContact(BaseModel):
    role: str
    name: str = UNKNOWN
    verified_email: AttributedField = Field(default_factory=AttributedField.unknown)
    verified_phone: AttributedField = Field(default_factory=AttributedField.unknown)
    linkedin: AttributedField = Field(default_factory=AttributedField.unknown)
    public_profile: AttributedField = Field(default_factory=AttributedField.unknown)
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class ContactCompleteness(BaseModel):
    roles: list[RoleContact] = Field(default_factory=list)
    coverage_percent: float = 0.0
    verified_email_count: int = 0
    verified_phone_count: int = 0
    evidence: list[str] = Field(default_factory=list)


class OutreachReadiness(BaseModel):
    status: OutreachReadinessStatus = OutreachReadinessStatus.NO
    can_contact_today: bool = False
    evidence: list[str] = Field(default_factory=list)


class TrustBreakdown(BaseModel):
    identity: float = 0.0
    technology: float = 0.0
    intent: float = 0.0
    contacts: float = 0.0
    website: float = 0.0
    source: float = 0.0
    verification: float = 0.0
    freshness: float = 0.0
    overall: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class RevenuePotential(BaseModel):
    deal_size: DealSizeBand = DealSizeBand.SMALL
    probability: float = 0.0
    sales_cycle: str = UNKNOWN
    recommended_founder_time: str = "Ignore"
    evidence: list[str] = Field(default_factory=list)


class SalesReadinessSnapshot(BaseModel):
    company_id: str
    company_name: str = UNKNOWN
    status: SalesReadinessStatus = SalesReadinessStatus.NOT_READY
    trust_score: float = 0.0
    stars: int = 0
    identity: IdentityCompleteness = Field(default_factory=IdentityCompleteness)
    website: WebsiteIntelligence = Field(default_factory=WebsiteIntelligence)
    technology: TechnologyReadiness = Field(default_factory=TechnologyReadiness)
    intent: BuyingIntent = Field(default_factory=BuyingIntent)
    services: list[ServiceRecommendation] = Field(default_factory=list)
    contacts: ContactCompleteness = Field(default_factory=ContactCompleteness)
    outreach: OutreachReadiness = Field(default_factory=OutreachReadiness)
    trust: TrustBreakdown = Field(default_factory=TrustBreakdown)
    revenue: RevenuePotential = Field(default_factory=RevenuePotential)
    recent_signals: list[AttributedField] = Field(default_factory=list)
    evidence_timeline: list[AttributedField] = Field(default_factory=list)
    suggested_first_message: str = UNKNOWN
    next_action: str = UNKNOWN
    visible_in_founder_queue: bool = False
    eligible_for_revenue_hunter: bool = False
    scoring_version: str = "sre-v1"
    evidence: list[str] = Field(default_factory=list)
