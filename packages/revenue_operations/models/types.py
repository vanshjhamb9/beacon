from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


SCORING_VERSION = "roc-v1"


class AlertLifecycle(StrEnum):
    NEW = "new"
    VIEWED = "viewed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ARCHIVED = "archived"


class AlertKind(StrEnum):
    HIGH_INTENT_REPLY = "high_intent_reply"
    MEETING_BOOKED = "meeting_booked"
    CAMPAIGN_STOPPED = "campaign_stopped"
    REPLY_OVERDUE = "reply_overdue"
    LEAD_QUALITY_DROPPED = "lead_quality_dropped"
    DECISION_MAKER_CHANGED = "decision_maker_changed"
    FUNDING_DETECTED = "funding_detected"
    LARGE_HIRING_DETECTED = "large_hiring_detected"
    REVENUE_OPPORTUNITY_INCREASED = "revenue_opportunity_increased"
    PROPOSAL_OVERDUE = "proposal_overdue"
    LOST_DEAL_RISK = "lost_deal_risk"


class RadarSignalKind(StrEnum):
    FUNDING = "funding"
    HIRING = "hiring"
    TECHNOLOGY_CHANGE = "technology_change"
    PRODUCT_LAUNCH = "product_launch"
    AI_ADOPTION = "ai_adoption"
    CLOUD_MIGRATION = "cloud_migration"
    DIGITAL_TRANSFORMATION = "digital_transformation"
    NEW_OFFICE = "new_office"
    EXPANSION = "expansion"
    LEADERSHIP_CHANGE = "leadership_change"
    DECISION_MAKER_CHANGE = "decision_maker_change"
    WEBSITE_REDESIGN = "website_redesign"
    HIRING_AI_ENGINEERS = "hiring_ai_engineers"
    HIRING_SOFTWARE_DEVELOPERS = "hiring_software_developers"
    HIRING_PRODUCT_MANAGERS = "hiring_product_managers"
    HIRING_AUTOMATION_ENGINEERS = "hiring_automation_engineers"
    TECH_STACK_CHANGE = "tech_stack_change"


class AgentRole(StrEnum):
    RESEARCH = "research"
    QUALIFICATION = "qualification"
    ENRICHMENT = "enrichment"
    DECISION_MAKER = "decision_maker"
    REVENUE = "revenue"
    SALES = "sales"
    CAMPAIGN = "campaign"
    COMMUNICATION = "communication"
    FOUNDER = "founder"


