from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

UNKNOWN = "UNKNOWN"


class AlphaVerdict(StrEnum):
    REJECTED = "REJECTED"
    SALES_READY = "SALES_READY"


class QaRating(StrEnum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    POOR = "Poor"
    FAKE = "Fake"
    DUPLICATE = "Duplicate"
    WRONG_SERVICE = "Wrong Service"
    WRONG_INTENT = "Wrong Intent"


class ServiceBucket(StrEnum):
    AI_AUTOMATION = "AI Automation"
    SAAS_DEVELOPMENT = "SaaS Development"
    CUSTOM_SOFTWARE = "Custom Software"
    MOBILE_APP = "Mobile App"
    ECOMMERCE = "E-commerce"
    ENTERPRISE = "Enterprise"
    UNKNOWN = "UNKNOWN"


class AttributedValue(BaseModel):
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


class AdmissionResult(BaseModel):
    """Rule 1 — would Vansh spend a cold email on this?"""

    admit: bool = False
    reason: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class IdentityGateResult(BaseModel):
    passed: bool = False
    missing: list[str] = Field(default_factory=list)
    fields: dict[str, AttributedValue] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class ContactEnrichmentResult(BaseModel):
    emails: list[AttributedValue] = Field(default_factory=list)
    phones: list[AttributedValue] = Field(default_factory=list)
    linkedin: list[AttributedValue] = Field(default_factory=list)
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    sources_used: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class IntentScores(BaseModel):
    pain_score: float = 0.0
    budget_score: float = 0.0
    urgency: float = 0.0
    technology_gap: float = 0.0
    ai_adoption: float = 0.0
    buying_signal: float = 0.0
    decision_window: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class IntentV2Result(BaseModel):
    primary_bucket: ServiceBucket = ServiceBucket.UNKNOWN
    buckets: dict[str, float] = Field(default_factory=dict)
    best_service: str = UNKNOWN
    scores: IntentScores = Field(default_factory=IntentScores)
    why_now: str = UNKNOWN
    pain: str = UNKNOWN
    estimated_budget: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class CompanyScore(BaseModel):
    total: float = 0.0
    identity: float = 0.0
    website: float = 0.0
    intent: float = 0.0
    service_match: float = 0.0
    contacts: float = 0.0
    evidence_score: float = 0.0
    founder_visible: bool = False
    evidence: list[str] = Field(default_factory=list)


class FounderQueueCard(BaseModel):
    company_id: str
    company: str = UNKNOWN
    why_now: str = UNKNOWN
    pain: str = UNKNOWN
    estimated_budget: str = UNKNOWN
    best_service: str = UNKNOWN
    decision_maker: str = UNKNOWN
    email: str = UNKNOWN
    phone: str = UNKNOWN
    source: str = UNKNOWN
    evidence: str = UNKNOWN
    confidence: float = 0.0
    recommended_first_line: str = UNKNOWN
    meeting_probability: float = 0.0
    score: float = 0.0


class SourceTransparency(BaseModel):
    collected_from: str = UNKNOWN
    collector: str = UNKNOWN
    date: datetime | str | None = None
    original_url: str = UNKNOWN
    original_post_title: str = UNKNOWN
    evidence_snippets: list[str] = Field(default_factory=list)
    verification_history: list[str] = Field(default_factory=list)
    last_crawl: datetime | str | None = None
    complete: bool = False
    evidence: list[str] = Field(default_factory=list)


class DedupeResult(BaseModel):
    is_duplicate: bool = False
    match_keys: list[str] = Field(default_factory=list)
    canonical_company_id: str | None = None
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class ManualQaDecision(BaseModel):
    company_id: str
    rating: QaRating
    notes: str = UNKNOWN
    decided_at: datetime | str | None = None
    reviewer: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class ManualQaCard(BaseModel):
    company_id: str
    website: Any = UNKNOWN
    linkedin: Any = UNKNOWN
    source: Any = UNKNOWN
    evidence_snippets: list[str] = Field(default_factory=list)
    contacts: list[dict[str, Any]] = Field(default_factory=list)
    opportunity: str = UNKNOWN
    industry: Any = UNKNOWN
    confidence: float = 0.0
    ai_reasoning: str = UNKNOWN
    service_match: str = UNKNOWN
    score: float = 0.0


class AlphaAcceptance(BaseModel):
    real_business_percent: float = 0.0
    working_website_percent: float = 0.0
    attributed_email_percent: float = 0.0
    business_phone_percent: float = 0.0
    service_correct_percent: float = 0.0
    duplicate_rate: float = 100.0
    sales_ready_per_day: int = 0
    review_under_15_min: bool = False
    live_outreach_ready: bool = False
    failures: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class AlphaSnapshot(BaseModel):
    company_id: str
    company_name: str = UNKNOWN
    verdict: AlphaVerdict = AlphaVerdict.REJECTED
    admission: AdmissionResult = Field(default_factory=AdmissionResult)
    identity: IdentityGateResult = Field(default_factory=IdentityGateResult)
    contacts: ContactEnrichmentResult = Field(default_factory=ContactEnrichmentResult)
    intent: IntentV2Result = Field(default_factory=IntentV2Result)
    score: CompanyScore = Field(default_factory=CompanyScore)
    transparency: SourceTransparency = Field(default_factory=SourceTransparency)
    founder_card: FounderQueueCard | None = None
    qa_card: ManualQaCard | None = None
    scoring_version: str = "alpha-v1"
    evidence: list[str] = Field(default_factory=list)
