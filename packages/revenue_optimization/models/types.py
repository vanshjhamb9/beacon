from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


SCORING_VERSION = "roip-v1"


class ReplyCategory(StrEnum):
    INTERESTED = "interested"
    NEED_MORE_INFO = "need_more_info"
    BUDGET_ISSUE = "budget_issue"
    TIMING_ISSUE = "timing_issue"
    ALREADY_USING_SOLUTION = "already_using_solution"
    COMPETITOR = "competitor"
    INTERNAL_DISCUSSION = "internal_discussion"
    NO_RESPONSE = "no_response"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MEETING_REQUESTED = "meeting_requested"
    DECISION_PENDING = "decision_pending"


class CTAType(StrEnum):
    BOOK_MEETING = "book_meeting"
    FREE_CONSULTATION = "free_consultation"
    AI_AUDIT = "ai_audit"
    REPLY_BACK = "reply_back"
    QUICK_QUESTION = "quick_question"
    DISCOVERY_15_MIN = "15_min_discovery"
    DOWNLOAD_GUIDE = "download_guide"
    WATCH_DEMO = "watch_demo"


class OfferType(StrEnum):
    WEBSITE_DEVELOPMENT = "Website Development"
    MOBILE_APPS = "Mobile Apps"
    CUSTOM_SAAS = "Custom SaaS"
    AI_AUTOMATION = "AI Automation"
    AI_CHATBOTS = "AI Chatbots"
    INTERNAL_AI = "Internal AI"
    CRM = "CRM"
    ERP = "ERP"
    WORKFLOW_AUTOMATION = "Workflow Automation"
    DATA_PLATFORM = "Data Platform"
    DASHBOARDS = "Dashboards"
    INTEGRATIONS = "Integrations"


class Period(StrEnum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class OutreachEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str
    company_id: UUID | None = None
    company_name: str = ""
    campaign_id: str | None = None
    industry: str | None = None
    company_size_band: str | None = None
    channel: str = "email"
    subject: str | None = None
    cta: str | None = None
    offer: str | None = None
    sent_at: datetime | None = None
    delivered: bool = False
    opened: bool = False
    open_count: int = 0
    open_hour: int | None = None
    open_weekday: int | None = None
    open_device: str | None = None
    open_country: str | None = None
    attachment_downloads: int = 0
    video_views: int = 0
    calendly_clicks: int = 0
    website_visits: int = 0
    replied: bool = False
    reply_hours: float | None = None
    reply_text: str = ""
    bounced: bool = False
    spam: bool = False
    unsubscribed: bool = False
    meeting_booked: bool = False
    meeting_completed: bool = False
    proposal_sent: bool = False
    closed_won: bool = False
    closed_lost: bool = False
    deal_value: float = 0.0
    followup_number: int = 0
    sequence_length: int = 1
    delay_days: float | None = None
    timezone: str | None = None
    founder_actor: bool = True
    pain_points: list[str] = Field(default_factory=list)
    technology: list[str] = Field(default_factory=list)
    buyer_persona: str | None = None
    evidence: list[str] = Field(default_factory=list)


class EmailMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    delivered: int = 0
    opened: int = 0
    multiple_opens: int = 0
    open_times: list[int] = Field(default_factory=list)
    open_devices: dict[str, int] = Field(default_factory=dict)
    open_countries: dict[str, int] = Field(default_factory=dict)
    attachment_downloads: int = 0
    video_views: int = 0
    calendly_clicks: int = 0
    website_visits: int = 0
    reply_times_hours: list[float] = Field(default_factory=list)
    bounce: int = 0
    spam: int = 0
    unsubscribe: int = 0
    open_rate: float = 0.0
    reply_rate: float = 0.0
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)


