"""EROWD v1 types — official website is identity; everything else is evidence."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

UNKNOWN = "unknown"


class ErowdVerdict(StrEnum):
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"
    SIGNAL_ONLY = "SIGNAL_ONLY"


class RejectionReason(StrEnum):
    NO_OFFICIAL_WEBSITE = "No Official Website"
    PLATFORM_URL_AS_IDENTITY = "Platform URL As Identity"
    WEBSITE_UNVERIFIED = "Website Unverified"
    LOW_IDENTITY_CONFIDENCE = "Low Identity Confidence"
    FABRICATED_DOMAIN = "Fabricated Domain"
    ARTICLE_ONLY = "Article Only"
    SOURCE_SIGNAL_ONLY = "Source Signal Only"
    NO_ENTITY_NAME = "No Entity Name"
    INCONSISTENT_IDENTITY = "Inconsistent Identity"


class OfficialWebsite(BaseModel):
    model_config = ConfigDict(frozen=True)

    website: str | None = None
    domain: str | None = None
    source: str = UNKNOWN
    confidence: float = 0.0
    verified_at: datetime | str | None = None
    discovered: bool = False
    evidence: list[str] = Field(default_factory=list)


class WebsiteAttribution(BaseModel):
    model_config = ConfigDict(frozen=True)

    website: str | None = None
    domain: str | None = None
    discovery_source: str = UNKNOWN
    collector: str = UNKNOWN
    confidence: float = 0.0
    timestamp: datetime | str | None = None
    evidence: list[str] = Field(default_factory=list)


class DomainValidation(BaseModel):
    model_config = ConfigDict(frozen=True)

    domain: str | None = None
    verified: bool = False
    https: bool = False
    dns_ok: bool = False
    status_ok: bool = False
    ssl_ok: bool = False
    homepage_reachable: bool = False
    title: str | None = None
    favicon_url: str | None = None
    redirect_final: str | None = None
    reason: str = ""
    evidence: list[str] = Field(default_factory=list)


class EntityCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = UNKNOWN
    aliases: list[str] = Field(default_factory=list)
    organization: str | None = None
    official_website: str | None = None
    domain: str | None = None
    normalized_key: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class CanonicalIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_name: str = UNKNOWN
    official_website: str | None = None
    domain: str | None = None
    logo_url: str | None = None
    industry: str | None = None
    country: str | None = None
    linkedin_url: str | None = None
    description: str | None = None
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class IdentityScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: float = 0.0
    website_discovered: float = 0.0
    https: float = 0.0
    name_match: float = 0.0
    linkedin_match: float = 0.0
    favicon_title: float = 0.0
    industry: float = 0.0
    passed: bool = False
    threshold: float = 90.0
    evidence: list[str] = Field(default_factory=list)


class EvidenceEdge(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    website: str | None = None
    company_key: str | None = None
    edge_type: str = "signal_to_website"
    source: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class ErowdAdmission(BaseModel):
    model_config = ConfigDict(frozen=True)

    admitted: bool = False
    verdict: ErowdVerdict = ErowdVerdict.REJECTED
    reasons: list[RejectionReason] = Field(default_factory=list)
    explanation: str = ""
    allow_create_company: bool = False
    evidence: list[str] = Field(default_factory=list)


class ErowdSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    source: str
    verdict: ErowdVerdict
    entity: EntityCandidate
    website: OfficialWebsite
    attribution: WebsiteAttribution
    validation: DomainValidation
    identity: CanonicalIdentity
    score: IdentityScore
    admission: ErowdAdmission
    evidence_edges: list[EvidenceEdge] = Field(default_factory=list)
    scoring_version: str = "erowd-v1"
    evidence: list[str] = Field(default_factory=list)


class ErowdRebuildReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_signals: int = 0
    entity_candidates: int = 0
    official_websites: int = 0
    verified_companies: int = 0
    sales_ready: int = 0
    admitted: int = 0
    rejected: int = 0
    discovery_rate: float = 0.0
    verification_rate: float = 0.0
    false_positives: int = 0
    identity_confidence_distribution: dict[str, int] = Field(default_factory=dict)
    source_precision: dict[str, dict[str, float | int]] = Field(default_factory=dict)
    top_verified: list[dict[str, Any]] = Field(default_factory=list)
    rejected_examples: list[dict[str, Any]] = Field(default_factory=list)
    scoring_version: str = "erowd-v1"
    evidence: list[str] = Field(default_factory=list)
