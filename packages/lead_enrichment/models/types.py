from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EnrichmentSourceType(StrEnum):
    COMPANY_WEBSITE = "company_website"
    LINKEDIN = "linkedin"
    CRUNCHBASE = "crunchbase"
    PRODUCT_HUNT = "product_hunt"
    GITHUB = "github"
    TWITTER = "twitter"
    G2 = "g2"
    CAPTERRA = "capterra"
    BUILTWITH = "builtwith"
    WAPPALYZER = "wappalyzer"
    DNS_MX = "dns_mx"
    SSL_CERTIFICATE = "ssl_certificate"
    PUBLIC_JS = "public_js"
    BEACON_CONTEXT = "beacon_context"
    BEACON_OPPORTUNITY = "beacon_opportunity"
    BEACON_REVENUE = "beacon_revenue"
    BEACON_INTELLIGENCE = "beacon_intelligence"
    USER_PROVIDED = "user_provided"


class ContactKind(StrEnum):
    COMPANY_EMAIL = "company_email"
    ROLE_BASED_EMAIL = "role_based_email"
    BUSINESS_PHONE = "business_phone"
    GENERAL = "general"


class FieldAttribution(BaseModel):
    model_config = ConfigDict(frozen=True)

    field_name: str
    value: Any
    source: EnrichmentSourceType
    source_url: str | None = None
    confidence: float = Field(ge=0.0, le=100.0)
    evidence: str = ""


class EnrichedCompanyProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_name: str
    website: str | None = None
    domain: str | None = None
    industry: str | None = None
    sub_industry: str | None = None
    description: str | None = None
    location: str | None = None
    country: str | None = None
    founded_year: int | None = None
    employee_count_estimate: int | None = None
    company_size_range: str | None = None
    revenue_estimate: str | None = None
    attributions: list[FieldAttribution] = Field(default_factory=list)


class TechnologyEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    category: str
    confidence: float = Field(ge=0.0, le=100.0)
    source: EnrichmentSourceType
    source_url: str | None = None
    signal: str | None = None


class PersonEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    role: str
    department: str | None = None
    linkedin_url: str | None = None
    work_email: str | None = None
    business_phone: str | None = None
    confidence: float = Field(ge=0.0, le=100.0)
    source: EnrichmentSourceType
    source_url: str | None = None


class ContactEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: ContactKind
    value: str
    label: str | None = None
    confidence: float = Field(ge=0.0, le=100.0)
    source: EnrichmentSourceType
    source_url: str | None = None
    is_public: bool = True


class SocialProfileEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    platform: str
    url: str
    handle: str | None = None
    confidence: float = Field(ge=0.0, le=100.0)
    source: EnrichmentSourceType


class TeamInsights(BaseModel):
    model_config = ConfigDict(frozen=True)

    leadership_team_size: int | None = None
    engineering_team_estimate: int | None = None
    support_team_estimate: int | None = None
    operations_team_estimate: int | None = None
    recent_hires: list[str] = Field(default_factory=list)
    open_positions: list[str] = Field(default_factory=list)
    hiring_trends: str | None = None
    attributions: list[FieldAttribution] = Field(default_factory=list)


class JobEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    department: str | None = None
    location: str | None = None
    url: str | None = None
    confidence: float = Field(ge=0.0, le=100.0)
    source: EnrichmentSourceType
    source_url: str | None = None


class EnrichmentScores(BaseModel):
    model_config = ConfigDict(frozen=True)

    profile_completeness: float = Field(ge=0.0, le=100.0)
    contact_availability: float = Field(ge=0.0, le=100.0)
    technology_confidence: float = Field(ge=0.0, le=100.0)
    decision_maker_confidence: float = Field(ge=0.0, le=100.0)
    overall_enrichment_confidence: float = Field(ge=0.0, le=100.0)


class EvidenceChainItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: str
    summary: str
    source: EnrichmentSourceType
    source_url: str | None = None
    confidence: float = Field(ge=0.0, le=100.0)
    reference_id: str | None = None


class SourceAttribution(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: EnrichmentSourceType
    source_url: str | None = None
    fields: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=100.0)
    licensed: bool = False
    notes: str = ""


class SalesReadyLeadProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    opportunity_id: UUID
    company_name: str
    opportunity_score: float
    business_pain: str
    recommended_service: str
    buyer_persona: str
    company_profile: EnrichedCompanyProfile
    technology_stack: list[TechnologyEntry]
    decision_makers: list[PersonEntry]
    public_contact_information: list[ContactEntry]
    team_insights: TeamInsights
    social_profiles: list[SocialProfileEntry]
    open_jobs: list[JobEntry]
    estimated_budget: str | None
    priority: str | None
    why_now: str
    best_outreach_angle: str
    evidence_chain: list[EvidenceChainItem]
    source_attribution: list[SourceAttribution]
    enrichment_confidence: EnrichmentScores
    processing_latency_ms: float = 0.0


class EnrichmentOpportunityInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    opportunity_id: UUID
    company_name: str
    domain: str | None
    website: str | None
    opportunity_score: float
    opportunity_status: str
    opportunity_narrative: str
    industry: str | None
    description: str | None
    location: str | None
    country: str | None
    company_attributes: dict[str, Any] = Field(default_factory=dict)
    context_intelligence: dict[str, Any] = Field(default_factory=dict)
    technology_signals: list[dict[str, Any]] = Field(default_factory=list)
    pains: list[dict[str, Any]] = Field(default_factory=list)
    goals: list[dict[str, Any]] = Field(default_factory=list)
    known_people: list[dict[str, Any]] = Field(default_factory=list)
    revenue_recommendation: dict[str, Any] = Field(default_factory=dict)
    opportunity_evidence: list[dict[str, Any]] = Field(default_factory=list)
    force_refresh: bool = False


class WebsitePageContent(BaseModel):
    model_config = ConfigDict(frozen=True)

    url: str
    page_type: str
    html: str
    text: str
    status_code: int = 200


class WebsiteFetchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    domain: str | None
    pages: list[WebsitePageContent] = Field(default_factory=list)
    fetched: bool = False
    error: str | None = None


class DnsMxResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    domain: str
    mx_hosts: list[str] = Field(default_factory=list)
    mail_provider: str | None = None
    confidence: float = Field(ge=0.0, le=100.0, default=0.0)


class LicensedProviderResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: EnrichmentSourceType
    enabled: bool
    technologies: list[TechnologyEntry] = Field(default_factory=list)
    profile_fields: dict[str, Any] = Field(default_factory=dict)
    people: list[PersonEntry] = Field(default_factory=list)
    notes: str = ""