class RecommendationStatus(StrEnum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ControlTowerMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    revenue_today: float = 0.0
    pipeline_value: float = 0.0
    meetings_today: int = 0
    replies_waiting: int = 0
    campaigns_running: int = 0
    deals_at_risk: int = 0
    proposals_pending: int = 0
    negotiations: int = 0
    expected_revenue: float = 0.0
    revenue_forecast: float = 0.0
    conversion_funnel: dict[str, float] = Field(default_factory=dict)
    top_industries: list[str] = Field(default_factory=list)
    top_services: list[str] = Field(default_factory=list)
    top_campaign: str | None = None
    top_lead_source: str | None = None
    weekly_trend: list[dict[str, Any]] = Field(default_factory=list)
    monthly_trend: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class RadarSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: RadarSignalKind
    company_id: UUID | None = None
    company_name: str
    detail: str
    intensity: float = Field(ge=0.0, le=100.0, default=50.0)
    hunter_score_delta: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class RevenueAlert(BaseModel):
    model_config = ConfigDict(frozen=True)

    alert_id: str
    kind: AlertKind
    title: str
    severity: str = "medium"
    company_id: UUID | None = None
    company_name: str | None = None
    recommendation: str
    lifecycle: AlertLifecycle = AlertLifecycle.NEW
    evidence: list[str] = Field(default_factory=list)
    dedupe_key: str


class AgentMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    from_agent: AgentRole
    to_agent: AgentRole | None = None
    topic: str
    payload: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class AgentRunResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    agent: AgentRole
    status: str = "ok"
    outputs: dict[str, Any] = Field(default_factory=dict)
    messages: list[AgentMessage] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class MemoryRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    record_type: str
    company_id: UUID | None = None
    company_name: str | None = None
    title: str
    body: str = ""
    tags: list[str] = Field(default_factory=list)
    searchable_text: str = ""
    evidence: list[str] = Field(default_factory=list)


class WinLossRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    outcome: str
    why: str
    industry: str | None = None
    budget: str | None = None
    timeline: str | None = None
    service_sold: str | None = None
    competitor: str | None = None
    decision_maker: str | None = None
    reply_speed_hours: float = 0.0
    meeting_count: int = 0
    proposal_count: int = 0
    sales_cycle_days: int = 0
    objections: list[str] = Field(default_factory=list)
    close_probability: float = 0.0
    company_name: str
    evidence: list[str] = Field(default_factory=list)


class ForecastHorizon(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    amount: float
    confidence: float = Field(ge=0.0, le=100.0)
    expected_meetings: int = 0
    expected_proposals: int = 0
    expected_closes: int = 0
    evidence: list[str] = Field(default_factory=list)


class RevenueForecastPack(BaseModel):
    model_config = ConfigDict(frozen=True)

    this_week: ForecastHorizon
    this_month: ForecastHorizon
    quarter: ForecastHorizon
    annual: ForecastHorizon
    pipeline_health: float = Field(ge=0.0, le=100.0)
    risk_analysis: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=100.0)
    evidence: list[str] = Field(default_factory=list)


class FounderAssistantBrief(BaseModel):
    model_config = ConfigDict(frozen=True)

    greeting: str
    executive_summary: str
    todays_mission: str
    top_priorities: list[str] = Field(default_factory=list)
    highest_probability_deals: list[dict[str, Any]] = Field(default_factory=list)
    deals_requiring_attention: list[dict[str, Any]] = Field(default_factory=list)
    replies: list[dict[str, Any]] = Field(default_factory=list)
    follow_ups: list[dict[str, Any]] = Field(default_factory=list)
    meetings: list[dict[str, Any]] = Field(default_factory=list)
    revenue_target: float = 0.0
    expected_revenue: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class ReplayEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    stage: str
    title: str
    detail: str = ""
    occurred_at: datetime | None = None
    evidence: list[str] = Field(default_factory=list)


class RevenueReplay(BaseModel):
    model_config = ConfigDict(frozen=True)

    opportunity_id: UUID | None = None
    company_id: UUID | None = None
    company_name: str
    events: list[ReplayEvent] = Field(default_factory=list)
    outcome: str | None = None
    evidence: list[str] = Field(default_factory=list)


class LearningRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    recommendation_id: str
    category: str
    title: str
    detail: str
    status: RecommendationStatus = RecommendationStatus.PENDING_APPROVAL
    evidence: list[str] = Field(default_factory=list)
    modifies_production: bool = False


class LearningLabReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    best_industries: list[str] = Field(default_factory=list)
    best_services: list[str] = Field(default_factory=list)
    best_email: str | None = None
    best_whatsapp: str | None = None
    best_meeting_time: str | None = None
    best_follow_up_interval_days: int = 2
    highest_converting_decision_makers: list[str] = Field(default_factory=list)
    highest_converting_company_sizes: list[str] = Field(default_factory=list)
    highest_converting_countries: list[str] = Field(default_factory=list)
    highest_converting_technologies: list[str] = Field(default_factory=list)
    recommendations: list[LearningRecommendation] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class CommandCenterView(BaseModel):
    model_config = ConfigDict(frozen=True)

    greeting: str
    revenue_score: float = Field(ge=0.0, le=100.0)
    todays_mission: str
    high_priority_queue: list[dict[str, Any]] = Field(default_factory=list)
    meetings: list[dict[str, Any]] = Field(default_factory=list)
    replies: list[dict[str, Any]] = Field(default_factory=list)
    campaign_health: dict[str, Any] = Field(default_factory=dict)
    pipeline: dict[str, Any] = Field(default_factory=dict)
    forecast: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class OperationalMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    discovery_rate: float = 0.0
    qualification_rate: float = 0.0
    enrichment_rate: float = 0.0
    decision_maker_success: float = 0.0
    reply_rate: float = 0.0
    meeting_rate: float = 0.0
    proposal_rate: float = 0.0
    close_rate: float = 0.0
    revenue: float = 0.0
    average_deal_size: float = 0.0
    sales_cycle_days: float = 0.0
    pipeline_velocity: float = 0.0
    customer_acquisition_cost: float = 0.0
    lifetime_value: float = 0.0
    roi: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class OpportunitySignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    opportunity_id: UUID | None = None
    company_id: UUID | None = None
    company_name: str
    industry: str | None = None
    service: str | None = None
    stage: str | None = None
    probability: float = 0.0
    pipeline_value: float = 0.0
    days_in_stage: int = 0
    reply_waiting: bool = False
    meeting_today: bool = False
    proposal_pending: bool = False
    negotiation: bool = False
    at_risk: bool = False
    won: bool = False
    lost: bool = False
    radar_hints: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    decision_makers: list[str] = Field(default_factory=list)
    lead_source: str | None = None
    campaign_name: str | None = None
    country: str | None = None
    company_size: str | None = None
    technologies: list[str] = Field(default_factory=list)
    meeting_count: int = 0
    proposal_count: int = 0
    reply_speed_hours: float = 0.0
    sales_cycle_days: int = 0
    why_won: str | None = None
    why_lost: str | None = None
    competitor: str | None = None
    budget: str | None = None
    timeline: str | None = None
    founder_notes: list[str] = Field(default_factory=list)


class RevenueOperationsInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    opportunities: list[OpportunitySignal] = Field(default_factory=list)
    campaigns_running: int = 0
    revenue_today: float = 0.0
    revenue_closed: float = 0.0
    revenue_target_week: float = 50000.0
    top_industries: list[str] = Field(default_factory=list)
    top_services: list[str] = Field(default_factory=list)
    top_campaign: str | None = None
    top_lead_source: str | None = None
    funnel_counts: dict[str, float] = Field(default_factory=dict)
    weekly_trend: list[dict[str, Any]] = Field(default_factory=list)
    monthly_trend: list[dict[str, Any]] = Field(default_factory=list)
    existing_alert_keys: list[str] = Field(default_factory=list)
    memory_seeds: list[dict[str, Any]] = Field(default_factory=list)
    learning_signals: dict[str, Any] = Field(default_factory=dict)
    agency_stats: dict[str, Any] = Field(default_factory=dict)
    founder_name: str = "Founder"
    now: datetime | None = None


class RevenueOperationsDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    control_tower: ControlTowerMetrics
    radar_signals: list[RadarSignal] = Field(default_factory=list)
    alerts: list[RevenueAlert] = Field(default_factory=list)
    agent_runs: list[AgentRunResult] = Field(default_factory=list)
    memory_records: list[MemoryRecord] = Field(default_factory=list)
    win_loss: list[WinLossRecord] = Field(default_factory=list)
    forecast: RevenueForecastPack
    founder_assistant: FounderAssistantBrief
    replays: list[RevenueReplay] = Field(default_factory=list)
    learning: LearningLabReport
    command_center: CommandCenterView
    operational_metrics: OperationalMetrics
    scoring_version: str = SCORING_VERSION
    evidence_chain: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
