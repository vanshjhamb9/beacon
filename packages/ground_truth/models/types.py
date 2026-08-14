from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

UNKNOWN = "UNKNOWN"


class GtVerdict(StrEnum):
    REJECTED = "REJECTED"
    SALES_READY = "SALES_READY"
    ENTERPRISE_READY = "ENTERPRISE_READY"


class RejectionReason(StrEnum):
    NO_WEBSITE = "No Website"
    NO_CONTACT = "No Contact"
    MARKETPLACE_LISTING = "Marketplace Listing"
    GITHUB_REPOSITORY = "GitHub Repository"
    DUPLICATE = "Duplicate"
    NO_BUSINESS = "No Business"
    LOW_INTENT = "Low Intent"
    NO_EVIDENCE = "No Evidence"
    UNKNOWN_IDENTITY = "Unknown Identity"
    UNKNOWN_WHY_NEED_US = "Unknown Why Need Us"
    UNKNOWN_SOURCE = "Unknown Source"
    UNKNOWN_DECISION_MAKER = "Unknown Decision Maker"
    UNKNOWN_WHY_NOW = "Unknown Why Now"
    FAKE = "Fake"
    LOW_TRUST = "Low Trust"
    LOW_READINESS = "Low Readiness"


class AttributedField(BaseModel):
    """Evidence-first field (Rule 4)."""

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


