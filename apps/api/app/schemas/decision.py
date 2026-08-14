from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DecisionMakerEntryResponse(BaseModel):
    id: UUID
    name: str
    role: str
    normalized_role: str
    department: str | None = None
    work_email: str | None = None
    business_phone: str | None = None
    linkedin_url: str | None = None
    is_primary: bool
    is_secondary: bool
    buyer_match_score: float
    confidence: float
    source: str
    source_url: str | None = None
    evidence: str


class DepartmentResponse(BaseModel):
    name: str
    signal_strength: float
    headcount_signal: str | None = None
    source: str
    source_url: str | None = None
    evidence: str


class ContactChannelResponse(BaseModel):
    kind: str
    value: str
    label: str | None = None
    rank: int
    confidence: float
    source: str
    source_url: str | None = None
    is_verified_public: bool
    evidence: str


class PublicProfileResponse(BaseModel):
    platform: str
    url: str
    handle: str | None = None
    confidence: float
    source: str


class LeadershipResponse(BaseModel):
    name: str
    title: str
    department: str | None = None
    confidence: float
    source: str
    source_url: str | None = None
    evidence: str


class ConfidenceResponse(BaseModel):
    leadership_confidence: float
    department_confidence: float
    contact_confidence: float
    buyer_match_confidence: float
    overall_discovery_score: float


class DecisionDiscoveryResponse(BaseModel):
    id: UUID
    company_id: UUID
    opportunity_id: UUID
    company_name: str
    opportunity_score: float
    business_pain: str
    recommended_service: str
    primary_decision_maker: DecisionMakerEntryResponse | None = None
    secondary_decision_maker: DecisionMakerEntryResponse | None = None
    decision_makers: list[DecisionMakerEntryResponse] = Field(default_factory=list)
    departments: list[DepartmentResponse] = Field(default_factory=list)
    leadership: list[LeadershipResponse] = Field(default_factory=list)
    contact_channels: list[ContactChannelResponse] = Field(default_factory=list)
    public_emails: list[str] = Field(default_factory=list)
    public_phones: list[str] = Field(default_factory=list)
    public_profiles: list[PublicProfileResponse] = Field(default_factory=list)
    best_outreach_sequence: list[dict[str, Any]] = Field(default_factory=list)
    no_public_contact_message: str | None = None
    buyer_match_confidence: float
    reason: str
    evidence_chain: list[dict[str, Any]] = Field(default_factory=list)
    source_attribution: list[dict[str, Any]] = Field(default_factory=list)
    confidence: ConfidenceResponse
    created_at: datetime


class DecisionRefreshResponse(BaseModel):
    refreshed: bool
    report: DecisionDiscoveryResponse | None = None


class DecisionSearchResponse(BaseModel):
    results: list[DecisionMakerEntryResponse]
