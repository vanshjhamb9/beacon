from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


SCORING_VERSION = "goap-v1"


class ConnectorAccessMode(StrEnum):
    PUBLIC_FEED = "public_feed"
    PUBLIC_JOBS = "public_jobs"
    LICENSED = "licensed"
    CREDENTIALS_REQUIRED = "credentials_required"
    INTERFACE_ONLY = "interface_only"


class ConnectorStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DEGRADED = "degraded"
    PENDING_CREDENTIALS = "pending_credentials"
    INTERFACE_ONLY = "interface_only"


class OpportunityIntent(StrEnum):
    HIRING = "hiring"
    FUNDING = "funding"
    EXPANSION = "expansion"
    AI_ADOPTION = "ai_adoption"
    DIGITAL_TRANSFORMATION = "digital_transformation"
    WEBSITE_REBUILD = "website_rebuild"
    CRM_MIGRATION = "crm_migration"
    ERP_MIGRATION = "erp_migration"
    CLOUD_MIGRATION = "cloud_migration"
    AUTOMATION = "automation"
    CUSTOMER_SUPPORT_SCALING = "customer_support_scaling"
    MARKETING_SCALING = "marketing_scaling"
    STARTUP_LAUNCH = "startup_launch"
    ACQUISITION = "acquisition"
    IPO = "ipo"
    PRODUCT_LAUNCH = "product_launch"
    TECHNOLOGY_MIGRATION = "technology_migration"
    INFRASTRUCTURE_UPGRADES = "infrastructure_upgrades"
    INTERNATIONAL_EXPANSION = "international_expansion"
    COMPLIANCE_CHANGES = "compliance_changes"
    SECURITY_INVESTMENT = "security_investment"
    PLATFORM_MODERNIZATION = "platform_modernization"


class GraphNodeType(StrEnum):
    COMPANY = "company"
    INDUSTRY = "industry"
    FUNDING = "funding"
    HIRING = "hiring"
    TECHNOLOGY = "technology"
    DECISION_MAKER = "decision_maker"
    WEBSITE = "website"
    BUYING_SIGNAL = "buying_signal"
    PAIN_POINT = "pain_point"
    COMPETITOR = "competitor"
    CAMPAIGN = "campaign"
    MEETING = "meeting"
    REVENUE = "revenue"
    HISTORY = "history"
    OUTCOME = "outcome"


class BenchmarkAction(StrEnum):
    INCREASE_FREQUENCY = "increase_frequency"
    REDUCE_FREQUENCY = "reduce_frequency"
    DISABLE_CONNECTOR = "disable_connector"
    MAINTAIN = "maintain"


class ConnectorDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    connector_id: str
    connector_name: str
    access_mode: ConnectorAccessMode
    status: ConnectorStatus = ConnectorStatus.ACTIVE
    category: str = "general"
    respects_robots_txt: bool = True
    public_information_only: bool = True
    requires_license: bool = False
    notes: str = ""


class ConnectorMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    connector_id: str
    connector_name: str
    health: str = "healthy"
    availability: float = Field(ge=0.0, le=100.0, default=100.0)
    last_run: datetime | None = None
    signals_found: int = 0
    companies_found: int = 0
    opportunities_found: int = 0
    duplicates: int = 0
    latency_ms: float = 0.0
    errors: int = 0
    quality_score: float = Field(ge=0.0, le=100.0, default=0.0)
    trust_score: float = Field(ge=0.0, le=100.0, default=0.0)
    coverage_score: float = Field(ge=0.0, le=100.0, default=0.0)
    freshness_score: float = Field(ge=0.0, le=100.0, default=0.0)
    roi_score: float = Field(ge=0.0, le=100.0, default=0.0)
    evidence: list[str] = Field(default_factory=list)


class RawSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    connector_id: str
    company_name: str
    company_domain: str | None = None
    title: str = ""
    body: str = ""
    url: str | None = None
    published_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedCompanySignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    canonical_key: str
    company_name: str
    company_domain: str | None = None
    source_connector_ids: list[str] = Field(default_factory=list)
    titles: list[str] = Field(default_factory=list)
    bodies: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class DetectedIntent(BaseModel):
    model_config = ConfigDict(frozen=True)

    intent: OpportunityIntent
    confidence: float = Field(ge=0.0, le=100.0)
    evidence: list[str] = Field(default_factory=list)


class TechnologyHit(BaseModel):
    model_config = ConfigDict(frozen=True)

    technology: str
    category: str
    confidence: float = Field(ge=0.0, le=100.0)
    evidence: list[str] = Field(default_factory=list)


class WebsiteProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_name: str
    domain: str | None = None
    cms: str | None = None
    framework: str | None = None
    hosting: str | None = None
    cloud: str | None = None
    ssl: bool = False
    mobile_responsive: bool = False
    performance_score: float = 0.0
    accessibility_score: float = 0.0
    seo_score: float = 0.0
    has_analytics: bool = False
    has_chatbot: bool = False
    has_ai_widget: bool = False
    has_booking: bool = False
    has_forms: bool = False
    crm: str | None = None
    email_platform: str | None = None
    marketing_automation: str | None = None
    support_software: str | None = None
    knowledge_base: bool = False
    payment_provider: str | None = None
    stack: list[str] = Field(default_factory=list)
    website_age_years: float | None = None
    broken_links_estimate: int = 0
    security_headers_score: float = 0.0
    structured_data: bool = False
    performance_issues: list[str] = Field(default_factory=list)
    modernization_score: float = Field(ge=0.0, le=100.0, default=0.0)
    opportunity_score: float = Field(ge=0.0, le=100.0, default=0.0)
    evidence: list[str] = Field(default_factory=list)


