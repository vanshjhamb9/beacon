"""IGF v1 types — companies exist only after Identity Graph admits them."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

UNKNOWN = "unknown"
SCORING_VERSION = "igf-v1"


class CanonicalStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    MERGED = "MERGED"
    PENDING = "PENDING"


class SourceRole(StrEnum):
    IDENTITY = "identity"
    INTENT = "intent"
    CONVERSATION = "conversation"


class IgfVerdict(StrEnum):
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"
    SIGNAL_ONLY = "SIGNAL_ONLY"
    MERGED = "MERGED"


class RejectionReason(StrEnum):
    NO_OFFICIAL_WEBSITE = "No Official Website"
    CONVERSATION_SOURCE = "Conversation Source Cannot Create Identity"
    INTENT_SOURCE_ONLY = "Intent Source Cannot Create Identity"
    LOW_IDENTITY_CONFIDENCE = "Low Identity Confidence"
    NO_CANDIDATE_NAME = "No Candidate Name"
    FABRICATED_DOMAIN = "Fabricated Domain"
    DUPLICATE_PENDING_MERGE = "Duplicate Pending Merge"
    PLATFORM_DOMAIN = "Platform Domain Rejected"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"


class IdentityEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    field: str
    value: str
    confidence: float = 0.0
    collector: str = UNKNOWN
    timestamp: datetime | str | None = None
    verified: bool = False
    reason: str = ""
    evidence: list[str] = Field(default_factory=list)


class IdentityCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = UNKNOWN
    aliases: list[str] = Field(default_factory=list)
    possible_domain: str | None = None
    source: str = UNKNOWN
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)
    signal_id: str = UNKNOWN
    source_role: SourceRole = SourceRole.CONVERSATION


class CanonicalCompany(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str | None = None
    legal_name: str = UNKNOWN
    trade_name: str = UNKNOWN
    aliases: list[str] = Field(default_factory=list)
    official_domain: str | None = None
    website: str | None = None
    linkedin_company_url: str | None = None
    github_organization: str | None = None
    crunchbase: str | None = None
    industry: str | None = None
    country: str | None = None
    employee_range: str | None = None
    founded: str | None = None
    description: str | None = None
    evidence: list[IdentityEvidence] = Field(default_factory=list)
    confidence: float = 0.0
    verified_at: datetime | str | None = None
    last_seen: datetime | str | None = None
    collectors: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    status: CanonicalStatus = CanonicalStatus.PENDING


class MergeResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    canonical_id: str | None = None
    merged: bool = False
    matched_on: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class IdentityScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: float = 0.0
    passed: bool = False
    breakdown: dict[str, float] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class IgfAdmission(BaseModel):
    model_config = ConfigDict(frozen=True)

    admitted: bool = False
    verdict: IgfVerdict = IgfVerdict.REJECTED
    reasons: list[RejectionReason] = Field(default_factory=list)
    explanation: str = ""
    allow_create_company: bool = False
    evidence: list[str] = Field(default_factory=list)


class IgfSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    source: str
    source_role: SourceRole
    candidate: IdentityCandidate
    evidence_items: list[IdentityEvidence] = Field(default_factory=list)
    website: str | None = None
    domain: str | None = None
    score: IdentityScore = Field(default_factory=IdentityScore)
    merge: MergeResult = Field(default_factory=MergeResult)
    canonical: CanonicalCompany | None = None
    admission: IgfAdmission = Field(default_factory=IgfAdmission)
    scoring_version: str = SCORING_VERSION
    payload: dict[str, Any] = Field(default_factory=dict)


class IgfFunnelMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    signals: int = 0
    candidates: int = 0
    evidence_collected: int = 0
    official_websites: int = 0
    verified_companies: int = 0
    merged: int = 0
    rejected: int = 0
    pending: int = 0
    identity_precision: float = 0.0
    business_emails: int = 0
    decision_makers: int = 0
    sales_ready: int = 0
    revenue_ready: int = 0
    top_sources: dict[str, int] = Field(default_factory=dict)
    top_failures: dict[str, int] = Field(default_factory=dict)
    scoring_version: str = SCORING_VERSION
