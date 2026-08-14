from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


SCORING_VERSION = "fos-v1"


class TaskKind(StrEnum):
    APPROVE_CAMPAIGN = "approve_campaign"
    REVIEW_EMAIL = "review_email"
    REPLY_NEEDED = "reply_needed"
    MEETING_TODAY = "meeting_today"
    PROPOSAL_REQUIRED = "proposal_required"
    FOLLOW_UP_TODAY = "follow_up_today"
    LEAD_MISSING_CONTACT = "lead_missing_contact"
    WEBSITE_AUDIT_REQUIRED = "website_audit_required"
    VERIFICATION_FAILED = "verification_failed"


class TaskPriority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class TaskStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class TimelineStage(StrEnum):
    DISCOVERY = "discovery"
    COLLECTION = "collection"
    ENRICHMENT = "enrichment"
    VERIFICATION = "verification"
    DECISION_MAKERS = "decision_makers"
    CAMPAIGN = "campaign"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    REPLY = "reply"
    MEETING = "meeting"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class ProposalStatus(StrEnum):
    NEEDED = "needed"
    DRAFTING = "drafting"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class AnalyticsEventType(StrEnum):
    CLICK = "click"
    APPROVAL = "approval"
    CAMPAIGN = "campaign"
    REPLY = "reply"
    MEETING = "meeting"
    PROPOSAL = "proposal"
    OUTCOME = "outcome"
    TASK = "task"
    BRIEF_VIEW = "brief_view"
    ASSISTANT_QUERY = "assistant_query"


class DailyBriefSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    new_companies_found: int = 0
    new_buying_signals: int = 0
    qualified_companies: int = 0
    sales_ready_accounts: int = 0
    a_plus_opportunities: int = 0
    campaigns_waiting_approval: int = 0
    replies_waiting: int = 0
    meetings_today: int = 0
    proposals_pending: int = 0
    estimated_pipeline: float = 0.0
    expected_revenue: float = 0.0
    lost_opportunities: int = 0
    won_opportunities: int = 0
    top_performing_industry: str | None = None
    top_performing_service: str | None = None
    top_performing_outreach_style: str | None = None
    top_performing_subject_line: str | None = None
    top_performing_cta: str | None = None
    executive_summary: str = ""
    evidence: list[str] = Field(default_factory=list)
    generated_at: datetime | None = None


class ContactRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    why_them: str
    why_today: str
    what_to_sell: str
    expected_budget: str
    expected_close_probability: float
    next_action: str
    evidence: list[str] = Field(default_factory=list)
    priority_grade: str | None = None
    rank: int = 0


class FounderAssistantBrief(BaseModel):
    model_config = ConfigDict(frozen=True)

    greeting: str
    mission: str
    contacts: list[ContactRecommendation] = Field(default_factory=list)
    summary: str
    evidence: list[str] = Field(default_factory=list)


class RevenueTask(BaseModel):
    model_config = ConfigDict(frozen=True)

    task_id: str
    kind: TaskKind
    title: str
    priority: TaskPriority
    deadline: datetime | None = None
    owner: str = "founder"
    status: TaskStatus = TaskStatus.OPEN
    reason: str
    evidence: list[str] = Field(default_factory=list)
    company_id: UUID | None = None
    company_name: str | None = None
    related_id: str | None = None


class TimelineEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str
    company_id: UUID
    company_name: str
    stage: TimelineStage
    occurred_at: datetime
    summary: str
    evidence: list[str] = Field(default_factory=list)
    actor: str = "system"
    metadata: dict[str, Any] = Field(default_factory=dict)
    immutable: bool = True


class SalesKPISnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    reply_rate: float = 0.0
    meeting_rate: float = 0.0
    proposal_rate: float = 0.0
    close_rate: float = 0.0
    average_deal_size: float = 0.0
    sales_velocity_days: float = 0.0
    revenue_forecast: float = 0.0
    pipeline_health: float = 0.0
    campaign_performance: dict[str, float] = Field(default_factory=dict)
    service_performance: dict[str, float] = Field(default_factory=dict)
    country_performance: dict[str, float] = Field(default_factory=dict)
    industry_performance: dict[str, float] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class FounderRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    recommendation_id: str
    title: str
    action: str
    reason: str
    evidence: list[str] = Field(default_factory=list)
    impact_metric: str
    confidence: float = Field(ge=0.0, le=100.0)


class ProposalQueueItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    estimated_scope: str
    recommended_services: list[str] = Field(default_factory=list)
    estimated_timeline: str
    budget_range: str
    suggested_architecture: str
    case_studies: list[str] = Field(default_factory=list)
    proposal_status: ProposalStatus = ProposalStatus.NEEDED
    owner: str = "founder"
    deadline: datetime | None = None
    evidence: list[str] = Field(default_factory=list)


class MeetingIntelligencePack(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    scheduled_at: datetime | None = None
    company_summary: str
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    business_problems: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    buying_signals: list[str] = Field(default_factory=list)
    timeline_summary: str
    discovery_questions: list[str] = Field(default_factory=list)
    possible_objections: list[str] = Field(default_factory=list)
    suggested_demo: str
    closing_strategy: str
    meeting_notes: str = ""
    next_actions: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class AnalyticsEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_type: AnalyticsEventType
    action: str
    actor: str = "founder"
    company_id: UUID | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None


class CommandCenterState(BaseModel):
    model_config = ConfigDict(frozen=True)

    revenue_pipeline: float = 0.0
    expected_revenue: float = 0.0
    meetings: int = 0
    campaign_queue: int = 0
    inbox: int = 0
    daily_tasks: list[RevenueTask] = Field(default_factory=list)
    proposal_queue: list[ProposalQueueItem] = Field(default_factory=list)
    work_queue: list[dict[str, Any]] = Field(default_factory=list)
    todays_top_companies: list[dict[str, Any]] = Field(default_factory=list)
    follow_up_queue: list[dict[str, Any]] = Field(default_factory=list)


class FounderOsInput(BaseModel):
    """Snapshot inputs composed from existing Beacon engines — no redesign."""

    model_config = ConfigDict(frozen=True)

    new_companies_found: int = 0
    new_buying_signals: int = 0
    qualified_companies: int = 0
    sales_ready_accounts: int = 0
    a_plus_opportunities: int = 0
    campaigns_waiting_approval: int = 0
    replies_waiting: int = 0
    meetings_today: int = 0
    proposals_pending: int = 0
    estimated_pipeline: float = 0.0
    expected_revenue: float = 0.0
    lost_opportunities: int = 0
    won_opportunities: int = 0
    industry_wins: dict[str, int] = Field(default_factory=dict)
    service_wins: dict[str, int] = Field(default_factory=dict)
    outreach_style_wins: dict[str, int] = Field(default_factory=dict)
    subject_line_wins: dict[str, int] = Field(default_factory=dict)
    cta_wins: dict[str, int] = Field(default_factory=dict)
    contacted_count: int = 0
    replied_count: int = 0
    meeting_count: int = 0
    proposal_count: int = 0
    average_deal_size: float = 0.0
    average_sales_cycle_days: float = 0.0
    country_wins: dict[str, int] = Field(default_factory=dict)
    campaign_sends: int = 0
    campaign_replies: int = 0
    # Work items from revenue hunter / campaigns / inbox
    top_companies: list[dict[str, Any]] = Field(default_factory=list)
    work_queue_items: list[dict[str, Any]] = Field(default_factory=list)
    follow_ups: list[dict[str, Any]] = Field(default_factory=list)
    pending_campaigns: list[dict[str, Any]] = Field(default_factory=list)
    pending_replies: list[dict[str, Any]] = Field(default_factory=list)
    meetings: list[dict[str, Any]] = Field(default_factory=list)
    proposal_candidates: list[dict[str, Any]] = Field(default_factory=list)
    missing_contacts: list[dict[str, Any]] = Field(default_factory=list)
    website_audit_needed: list[dict[str, Any]] = Field(default_factory=list)
    verification_failed: list[dict[str, Any]] = Field(default_factory=list)
    timeline_seeds: list[dict[str, Any]] = Field(default_factory=list)
    now: datetime | None = None


class FounderOsDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    brief: DailyBriefSnapshot
    command_center: CommandCenterState
    assistant: FounderAssistantBrief
    tasks: list[RevenueTask] = Field(default_factory=list)
    timeline_events: list[TimelineEvent] = Field(default_factory=list)
    kpis: SalesKPISnapshot
    recommendations: list[FounderRecommendation] = Field(default_factory=list)
    proposals: list[ProposalQueueItem] = Field(default_factory=list)
    meeting_packs: list[MeetingIntelligencePack] = Field(default_factory=list)
    scoring_version: str = SCORING_VERSION