class TruthQuestions(BaseModel):
    who_are_they: AttributedField = Field(default_factory=AttributedField.unknown)
    what_do_they_do: AttributedField = Field(default_factory=AttributedField.unknown)
    why_need_us: AttributedField = Field(default_factory=AttributedField.unknown)
    where_found: AttributedField = Field(default_factory=AttributedField.unknown)
    can_contact: AttributedField = Field(default_factory=AttributedField.unknown)
    who_decides: AttributedField = Field(default_factory=AttributedField.unknown)
    why_now: AttributedField = Field(default_factory=AttributedField.unknown)
    all_answered: bool = False
    missing: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class CompanyTruthProfile(BaseModel):
    """Rule 2 — ONE company truth profile."""

    company_id: str
    company_name: str = UNKNOWN
    website: AttributedField = Field(default_factory=AttributedField.unknown)
    description: AttributedField = Field(default_factory=AttributedField.unknown)
    country: AttributedField = Field(default_factory=AttributedField.unknown)
    employees: AttributedField = Field(default_factory=AttributedField.unknown)
    industry: AttributedField = Field(default_factory=AttributedField.unknown)
    stage: AttributedField = Field(default_factory=AttributedField.unknown)
    funding: AttributedField = Field(default_factory=AttributedField.unknown)
    products: list[AttributedField] = Field(default_factory=list)
    technology: list[AttributedField] = Field(default_factory=list)
    ai_usage: AttributedField = Field(default_factory=AttributedField.unknown)
    hiring_ai: AttributedField = Field(default_factory=AttributedField.unknown)
    hiring_backend: AttributedField = Field(default_factory=AttributedField.unknown)
    hiring_product: AttributedField = Field(default_factory=AttributedField.unknown)
    hiring_ml: AttributedField = Field(default_factory=AttributedField.unknown)
    intent: AttributedField = Field(default_factory=AttributedField.unknown)
    intent_reason: AttributedField = Field(default_factory=AttributedField.unknown)
    needs: list[AttributedField] = Field(default_factory=list)
    decision_makers: list[AttributedField] = Field(default_factory=list)
    contacts_email: list[AttributedField] = Field(default_factory=list)
    contacts_linkedin: list[AttributedField] = Field(default_factory=list)
    contacts_phone: list[AttributedField] = Field(default_factory=list)
    contacts_twitter: list[AttributedField] = Field(default_factory=list)
    evidence_sources: list[AttributedField] = Field(default_factory=list)
    trust: float = 0.0
    sales_ready: bool = False
    questions: TruthQuestions = Field(default_factory=TruthQuestions)
    scoring_version: str = "alpha-plus-v1"
    evidence: list[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    date: datetime | str | None = None
    event: str = UNKNOWN
    source: str = UNKNOWN
    confidence: float | None = None
    evidence: list[str] = Field(default_factory=list)


class CompanyTimeline(BaseModel):
    events: list[TimelineEvent] = Field(default_factory=list)
    why_now: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class ContactWaterfallV2Result(BaseModel):
    sources_tried: list[str] = Field(default_factory=list)
    sources_hit: list[str] = Field(default_factory=list)
    emails: list[AttributedField] = Field(default_factory=list)
    phones: list[AttributedField] = Field(default_factory=list)
    linkedin: list[AttributedField] = Field(default_factory=list)
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class IntelligenceCard(BaseModel):
    company_id: str
    company_name: str = UNKNOWN
    identity: str = UNKNOWN
    website: Any = UNKNOWN
    description: Any = UNKNOWN
    products: list[str] = Field(default_factory=list)
    funding: Any = UNKNOWN
    hiring: list[str] = Field(default_factory=list)
    technology: list[str] = Field(default_factory=list)
    buying_intent: Any = UNKNOWN
    decision_makers: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    pain: str = UNKNOWN
    recommended_service: str = UNKNOWN
    next_action: str = UNKNOWN
    probability: float = 0.0
    trust: float = 0.0
    sales_ready: bool = False
    scoring_version: str = "alpha-plus-v1"


class FounderQueueItem(BaseModel):
    company_id: str
    company: str = UNKNOWN
    reason: str = UNKNOWN
    evidence: str = UNKNOWN
    contact: str = UNKNOWN
    email: str = UNKNOWN
    phone: str = UNKNOWN
    decision_maker: str = UNKNOWN
    service: str = UNKNOWN
    estimated_deal: str = UNKNOWN
    next_step: str = UNKNOWN
    open_profile: str = UNKNOWN
    approve: bool = False
    trust: float = 0.0
    score: float = 0.0


class QualityFunnel(BaseModel):
    companies: int = 0
    rejected: int = 0
    fake: int = 0
    missing_website: int = 0
    missing_evidence: int = 0
    sales_ready: int = 0
    enterprise_ready: int = 0
    by_rejection_reason: dict[str, int] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class RejectionRecord(BaseModel):
    company_id: str
    company_name: str = UNKNOWN
    reasons: list[RejectionReason] = Field(default_factory=list)
    explanation: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class DailyImprovementReport(BaseModel):
    date: str = UNKNOWN
    collected: int = 0
    rejected: int = 0
    passed: int = 0
    sales_ready: int = 0
    enterprise: int = 0
    emails_recovered: int = 0
    phones_recovered: int = 0
    fake_removed: int = 0
    duplicates_merged: int = 0
    average_quality: float = 0.0
    todays_best_company: str = UNKNOWN
    todays_best_potential: str = UNKNOWN
    todays_best_missing: str = UNKNOWN
    scoring_version: str = "alpha-plus-v1"
    evidence: list[str] = Field(default_factory=list)


class ProductionLockResult(BaseModel):
    unlocked: bool = False
    identity: bool = False
    website: bool = False
    evidence_ok: bool = False
    intent: bool = False
    decision_maker_or_email: bool = False
    sales_readiness_80: bool = False
    not_duplicate: bool = False
    not_fake: bool = False
    source_known: bool = False
    trust_90: bool = False
    failures: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class GtAcceptance(BaseModel):
    real_companies: int = 0
    real_identities_percent: float = 0.0
    websites_percent: float = 0.0
    decision_makers_percent: float = 0.0
    verified_contact_percent: float = 0.0
    duplicate_percent: float = 100.0
    fake_percent: float = 100.0
    evidence_coverage_percent: float = 0.0
    founder_email_confidence_percent: float = 0.0
    production_unlocked: bool = False
    failures: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class GtSnapshot(BaseModel):
    company_id: str
    company_name: str = UNKNOWN
    verdict: GtVerdict = GtVerdict.REJECTED
    questions: TruthQuestions = Field(default_factory=TruthQuestions)
    truth: CompanyTruthProfile | None = None
    contacts: ContactWaterfallV2Result = Field(default_factory=ContactWaterfallV2Result)
    timeline: CompanyTimeline = Field(default_factory=CompanyTimeline)
    card: IntelligenceCard | None = None
    founder_item: FounderQueueItem | None = None
    rejection: RejectionRecord | None = None
    production_lock: ProductionLockResult = Field(default_factory=ProductionLockResult)
    trust: float = 0.0
    readiness: float = 0.0
    scoring_version: str = "alpha-plus-v1"
    evidence: list[str] = Field(default_factory=list)
