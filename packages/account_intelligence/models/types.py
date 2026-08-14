from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


SCORING_VERSION = "aip-v1"

LICENSED_PROVIDERS_DISABLED = (
    "apollo",
    "people_data_labs",
    "zoominfo",
    "clearbit",
    "crunchbase",
)


class SalesReadinessCategory(StrEnum):
    COLD = "cold"
    WARM = "warm"
    QUALIFIED = "qualified"
    SALES_READY = "sales_ready"
    FOUNDER_READY = "founder_ready"


class CommitteeRole(StrEnum):
    FOUNDER = "Founder"
    CEO = "CEO"
    CTO = "CTO"
    COO = "COO"
    CIO = "CIO"
    VP_ENGINEERING = "VP Engineering"
    ENGINEERING_MANAGER = "Engineering Manager"
    HEAD_OF_AI = "Head of AI"
    PRODUCT_MANAGER = "Product Manager"
    HEAD_OF_OPERATIONS = "Head of Operations"
    MARKETING_HEAD = "Marketing Head"
    SALES_HEAD = "Sales Head"
    CUSTOMER_SUCCESS = "Customer Success"
    SUPPORT_HEAD = "Support Head"
    FINANCE_HEAD = "Finance Head"
    HR_HEAD = "HR Head"
    LEGAL = "Legal"
    IT_MANAGER = "IT Manager"


class FieldValue(BaseModel):
    """Every enrichment field carries confidence, source, and verification metadata."""

    model_config = ConfigDict(frozen=True)

    value: Any = None
    confidence: float = Field(ge=0.0, le=100.0, default=0.0)
    source: str = "unknown"
    last_verified: datetime | None = None
    evidence: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)


class ObservedContact(BaseModel):
    """Publicly observed contact input — never invent missing PII."""

    model_config = ConfigDict(frozen=True)

    full_name: str
    role: str | None = None
    department: str | None = None
    business_email: str | None = None
    business_phone: str | None = None
    linkedin_url: str | None = None
    company_profile_url: str | None = None
    source: str
    observed_at: datetime | None = None
    evidence: list[str] = Field(default_factory=list)


class AccountIntelligenceInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID | None = None
    company_name: str
    website: str | None = None
    domain: str | None = None
    legal_name: str | None = None
    industry: str | None = None
    sub_industry: str | None = None
    business_model: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    founded: str | None = None
    employee_count: int | None = None
    revenue_estimate: float | None = None
    funding: str | None = None
    latest_funding_round: str | None = None
    investors: list[str] = Field(default_factory=list)
    offices: list[str] = Field(default_factory=list)
    locations: list[dict[str, Any]] = Field(default_factory=list)
    time_zone: str | None = None
    languages: list[str] = Field(default_factory=list)
    parent_company: str | None = None
    subsidiaries: list[str] = Field(default_factory=list)
    is_public: bool | None = None
    ipo_status: str | None = None
    annual_growth: float | None = None
    hiring_trend: float | None = None
    expansion_score: float | None = None
    html_hints: list[str] = Field(default_factory=list)
    tech_hints: list[str] = Field(default_factory=list)
    observed_contacts: list[ObservedContact] = Field(default_factory=list)
    campaigns: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    replies: list[str] = Field(default_factory=list)
    meetings: list[str] = Field(default_factory=list)
    proposals: list[str] = Field(default_factory=list)
    revenue_notes: list[str] = Field(default_factory=list)
    referrals: list[str] = Field(default_factory=list)
    history: list[str] = Field(default_factory=list)
    buying_intent: float = 50.0
    source_attribution: str = "goap"
    field_sources: dict[str, str] = Field(default_factory=dict)
    now: datetime | None = None


