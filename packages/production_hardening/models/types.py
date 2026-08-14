from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AdmissionVerdict(StrEnum):
    ADMIT = "admit"
    REJECT = "reject"


class ContactReadinessStatus(StrEnum):
    NOT_READY = "not_ready"
    PARTIAL = "partial"
    CONTACT_READY = "contact_ready"
    SALES_READY = "sales_ready"


class AdmissionDecision(BaseModel):
    verdict: AdmissionVerdict
    reasons: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    company_name: str | None = None
    domain: str | None = None


class IdentityReport(BaseModel):
    company_name: str
    official_domain: str | None = None
    website_title: str | None = None
    logo_url: str | None = None
    industry: str | None = None
    country: str | None = None
    linkedin_company_url: str | None = None
    description: str | None = None
    employee_estimate: str | None = None
    technology_stack: list[str] = Field(default_factory=list)
    first_seen_at: datetime | None = None
    last_verified_at: datetime | None = None
    confidence: float = 0.0
    admitted: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ContactReadiness(BaseModel):
    status: ContactReadinessStatus
    has_website: bool = False
    has_verified_email: bool = False
    has_contact_form: bool = False
    has_phone: bool = False
    has_decision_maker: bool = False
    has_linkedin: bool = False
    has_business_evidence: bool = False
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    why_unavailable: str | None = None
    responsible_engine: str | None = None


class LeadQualityScore(BaseModel):
    total: float
    business_identity: float = 0.0
    verified_website: float = 0.0
    intent_signals: float = 0.0
    decision_maker: float = 0.0
    verified_email: float = 0.0
    verified_phone: float = 0.0
    freshness: float = 0.0
    technology_match: float = 0.0
    buying_signals: float = 0.0
    visible: bool = False
    evidence: list[str] = Field(default_factory=list)


class EvidenceCard(BaseModel):
    source: str
    connector: str | None = None
    collected_at: datetime | None = None
    snippets: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    confidence: float | None = None
    freshness_hours: float | None = None
    verification_status: str | None = None


class DuplicateMergePlan(BaseModel):
    canonical_company_id: str
    merged_company_ids: list[str] = Field(default_factory=list)
    match_keys: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class TrustMetrics(BaseModel):
    companies_collected: int = 0
    qualified: int = 0
    rejected: int = 0
    merged: int = 0
    duplicate_percent: float = 0.0
    verified_websites_percent: float = 0.0
    verified_emails_percent: float = 0.0
    verified_phones_percent: float = 0.0
    decision_makers_percent: float = 0.0
    average_confidence: float = 0.0
    average_freshness_hours: float | None = None
    collector_health: dict[str, Any] = Field(default_factory=dict)
    daily_pipeline_conversion: dict[str, float] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class FounderCompanyCard(BaseModel):
    company_id: str
    company: str
    industry: str | None = None
    location: str | None = None
    employees: str | None = None
    website: str | None = None
    source: str | None = None
    intent: str | None = None
    score: float = 0.0
    decision_maker: str | None = None
    verified_email: str | None = None
    verified_phone: str | None = None
    recommended_service: str | None = None
    estimated_deal: str | None = None
    confidence: float = 0.0
    contact_readiness: ContactReadinessStatus = ContactReadinessStatus.NOT_READY
    visible_in_founder_queue: bool = False
    evidence_cards: list[EvidenceCard] = Field(default_factory=list)
