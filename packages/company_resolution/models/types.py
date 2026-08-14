"""CRE v1 types — Signal → Evidence → Identity → Verification → Company."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

UNKNOWN = "unknown"


class CreVerdict(StrEnum):
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class RejectionReason(StrEnum):
    NO_ORGANIZATION = "No Organization"
    NO_DOMAIN = "No Domain"
    NO_OFFICIAL_URL = "No Official URL"
    LOW_IDENTITY_CONFIDENCE = "Low Identity Confidence"
    WEBSITE_INVALID = "Website Invalid"
    PARKED_DOMAIN = "Parked Domain"
    PERSONAL_BLOG = "Personal Blog"
    GITHUB_PAGES = "GitHub Pages"
    DOCUMENTATION = "Documentation"
    MEDIUM = "Medium"
    NEWS_SITE = "News Site"
    FORUM = "Forum"
    REPOSITORY = "Repository"
    PLATFORM_DOMAIN = "Platform Domain"
    FAKE_NAME = "Fake Name"
    SOURCE_POLICY = "Source Policy Block"
    MISSING_ATTRIBUTION = "Missing Attribution"
    INCONSISTENT_IDENTITY = "Inconsistent Identity"


class RawSignalEnvelope(BaseModel):
    """Phase 1 — collectors emit signals, never companies."""

    model_config = ConfigDict(frozen=True)

    signal_id: str = UNKNOWN
    title: str = ""
    body: str = ""
    url: str | None = None
    source: str = UNKNOWN
    author: str | None = None
    timestamp: datetime | str | None = None
    extracted_entities: list[str] = Field(default_factory=list)
    outbound_links: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_raw(
        cls,
        *,
        signal_id: str,
        title: str,
        body: str,
        url: str | None,
        source: str,
        author: str | None = None,
        timestamp: datetime | str | None = None,
        metadata: dict[str, Any] | None = None,
        extracted_entities: list[str] | None = None,
        outbound_links: list[str] | None = None,
        domains: list[str] | None = None,
        mentions: list[str] | None = None,
    ) -> RawSignalEnvelope:
        return cls(
            signal_id=signal_id,
            title=title or "",
            body=body or "",
            url=url,
            source=source or UNKNOWN,
            author=author,
            timestamp=timestamp,
            extracted_entities=list(extracted_entities or []),
            outbound_links=list(outbound_links or []),
            domains=list(domains or []),
            mentions=list(mentions or []),
            metadata=dict(metadata or {}),
        )


class OrganizationCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    legal_name: str = UNKNOWN
    official_domain: str | None = None
    official_url: str | None = None
    linkedin_company: str | None = None
    github_organization: str | None = None
    funding_page: str | None = None
    homepage: str | None = None
    business_registration: str | None = None
    evidence: list[str] = Field(default_factory=list)
    found: bool = False


class IdentityConfidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: float = 0.0
    legal_name_score: float = 0.0
    domain_score: float = 0.0
    website_score: float = 0.0
    industry_score: float = 0.0
    description_score: float = 0.0
    country_score: float = 0.0
    linkedin_score: float = 0.0
    consistency_score: float = 0.0
    passed: bool = False
    threshold: float = 90.0
    evidence: list[str] = Field(default_factory=list)


class WebsiteValidation(BaseModel):
    model_config = ConfigDict(frozen=True)

    domain: str | None = None
    valid: bool = False
    http_status: int | None = None
    ssl: bool = False
    reject_reason: RejectionReason | None = None
    title: str | None = None
    evidence: list[str] = Field(default_factory=list)


class SourceAttribution(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str = UNKNOWN
    source: str = UNKNOWN
    source_url: str | None = None
    article_url: str | None = None
    reddit_thread: str | None = None
    product_hunt_page: str | None = None
    devto_article: str | None = None
    hn_item: str | None = None
    collected_at: datetime | str | None = None
    complete: bool = False
    evidence: list[str] = Field(default_factory=list)


class CreAdmission(BaseModel):
    model_config = ConfigDict(frozen=True)

    admitted: bool = False
    verdict: CreVerdict = CreVerdict.REJECTED
    reasons: list[RejectionReason] = Field(default_factory=list)
    explanation: str = ""
    allow_create_company: bool = False
    evidence: list[str] = Field(default_factory=list)


class CreSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    source: str
    verdict: CreVerdict
    signal: RawSignalEnvelope
    organization: OrganizationCandidate
    identity: IdentityConfidence
    website: WebsiteValidation
    attribution: SourceAttribution
    admission: CreAdmission
    company_name: str | None = None
    company_domain: str | None = None
    scoring_version: str = "cre-v1"
    evidence: list[str] = Field(default_factory=list)
    false_positive_example: bool = False


class CreRebuildReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_raw_signals: int = 0
    resolved_companies: int = 0
    verified_companies: int = 0
    sales_ready: int = 0
    companies_created: int = 0
    companies_rejected: int = 0
    resolution_success_rate: float = 0.0
    rejection_reasons: dict[str, int] = Field(default_factory=dict)
    identity_confidence_distribution: dict[str, int] = Field(default_factory=dict)
    source_precision: dict[str, dict[str, float | int]] = Field(default_factory=dict)
    top_verified: list[dict[str, Any]] = Field(default_factory=list)
    rejected_examples: list[dict[str, Any]] = Field(default_factory=list)
    scoring_version: str = "cre-v1"
    evidence: list[str] = Field(default_factory=list)
