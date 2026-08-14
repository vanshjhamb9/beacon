from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

UNKNOWN = "UNKNOWN"


class RevenueVerdict(StrEnum):
    """Binary outcome — no middle state for revenue surfaces."""

    REJECTED = "REJECTED"
    SALES_READY = "SALES_READY"


class SurfaceStatus(StrEnum):
    """Statuses allowed into founder/revenue surfaces (Rule 9)."""

    CONTACT_READY = "CONTACT READY"
    SALES_READY = "SALES READY"
    ENTERPRISE_READY = "ENTERPRISE READY"


class AttributedField(BaseModel):
    value: Any = UNKNOWN
    source: str = UNKNOWN
    collected_at: datetime | str | None = None
    confidence: float | None = None
    verification: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)

    @classmethod
    def unknown(cls, *, reason: str = "not_observed") -> AttributedField:
        return cls(value=UNKNOWN, source=UNKNOWN, confidence=None, verification=UNKNOWN, evidence=[reason])

    @classmethod
    def of(
        cls,
        value: Any,
        *,
        source: str,
        collected_at: datetime | str | None = None,
        confidence: float | None = None,
        verification: str = "unverified",
        evidence: list[str] | None = None,
    ) -> AttributedField:
        if value is None or value == "" or value == UNKNOWN:
            return cls.unknown()
        return cls(
            value=value,
            source=source or UNKNOWN,
            collected_at=collected_at,
            confidence=confidence,
            verification=verification,
            evidence=list(evidence or []),
        )


class SalesReadyRequirement(BaseModel):
    field: str
    present: bool = False
    value: Any = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class SalesReadyGateResult(BaseModel):
    verdict: RevenueVerdict = RevenueVerdict.REJECTED
    requirements: list[SalesReadyRequirement] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    complete: bool = False
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class WaterfallSourceResult(BaseModel):
    source: str
    found: bool = False
    contacts_found: int = 0
    confidence_boost: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class ContactWaterfallResult(BaseModel):
    sources_tried: list[WaterfallSourceResult] = Field(default_factory=list)
    contacts: list[dict[str, Any]] = Field(default_factory=list)
    total_confidence: float = 0.0
    emails: list[AttributedField] = Field(default_factory=list)
    phones: list[AttributedField] = Field(default_factory=list)
    decision_makers: list[AttributedField] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class CrawlDiscovery(BaseModel):
    page_type: str
    url: str = UNKNOWN
    found: bool = False
    evidence: list[str] = Field(default_factory=list)


class WebsiteCrawlResult(BaseModel):
    pages: list[CrawlDiscovery] = Field(default_factory=list)
    emails: list[AttributedField] = Field(default_factory=list)
    phones: list[AttributedField] = Field(default_factory=list)
    social: dict[str, AttributedField] = Field(default_factory=dict)
    founders: list[AttributedField] = Field(default_factory=list)
    executives: list[AttributedField] = Field(default_factory=list)
    schema_org: dict[str, Any] = Field(default_factory=dict)
    open_graph: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class IdentityValidationResult(BaseModel):
    accepted: bool = False
    rejected: bool = False
    rejection_reasons: list[str] = Field(default_factory=list)
    checks: dict[str, bool] = Field(default_factory=dict)
    legal_name: AttributedField = Field(default_factory=AttributedField.unknown)
    linkedin_exists: bool = False
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class ConfidentContact(BaseModel):
    name: str = UNKNOWN
    role: str = UNKNOWN
    email: AttributedField = Field(default_factory=AttributedField.unknown)
    phone: AttributedField = Field(default_factory=AttributedField.unknown)
    linkedin: AttributedField = Field(default_factory=AttributedField.unknown)
    source: str = UNKNOWN
    collected_at: datetime | str | None = None
    confidence: float = 0.0
    verification: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class ContactConfidenceResult(BaseModel):
    contacts: list[ConfidentContact] = Field(default_factory=list)
    average_confidence: float = 0.0
    verified_email_count: int = 0
    verified_phone_count: int = 0
    evidence: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    collected_from: str = UNKNOWN
    url: str = UNKNOWN
    date: datetime | str | None = None
    collector: str = UNKNOWN
    evidence: str = UNKNOWN
    reason: str = UNKNOWN


class EvidencePanel(BaseModel):
    items: list[EvidenceItem] = Field(default_factory=list)
    complete: bool = False
    evidence: list[str] = Field(default_factory=list)