class HiringInsight(BaseModel):
    model_config = ConfigDict(frozen=True)

    growth: float = 0.0
    engineering_expansion: float = 0.0
    ai_investment: float = 0.0
    product_investment: float = 0.0
    sales_expansion: float = 0.0
    support_expansion: float = 0.0
    marketing_expansion: float = 0.0
    roles: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class FundingEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    round: str
    amount_hint: str | None = None
    confidence: float = Field(ge=0.0, le=100.0, default=0.0)
    evidence: list[str] = Field(default_factory=list)


class ReviewSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    complaints: list[str] = Field(default_factory=list)
    missing_features: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    competitor_mentions: list[str] = Field(default_factory=list)
    migration_opportunities: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class CommunitySignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    needs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=100.0, default=0.0)
    evidence: list[str] = Field(default_factory=list)


class ProcurementSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    tender_type: str
    summary: str
    confidence: float = Field(ge=0.0, le=100.0, default=0.0)
    evidence: list[str] = Field(default_factory=list)


class GraphNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    node_id: str
    node_type: GraphNodeType
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


class OpportunityGraph(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_key: str
    company_name: str
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class FreshnessScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: float = Field(ge=0.0, le=100.0)
    factors: dict[str, float] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class ConnectorBenchmark(BaseModel):
    model_config = ConfigDict(frozen=True)

    connector_id: str
    connector_name: str
    qualified_opportunities: int = 0
    meetings_booked: int = 0
    reply_rate: float = 0.0
    proposal_rate: float = 0.0
    close_rate: float = 0.0
    revenue_generated: float = 0.0
    average_quality: float = 0.0
    false_positives: int = 0
    latency_ms: float = 0.0
    coverage: float = 0.0
    rank: int = 0
    recommendation: BenchmarkAction = BenchmarkAction.MAINTAIN
    evidence: list[str] = Field(default_factory=list)


class GOAPAnalytics(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_connectors: int = 0
    active_connectors: int = 0
    pending_credentials: int = 0
    total_signals: int = 0
    unique_companies: int = 0
    intents_detected: dict[str, int] = Field(default_factory=dict)
    top_sources: list[str] = Field(default_factory=list)
    average_freshness: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class DailyGOAPReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    generated_at: datetime
    summary: str
    analytics: GOAPAnalytics
    top_benchmarks: list[ConnectorBenchmark] = Field(default_factory=list)
    alerts: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class CompanyObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID | None = None
    company_name: str
    company_domain: str | None = None
    industry: str | None = None
    source_texts: list[str] = Field(default_factory=list)
    source_connector_ids: list[str] = Field(default_factory=list)
    html_hints: list[str] = Field(default_factory=list)
    job_titles: list[str] = Field(default_factory=list)
    funding_text: list[str] = Field(default_factory=list)
    review_text: list[str] = Field(default_factory=list)
    community_text: list[str] = Field(default_factory=list)
    procurement_text: list[str] = Field(default_factory=list)
    decision_makers: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    campaigns: list[str] = Field(default_factory=list)
    meetings: list[str] = Field(default_factory=list)
    revenue_notes: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)
    history: list[str] = Field(default_factory=list)
    verified: bool = False
    last_seen_hours: float = 24.0
    engagement_score: float = 50.0
    activity_score: float = 50.0
    now: datetime | None = None


class GOAPInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    raw_signals: list[RawSignal] = Field(default_factory=list)
    companies: list[CompanyObservation] = Field(default_factory=list)
    connector_outcomes: dict[str, dict[str, Any]] = Field(default_factory=dict)
    now: datetime | None = None


class CompanyIntelligencePack(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_name: str
    company_domain: str | None = None
    canonical_key: str
    intents: list[DetectedIntent] = Field(default_factory=list)
    technologies: list[TechnologyHit] = Field(default_factory=list)
    website: WebsiteProfile | None = None
    hiring: HiringInsight | None = None
    funding: list[FundingEvent] = Field(default_factory=list)
    reviews: ReviewSignal | None = None
    community: CommunitySignal | None = None
    procurement: list[ProcurementSignal] = Field(default_factory=list)
    graph: OpportunityGraph | None = None
    freshness: FreshnessScore | None = None
    evidence: list[str] = Field(default_factory=list)


class GOAPDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    scoring_version: str = SCORING_VERSION
    connectors: list[ConnectorMetrics] = Field(default_factory=list)
    normalized: list[NormalizedCompanySignal] = Field(default_factory=list)
    companies: list[CompanyIntelligencePack] = Field(default_factory=list)
    benchmarks: list[ConnectorBenchmark] = Field(default_factory=list)
    analytics: GOAPAnalytics
    daily_report: DailyGOAPReport | None = None
    evidence_chain: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
