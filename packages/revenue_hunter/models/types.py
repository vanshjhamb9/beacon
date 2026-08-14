from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


SCORING_VERSION = "rh-v1"


class PriorityGrade(StrEnum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class WorkQueueAction(StrEnum):
    APPROVE = "approve"
    SEND = "send"
    REPLY = "reply"
    BOOK_MEETING = "book_meeting"
    SKIP = "skip"
    DEFER = "defer"


class WorkQueueStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    SENT = "sent"
    REPLIED = "replied"
    MEETING_BOOKED = "meeting_booked"
    SKIPPED = "skipped"
    DEFERRED = "deferred"


class CompanySizeBand(StrEnum):
    S_10_25 = "10-25"
    S_25_50 = "25-50"
    S_50_100 = "50-100"
    S_100_250 = "100-250"
    S_250_500 = "250-500"
    S_500_PLUS = "500+"


class FundingStage(StrEnum):
    BOOTSTRAPPED = "Bootstrapped"
    SEED = "Seed"
    SERIES_A = "Series A"
    SERIES_B = "Series B"
    SERIES_C = "Series C"
    PUBLIC = "Public"


class RevenueBand(StrEnum):
    STARTUP = "Startup"
    SMB = "SMB"
    MID_MARKET = "Mid Market"
    ENTERPRISE = "Enterprise"


class BeaconService(StrEnum):
    COMAI = "COMAI"
    CUSTOM_AI = "Custom AI"
    WEBSITE = "Website"
    MOBILE_APP = "Mobile App"
    SAAS = "SaaS"
    INTERNAL_SOFTWARE = "Internal Software"
    AUTOMATION = "Automation"
    AI_CHATBOT = "AI Chatbot"
    CRM = "CRM"
    ERP = "ERP"
    MULTI_AGENT_SYSTEMS = "Multi Agent Systems"


class ScoreComponent(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    value: float = Field(ge=0.0, le=100.0)
    weight: float = Field(ge=0.0, le=1.0)
    explanation: str
    evidence: list[str] = Field(default_factory=list)


class FilterCriteria(BaseModel):
    model_config = ConfigDict(frozen=True)

    countries: list[str] = Field(default_factory=list)
    company_sizes: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    funding_stages: list[str] = Field(default_factory=list)
    revenue_bands: list[str] = Field(default_factory=list)


class FilterMatch(BaseModel):
    model_config = ConfigDict(frozen=True)

    passed: bool
    country_match: bool
    size_match: bool
    industry_match: bool
    funding_match: bool
    revenue_match: bool
    matched_country: str | None = None
    matched_size: str | None = None
    matched_industry: str | None = None
    matched_funding: str | None = None
    matched_revenue: str | None = None
    reasons: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ServiceMatchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    service: str
    confidence: float = Field(ge=0.0, le=100.0)
    reasoning: str
    evidence: list[str] = Field(default_factory=list)
    term_hits: int = 0
    pain_hits: int = 0
    industry_hit: bool = False


class PainPoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    problem: str
    confidence: float = Field(ge=0.0, le=100.0)
    evidence: list[str] = Field(default_factory=list)
    category: str = "operations"


class WebsiteOpportunity(BaseModel):
    model_config = ConfigDict(frozen=True)

    area: str
    recommendation: str
    severity: str
    evidence: list[str] = Field(default_factory=list)


class WebsiteIntelligence(BaseModel):
    model_config = ConfigDict(frozen=True)

    homepage_score: float = Field(ge=0.0, le=100.0)
    speed_score: float = Field(ge=0.0, le=100.0)
    seo_score: float = Field(ge=0.0, le=100.0)
    accessibility_score: float = Field(ge=0.0, le=100.0)
    lcp_ms: float | None = None
    cls: float | None = None
    inp_ms: float | None = None
    cms: str | None = None
    analytics: list[str] = Field(default_factory=list)
    pixels: list[str] = Field(default_factory=list)
    has_forms: bool = False
    has_chatbot: bool = False
    broken_pages: list[str] = Field(default_factory=list)
    technology_stack: list[str] = Field(default_factory=list)
    opportunities: list[WebsiteOpportunity] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class WhyNowV2(BaseModel):
    model_config = ConfigDict(frozen=True)

    why_this_company: str
    why_today: str
    why_us: str
    expected_budget: str
    expected_timeline: str
    probability: float = Field(ge=0.0, le=100.0)
    evidence_chain: list[str] = Field(default_factory=list)
    summary: str


class DecisionMakerContact(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    confidence: float = 0.0


class RevenueDossier(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    company_summary: str
    business: str
    products: list[str] = Field(default_factory=list)
    technology: list[str] = Field(default_factory=list)
    employees: int | None = None
    revenue: str | None = None
    funding: str | None = None
    hiring: list[str] = Field(default_factory=list)
    decision_makers: list[DecisionMakerContact] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    social: list[str] = Field(default_factory=list)
    pain_points: list[PainPoint] = Field(default_factory=list)
    buying_signals: list[str] = Field(default_factory=list)
    recommended_service: str
    service_confidence: float = 0.0
    expected_budget: str
    expected_timeline: str
    probability: float = 0.0
    proposal_strategy: str
    meeting_strategy: str
    objections: list[str] = Field(default_factory=list)
    portfolio_recommendation: str
    case_studies: list[str] = Field(default_factory=list)
    website: WebsiteIntelligence | None = None
    why_now: WhyNowV2 | None = None
    priority_grade: PriorityGrade
    revenue_score: float = Field(ge=0.0, le=100.0)
    proceed_to_campaign: bool = False
    score_breakdown: list[ScoreComponent] = Field(default_factory=list)
    evidence_chain: list[str] = Field(default_factory=list)
    scoring_version: str = SCORING_VERSION


class WorkQueueItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    dossier_id: UUID | None = None
    priority_grade: PriorityGrade
    recommended_service: str
    why_today: str
    expected_budget: str
    probability: float
    primary_contact: DecisionMakerContact | None = None
    status: WorkQueueStatus = WorkQueueStatus.PENDING
    allowed_actions: list[WorkQueueAction] = Field(
        default_factory=lambda: [
            WorkQueueAction.APPROVE,
            WorkQueueAction.SEND,
            WorkQueueAction.REPLY,
            WorkQueueAction.BOOK_MEETING,
        ]
    )
    rank: int = 0


class FounderDashboard(BaseModel):
    model_config = ConfigDict(frozen=True)

    todays_targets: list[WorkQueueItem] = Field(default_factory=list)
    top_25_companies: list[dict[str, Any]] = Field(default_factory=list)
    expected_revenue: float = 0.0
    expected_pipeline: float = 0.0
    meetings_today: int = 0
    campaign_queue: int = 0
    reply_queue: int = 0
    follow_ups: int = 0
    hot_opportunities: int = 0
    generated_at: datetime | None = None


class RevenueHunterInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    opportunity_id: UUID | None = None
    industry: str | None = None
    country: str | None = None
    domain: str | None = None
    website: str | None = None
    employee_count: int | None = None
    company_size_band: str | None = None
    revenue_band: str | None = None
    funding_stage: str | None = None
    funding_amount: float | None = None
    funding_days_ago: int | None = None
    technologies: list[str] = Field(default_factory=list)
    hiring_roles: list[str] = Field(default_factory=list)
    hiring_count: int = 0
    pains: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    business_model: str | None = None
    growth_signals: list[str] = Field(default_factory=list)
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    contacts: list[dict[str, Any]] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    social_profiles: list[str] = Field(default_factory=list)
    news: list[str] = Field(default_factory=list)
    website_metrics: dict[str, Any] = Field(default_factory=dict)
    opportunity_score: float = 0.0
    verification_score: float = 0.0
    enrichment: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RevenueHunterDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    opportunity_id: UUID | None = None
    filter_match: FilterMatch
    service_matches: list[ServiceMatchResult] = Field(default_factory=list)
    recommended_service: str
    service_confidence: float
    pain_points: list[PainPoint] = Field(default_factory=list)
    website: WebsiteIntelligence
    why_now: WhyNowV2
    dossier: RevenueDossier
    priority_grade: PriorityGrade
    revenue_score: float
    proceed_to_campaign: bool
    work_queue_eligible: bool
    score_breakdown: list[ScoreComponent] = Field(default_factory=list)
    evidence_chain: list[str] = Field(default_factory=list)
    scoring_version: str = SCORING_VERSION
    explanations: dict[str, str] = Field(default_factory=dict)