class CompanyLocation(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    country: str | None = None
    state: str | None = None
    city: str | None = None
    is_hq: bool = False
    confidence: float = 0.0
    source: str = "unknown"
    last_verified: datetime | None = None
    evidence: list[str] = Field(default_factory=list)


class MasterAccountProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_name: FieldValue
    website: FieldValue
    legal_name: FieldValue
    industry: FieldValue
    sub_industry: FieldValue
    business_model: FieldValue
    country: FieldValue
    state: FieldValue
    city: FieldValue
    founded: FieldValue
    employee_count: FieldValue
    revenue_estimate: FieldValue
    funding: FieldValue
    latest_funding_round: FieldValue
    investors: FieldValue
    offices: FieldValue
    locations: list[CompanyLocation] = Field(default_factory=list)
    time_zone: FieldValue
    languages: FieldValue
    parent_company: FieldValue
    subsidiaries: FieldValue
    public_company_status: FieldValue
    ipo_status: FieldValue
    annual_growth: FieldValue
    hiring_trend: FieldValue
    expansion_score: FieldValue
    overall_confidence: float = 0.0
    source: str = "aip"
    last_verified: datetime | None = None
    evidence: list[str] = Field(default_factory=list)


class CommitteeMember(BaseModel):
    model_config = ConfigDict(frozen=True)

    full_name: str
    role: str
    department: str | None = None
    business_email: str | None = None
    business_phone: str | None = None
    linkedin_url: str | None = None
    company_profile_url: str | None = None
    confidence: float = 0.0
    verification: str = "unverified"
    source: str
    last_verified: datetime | None = None
    priority: int = 50
    influence_score: float = 0.0
    decision_authority: float = 0.0
    evidence: list[str] = Field(default_factory=list)
    fabricated: bool = False


class ContactValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    full_name: str
    business_email: str | None = None
    domain_match: bool = False
    mx_check: str = "interface_optional"
    role_valid: bool = False
    public_presence: bool = False
    business_phone: str | None = None
    country_code: str | None = None
    verification: str = "unverified"
    freshness: float = 0.0
    conflicts: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    source: str
    last_verified: datetime | None = None
    evidence: list[str] = Field(default_factory=list)
    accepted: bool = False


class TechnologyProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    frontend: list[str] = Field(default_factory=list)
    backend: list[str] = Field(default_factory=list)
    database: list[str] = Field(default_factory=list)
    cloud: list[str] = Field(default_factory=list)
    hosting: list[str] = Field(default_factory=list)
    cdn: list[str] = Field(default_factory=list)
    crm: list[str] = Field(default_factory=list)
    erp: list[str] = Field(default_factory=list)
    analytics: list[str] = Field(default_factory=list)
    marketing_automation: list[str] = Field(default_factory=list)
    payment_gateway: list[str] = Field(default_factory=list)
    customer_support: list[str] = Field(default_factory=list)
    ai_stack: list[str] = Field(default_factory=list)
    llm_stack: list[str] = Field(default_factory=list)
    security_stack: list[str] = Field(default_factory=list)
    devops: list[str] = Field(default_factory=list)
    monitoring: list[str] = Field(default_factory=list)
    cicd: list[str] = Field(default_factory=list)
    search: list[str] = Field(default_factory=list)
    caching: list[str] = Field(default_factory=list)
    storage: list[str] = Field(default_factory=list)
    cms: list[str] = Field(default_factory=list)
    framework: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    source: str = "public_hints"
    last_verified: datetime | None = None
    evidence: list[str] = Field(default_factory=list)


class WebsiteEnrichment(BaseModel):
    model_config = ConfigDict(frozen=True)

    seo_score: float = 0.0
    accessibility_score: float = 0.0
    core_web_vitals: float = 0.0
    performance_score: float = 0.0
    ssl: bool = False
    schema_markup: bool = False
    security_headers_score: float = 0.0
    mobile: bool = False
    forms: bool = False
    booking: bool = False
    contact_page: bool = False
    pricing: bool = False
    blog: bool = False
    resources: bool = False
    case_studies: bool = False
    testimonials: bool = False
    careers: bool = False
    knowledge_base: bool = False
    support_portal: bool = False
    ai_widgets: bool = False
    chatbot: bool = False
    automation: bool = False
    confidence: float = 0.0
    source: str = "public_hints"
    last_verified: datetime | None = None
    evidence: list[str] = Field(default_factory=list)


class BusinessProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    growth_stage: str = "unknown"
    digital_maturity: float = 0.0
    automation_level: float = 0.0
    ai_adoption: float = 0.0
    software_maturity: float = 0.0
    customer_segment: str = "unknown"
    market_position: str = "unknown"
    competitive_position: str = "unknown"
    buying_intent: float = 0.0
    business_risks: list[str] = Field(default_factory=list)
    growth_opportunities: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    source: str = "inferred"
    last_verified: datetime | None = None
    evidence: list[str] = Field(default_factory=list)


class AIReadinessReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    need_ai_automation: float = 0.0
    need_crm: float = 0.0
    need_erp: float = 0.0
    need_saas: float = 0.0
    need_website: float = 0.0
    need_mobile_app: float = 0.0
    need_custom_software: float = 0.0
    need_chatbot: float = 0.0
    need_internal_ai: float = 0.0
    need_analytics: float = 0.0
    need_knowledge_base: float = 0.0
    need_workflow_automation: float = 0.0
    need_integrations: float = 0.0
    overall: float = 0.0
    confidence: float = 0.0
    source: str = "aip"
    last_verified: datetime | None = None
    evidence: list[str] = Field(default_factory=list)


class SalesReadinessReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    opportunity: float = 0.0
    budget: float = 0.0
    authority: float = 0.0
    need: float = 0.0
    timing: float = 0.0
    data_completeness: float = 0.0
    decision_makers: float = 0.0
    contact_availability: float = 0.0
    technology: float = 0.0
    growth: float = 0.0
    urgency: float = 0.0
    confidence: float = 0.0
    score: float = 0.0
    category: SalesReadinessCategory = SalesReadinessCategory.COLD
    source: str = "aip"
    last_verified: datetime | None = None
    evidence: list[str] = Field(default_factory=list)


class GraphNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    node_id: str
    node_type: str
    label: str
    payload: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class GraphEdge(BaseModel):
    model_config = ConfigDict(frozen=True)

    edge_id: str
    source_id: str
    target_id: str
    relation: str
    evidence: list[str] = Field(default_factory=list)


class RelationshipGraph(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_key: str
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ConfidenceReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    field_scores: dict[str, float] = Field(default_factory=dict)
    overall: float = 0.0
    conflicts: list[str] = Field(default_factory=list)
    sources: dict[str, str] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class VerificationRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    field: str
    status: str
    source: str
    confidence: float = 0.0
    last_verified: datetime | None = None
    evidence: list[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_type: str
    title: str
    timestamp: datetime
    evidence: list[str] = Field(default_factory=list)


class FinancialProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    revenue_estimate: FieldValue
    funding: FieldValue
    latest_funding_round: FieldValue
    investors: FieldValue
    evidence: list[str] = Field(default_factory=list)


class GrowthProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    annual_growth: FieldValue
    hiring_trend: FieldValue
    expansion_score: FieldValue
    evidence: list[str] = Field(default_factory=list)


class IndustryBenchmark(BaseModel):
    model_config = ConfigDict(frozen=True)

    industry: str
    avg_employee_band: str = "unknown"
    avg_digital_maturity: float = 50.0
    avg_ai_adoption: float = 40.0
    evidence: list[str] = Field(default_factory=list)


class AccountIntelligenceDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID | None = None
    company_name: str
    profile: MasterAccountProfile
    departments: list[str] = Field(default_factory=list)
    locations: list[CompanyLocation] = Field(default_factory=list)
    buying_committee: list[CommitteeMember] = Field(default_factory=list)
    verified_contacts: list[ContactValidationResult] = Field(default_factory=list)
    technology: TechnologyProfile
    website: WebsiteEnrichment
    financial: FinancialProfile
    business: BusinessProfile
    growth: GrowthProfile
    ai_readiness: AIReadinessReport
    sales_readiness: SalesReadinessReport
    relationship_graph: RelationshipGraph
    confidence: ConfidenceReport
    verification_history: list[VerificationRecord] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    industry_benchmark: IndustryBenchmark | None = None
    licensed_providers_disabled: list[str] = Field(default_factory=lambda: list(LICENSED_PROVIDERS_DISABLED))
    scoring_version: str = SCORING_VERSION
    evidence_chain: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