class SubjectPerformance(BaseModel):
    model_config = ConfigDict(frozen=True)

    subject: str
    sends: int = 0
    open_rate: float = 0.0
    reply_rate: float = 0.0
    meeting_rate: float = 0.0
    proposal_rate: float = 0.0
    close_rate: float = 0.0
    revenue_generated: float = 0.0
    rank: int = 0
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class CTAPerformance(BaseModel):
    model_config = ConfigDict(frozen=True)

    cta: str
    sends: int = 0
    ctr: float = 0.0
    replies: int = 0
    meetings: int = 0
    deals: int = 0
    revenue: float = 0.0
    score: float = 0.0
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class FollowupPattern(BaseModel):
    model_config = ConfigDict(frozen=True)

    best_day: int | None = None
    best_hour: int | None = None
    best_timezone: str | None = None
    best_delay_days: float | None = None
    best_followup_count: int | None = None
    best_sequence_length: int | None = None
    industry_timing: dict[str, dict[str, Any]] = Field(default_factory=dict)
    company_size_timing: dict[str, dict[str, Any]] = Field(default_factory=dict)
    founder_timing: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class IndustryMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    industry: str
    open_rate: float = 0.0
    reply_rate: float = 0.0
    meeting_rate: float = 0.0
    proposal_rate: float = 0.0
    close_rate: float = 0.0
    average_deal_size: float = 0.0
    sales_cycle_days: float = 0.0
    revenue: float = 0.0
    rank: int = 0
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class FounderMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    companies_contacted: int = 0
    emails_sent: int = 0
    whatsapp_messages: int = 0
    meetings_booked: int = 0
    meetings_completed: int = 0
    proposals_sent: int = 0
    deals_closed: int = 0
    revenue: float = 0.0
    followup_speed_hours: float = 0.0
    average_response_time_hours: float = 0.0
    pipeline_health: float = 0.0
    weekly_trend: float = 0.0
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class OfferMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    offer: str
    interest: int = 0
    meetings: int = 0
    wins: int = 0
    revenue: float = 0.0
    score: float = 0.0
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class CaseStudyRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    asset_type: str
    asset_id: str
    title: str
    reason: str
    industry: str | None = None
    company_size: str | None = None
    score: float = 0.0
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class ReplyAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    reply_id: str
    category: ReplyCategory
    urgency: float = 0.0
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class LearningInsight(BaseModel):
    model_config = ConfigDict(frozen=True)

    insight_type: str
    summary: str
    why_won: list[str] = Field(default_factory=list)
    why_lost: list[str] = Field(default_factory=list)
    common_objections: list[str] = Field(default_factory=list)
    winning_patterns: list[str] = Field(default_factory=list)
    best_channels: list[str] = Field(default_factory=list)
    best_industries: list[str] = Field(default_factory=list)
    best_timing: list[str] = Field(default_factory=list)
    best_offers: list[str] = Field(default_factory=list)
    modifies_production: bool = False
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class RevenueBenchmark(BaseModel):
    model_config = ConfigDict(frozen=True)

    period: Period
    open_rate: float = 0.0
    reply_rate: float = 0.0
    meeting_rate: float = 0.0
    proposal_rate: float = 0.0
    win_rate: float = 0.0
    revenue: float = 0.0
    average_deal_size: float = 0.0
    sales_cycle_days: float = 0.0
    previous_open_rate: float = 0.0
    growth: float = 0.0
    decline: float = 0.0
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class OptimizationRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    recommendation_id: str
    title: str
    action: str
    segment: str
    confidence: float = 0.0
    requires_founder_approval: bool = True
    modifies_production: bool = False
    evidence: list[str] = Field(default_factory=list)


class ROIPInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    events: list[OutreachEvent] = Field(default_factory=list)
    previous_period_events: list[OutreachEvent] = Field(default_factory=list)
    portfolio_assets: list[dict[str, Any]] = Field(default_factory=list)
    company_id: UUID | None = None
    campaign_id: str | None = None
    now: datetime | None = None


class ROIPDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    scoring_version: str = SCORING_VERSION
    email_metrics: EmailMetrics
    subjects: list[SubjectPerformance] = Field(default_factory=list)
    ctas: list[CTAPerformance] = Field(default_factory=list)
    followup: FollowupPattern
    industries: list[IndustryMetrics] = Field(default_factory=list)
    founder: FounderMetrics
    offers: list[OfferMetrics] = Field(default_factory=list)
    case_studies: list[CaseStudyRecommendation] = Field(default_factory=list)
    replies: list[ReplyAnalysis] = Field(default_factory=list)
    learning: LearningInsight
    benchmarks: list[RevenueBenchmark] = Field(default_factory=list)
    recommendations: list[OptimizationRecommendation] = Field(default_factory=list)
    evidence_chain: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