class DuplicateMatch(BaseModel):
    company_a: str
    company_b: str
    match_keys: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    merge_recommended: bool = False
    evidence: list[str] = Field(default_factory=list)


class DuplicateRecoveryResult(BaseModel):
    matches: list[DuplicateMatch] = Field(default_factory=list)
    duplicate_rate: float = 0.0
    merge_plans: int = 0
    evidence: list[str] = Field(default_factory=list)


class CompanyProfile(BaseModel):
    company_id: str
    company_name: str = UNKNOWN
    logo: Any = UNKNOWN
    website: Any = UNKNOWN
    industry: Any = UNKNOWN
    hq: Any = UNKNOWN
    employees: Any = UNKNOWN
    funding: Any = UNKNOWN
    founded: Any = UNKNOWN
    revenue_estimate: Any = UNKNOWN
    tech_stack: list[str] = Field(default_factory=list)
    hiring: list[str] = Field(default_factory=list)
    intent: str = UNKNOWN
    pain: str = UNKNOWN
    recommended_service: str = UNKNOWN
    decision_makers: list[ConfidentContact] = Field(default_factory=list)
    verified_emails: list[AttributedField] = Field(default_factory=list)
    verified_phones: list[AttributedField] = Field(default_factory=list)
    linkedin: Any = UNKNOWN
    confidence: float = 0.0
    evidence_timeline: list[EvidenceItem] = Field(default_factory=list)
    outreach_recommendation: str = UNKNOWN
    sales_ready_badge: bool = False
    verdict: RevenueVerdict = RevenueVerdict.REJECTED
    scoring_version: str = "rqp-v1"
    evidence: list[str] = Field(default_factory=list)


class SurfaceAdmission(BaseModel):
    admitted: bool = False
    status: str = UNKNOWN
    surfaces: list[str] = Field(default_factory=list)
    hidden: bool = True
    evidence: list[str] = Field(default_factory=list)


class DailyKpiReport(BaseModel):
    collected_today: int = 0
    rejected_today: int = 0
    recovered_today: int = 0
    identity_percent: float = 0.0
    website_percent: float = 0.0
    contacts_percent: float = 0.0
    decision_makers_percent: float = 0.0
    sales_ready_percent: float = 0.0
    enterprise_percent: float = 0.0
    average_confidence: float = 0.0
    duplicates: int = 0
    fake_companies: int = 0
    scoring_version: str = "rqp-v1"


class GoldenCompany(BaseModel):
    company_id: str
    company_name: str
    website: str
    domain: str
    linkedin_company: str
    industry: str
    country: str
    employee_estimate: int
    verified: bool = True
    evidence: list[str] = Field(default_factory=list)


class GoldenDataset(BaseModel):
    companies: list[GoldenCompany] = Field(default_factory=list)
    size: int = 0
    benchmark_version: str = "beacon-gold-v1"
    evidence: list[str] = Field(default_factory=list)


class AcceptanceCriteria(BaseModel):
    identity_percent: float = 0.0
    website_percent: float = 0.0
    verified_email_percent: float = 0.0
    phone_or_alt_percent: float = 0.0
    duplicate_rate: float = 100.0
    fake_percent: float = 100.0
    evidence_attribution_percent: float = 0.0
    founder_queue_sales_ready_only: bool = False
    outreach_ready_count: int = 0
    manual_review_sample: int = 0
    manual_review_accuracy: float = 0.0
    production_unlocked: bool = False
    failures: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class RqpSnapshot(BaseModel):
    company_id: str
    company_name: str = UNKNOWN
    verdict: RevenueVerdict = RevenueVerdict.REJECTED
    sales_ready_gate: SalesReadyGateResult = Field(default_factory=SalesReadyGateResult)
    identity: IdentityValidationResult = Field(default_factory=IdentityValidationResult)
    crawl: WebsiteCrawlResult = Field(default_factory=WebsiteCrawlResult)
    waterfall: ContactWaterfallResult = Field(default_factory=ContactWaterfallResult)
    contacts: ContactConfidenceResult = Field(default_factory=ContactConfidenceResult)
    evidence_panel: EvidencePanel = Field(default_factory=EvidencePanel)
    profile: CompanyProfile | None = None
    surface: SurfaceAdmission = Field(default_factory=SurfaceAdmission)
    confidence: float = 0.0
    scoring_version: str = "rqp-v1"
    evidence: list[str] = Field(default_factory=list)
