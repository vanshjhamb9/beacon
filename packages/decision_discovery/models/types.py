from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DiscoverySourceType(StrEnum):
    COMPANY_WEBSITE = "company_website"
    COMPANY_CONTACT_PAGE = "company_contact_page"
    COMPANY_CAREERS_PAGE = "company_careers_page"
    COMPANY_PRESS_PAGE = "company_press_page"
    LINKEDIN_COMPANY = "linkedin_company"
    GITHUB_ORGANIZATION = "github_organization"
    TWITTER_COMPANY = "twitter_company"
    FACEBOOK_COMPANY = "facebook_company"
    YOUTUBE_COMPANY = "youtube_company"
    BEACON_ENRICHMENT = "beacon_enrichment"
    BEACON_VERIFICATION = "beacon_verification"
    BEACON_REVENUE = "beacon_revenue"
    BEACON_CONTEXT = "beacon_context"
    BEACON_INTELLIGENCE = "beacon_intelligence"
    LICENSED_PROVIDER = "licensed_provider"
    USER_PROVIDED = "user_provided"


class DecisionRole(StrEnum):
    FOUNDER = "Founder"
    CEO = "CEO"
    CTO = "CTO"
    COO = "COO"
    HEAD_OF_ENGINEERING = "Head of Engineering"
    ENGINEERING_MANAGER = "Engineering Manager"
    HEAD_OF_CUSTOMER_SUPPORT = "Head of Customer Support"
    SUPPORT_MANAGER = "Support Manager"
    HEAD_OF_OPERATIONS = "Head of Operations"
    MARKETING_HEAD = "Marketing Head"
    SALES_HEAD = "Sales Head"
    PRODUCT_MANAGER = "Product Manager"
    AI_LEAD = "AI Lead"
    INNOVATION_LEAD = "Innovation Lead"
    OTHER = "Other"


class ContactChannelKind(StrEnum):
    FOUNDER_EMAIL = "founder_email"
    EXECUTIVE_EMAIL = "executive_email"
    ROLE_BASED_EMAIL = "role_based_email"
    BUSINESS_EMAIL = "business_email"
    CONTACT_FORM = "contact_form"
    BUSINESS_PHONE = "business_phone"
    LINKEDIN_COMPANY = "linkedin_company"
    GITHUB_ORGANIZATION = "github_organization"
    TWITTER_COMPANY = "twitter_company"
    FACEBOOK_COMPANY = "facebook_company"
    YOUTUBE_COMPANY = "youtube_company"
    CAREERS_PAGE = "careers_page"
    PRESS_PAGE = "press_page"
    SUPPORT_EMAIL = "support_email"
    SALES_EMAIL = "sales_email"


class FieldAttribution(BaseModel):
    model_config = ConfigDict(frozen=True)

    field_name: str
    value: Any
    source: DiscoverySourceType
    source_url: str | None = None
    confidence: float = Field(ge=0.0, le=100.0)
    evidence: str = ""


class DecisionMakerCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    role: str
    normalized_role: DecisionRole
    department: str | None = None
    seniority_rank: int = 50
    work_email: str | None = None
    business_phone: str | None = None
    linkedin_url: str | None = None
    is_primary: bool = False
    is_secondary: bool = False
    buyer_match_score: float = Field(default=0.0, ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=100.0)
    source: DiscoverySourceType
    source_url: str | None = None
    evidence: str = ""


class DepartmentEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    signal_strength: float = Field(ge=0.0, le=100.0)
    headcount_signal: str | None = None
    source: DiscoverySourceType
    source_url: str | None = None
    evidence: str = ""


class ContactChannel(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: ContactChannelKind
    value: str
    label: str | None = None
    rank: int = 100
    confidence: float = Field(ge=0.0, le=100.0)
    source: DiscoverySourceType
    source_url: str | None = None
    is_verified_public: bool = True
    evidence: str = ""


class PublicProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    platform: str
    url: str
    handle: str | None = None
    confidence: float = Field(ge=0.0, le=100.0)
    source: DiscoverySourceType
    source_url: str | None = None


class LeadershipEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    title: str
    department: str | None = None
    confidence: float = Field(ge=0.0, le=100.0)
    source: DiscoverySourceType
    source_url: str | None = None
    evidence: str = ""


class OutreachStep(BaseModel):
    model_config = ConfigDict(frozen=True)

    rank: int
    channel_kind: ContactChannelKind
    value: str
    rationale: str
    confidence: float = Field(ge=0.0, le=100.0)
    source: DiscoverySourceType
    source_url: str | None = None


class DiscoveryConfidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    leadership_confidence: float = Field(ge=0.0, le=100.0)
    department_confidence: float = Field(ge=0.0, le=100.0)
    contact_confidence: float = Field(ge=0.0, le=100.0)
    buyer_match_confidence: float = Field(ge=0.0, le=100.0)
    overall_discovery_score: float = Field(ge=0.0, le=100.0)


class EvidenceChainItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: str
    summary: str
    source: DiscoverySourceType
    source_url: str | None = None
    confidence: float = Field(ge=0.0, le=100.0)
    reference_id: str | None = None


class SourceAttribution(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: DiscoverySourceType
    source_url: str | None = None
    fields: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=100.0)
    licensed: bool = False
    notes: str = ""


class DecisionMakerReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    opportunity_id: UUID
    verification_report_id: UUID | None = None
    enrichment_report_id: UUID | None = None
    company_name: str
    opportunity_score: float
    business_pain: str
    recommended_service: str
    primary_decision_maker: DecisionMakerCandidate | None = None
    secondary_decision_maker: DecisionMakerCandidate | None = None
    decision_makers: list[DecisionMakerCandidate] = Field(default_factory=list)
    departments: list[DepartmentEntry] = Field(default_factory=list)
    leadership: list[LeadershipEntry] = Field(default_factory=list)
    contact_channels: list[ContactChannel] = Field(default_factory=list)
    public_emails: list[str] = Field(default_factory=list)
    public_phones: list[str] = Field(default_factory=list)
    public_profiles: list[PublicProfile] = Field(default_factory=list)
    best_outreach_sequence: list[OutreachStep] = Field(default_factory=list)
    no_public_contact_message: str | None = None
    buyer_match_confidence: float = Field(ge=0.0, le=100.0)
    reason: str
    evidence_chain: list[EvidenceChainItem] = Field(default_factory=list)
    source_attribution: list[SourceAttribution] = Field(default_factory=list)
    confidence: DiscoveryConfidence
    processing_latency_ms: float = 0.0
    report_payload: dict[str, Any] = Field(default_factory=dict)


class DecisionDiscoveryInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    opportunity_id: UUID
    company_name: str
    domain: str | None = None
    website: str | None = None
    opportunity_score: float
    opportunity_status: str
    business_pain: str
    recommended_service: str
    buyer_persona: str | None = None
    revenue_recommendation: dict[str, Any] = Field(default_factory=dict)
    lead_profile: dict[str, Any] = Field(default_factory=dict)
    verification_payload: dict[str, Any] = Field(default_factory=dict)
    context_intelligence: dict[str, Any] = Field(default_factory=dict)
    known_people: list[dict[str, Any]] = Field(default_factory=list)
    enrichment_contacts: list[dict[str, Any]] = Field(default_factory=list)
    enrichment_people: list[dict[str, Any]] = Field(default_factory=list)
    enrichment_profiles: list[dict[str, Any]] = Field(default_factory=list)
    enrichment_report_id: UUID | None = None
    verification_report_id: UUID | None = None
    force_refresh: bool = False
