from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


SCORING_VERSION = "asa-v1"


class SalesWorkflowStage(StrEnum):
    LEAD_DISCOVERED = "lead_discovered"
    QUALIFIED = "qualified"
    RESEARCH_COMPLETE = "research_complete"
    DECISION_MAKERS_FOUND = "decision_makers_found"
    SALES_PACKAGE_READY = "sales_package_ready"
    CAMPAIGN_CREATED = "campaign_created"
    FOUNDER_APPROVAL = "founder_approval"
    EMAIL_SENT = "email_sent"
    WHATSAPP_SENT = "whatsapp_sent"
    REPLY_RECEIVED = "reply_received"
    MEETING_REQUESTED = "meeting_requested"
    MEETING_BOOKED = "meeting_booked"
    PROPOSAL_PENDING = "proposal_pending"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    FOLLOW_UP = "follow_up"
    ARCHIVED = "archived"


class FollowUpChannel(StrEnum):
    EMAIL_FOLLOW_UP = "email_follow_up"
    VALUE_EMAIL = "value_email"
    WHATSAPP = "whatsapp"
    FINAL_EMAIL = "final_email"
    ARCHIVE = "archive"
    NONE = "none"


class NextActionKind(StrEnum):
    SEND_FOLLOW_UP = "send_follow_up"
    WAIT = "wait"
    BOOK_MEETING = "book_meeting"
    CALL = "call"
    WHATSAPP = "whatsapp"
    SEND_CASE_STUDY = "send_case_study"
    PREPARE_PROPOSAL = "prepare_proposal"
    CLOSE_FILE = "close_file"
    APPROVE_CAMPAIGN = "approve_campaign"
    ATTEND_MEETING = "attend_meeting"
    WRITE_PROPOSAL = "write_proposal"
    NEGOTIATE = "negotiate"


class ObjectionKind(StrEnum):
    BUDGET = "Budget"
    TIMING = "Timing"
    NO_TEAM = "No team"
    EXISTING_VENDOR = "Already using vendor"
    NEED_APPROVAL = "Need approval"
    NO_URGENCY = "No urgency"
    NOT_INTERESTED = "Not interested"
    WRONG_CONTACT = "Wrong contact"
    NEED_PROPOSAL = "Need proposal"
    NEED_DEMO = "Need demo"


class WorkflowTransition(BaseModel):
    model_config = ConfigDict(frozen=True)

    from_stage: SalesWorkflowStage | None
    to_stage: SalesWorkflowStage
    timestamp: datetime
    reason: str
    evidence: list[str] = Field(default_factory=list)
    actor: str = "system"
    next_action: str


class FollowUpRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    channel: FollowUpChannel
    days_since_last_touch: int
    message_hint: str
    due: bool
    evidence: list[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_type: str
    title: str
    detail: str = ""
    occurred_at: datetime | None = None
    actor: str = "system"
    evidence: list[str] = Field(default_factory=list)


class MeetingIntelligencePack(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_overview: str
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    business_pains: list[str] = Field(default_factory=list)
    automation_opportunities: list[str] = Field(default_factory=list)
    likely_objections: list[str] = Field(default_factory=list)
    discovery_questions: list[str] = Field(default_factory=list)
    upsell_ideas: list[str] = Field(default_factory=list)
    cross_sell_ideas: list[str] = Field(default_factory=list)
    budget_hints: str
    technology_stack: list[str] = Field(default_factory=list)
    recent_activity: list[str] = Field(default_factory=list)
    competitive_landscape: list[str] = Field(default_factory=list)
    roi_talking_points: list[str] = Field(default_factory=list)
    meeting_agenda: list[str] = Field(default_factory=list)
    success_checklist: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class NextBestAction(BaseModel):
    model_config = ConfigDict(frozen=True)

    action: NextActionKind
    confidence: float = Field(ge=0.0, le=100.0)
    reason: str
    evidence: list[str] = Field(default_factory=list)
    expected_impact: str


class CaseStudyRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    industry_key: str
    title: str
    relevance: float = Field(ge=0.0, le=100.0)
    why: str
    evidence: list[str] = Field(default_factory=list)


class ObjectionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    objection: ObjectionKind
    frequency: int = 1
    industry: str | None = None
    company_size: str | None = None
    win_rate: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class SalesMemoryInsight(BaseModel):
    model_config = ConfigDict(frozen=True)

    best_email_pattern: str | None = None
    best_cta: str | None = None
    best_follow_up_interval_days: int = 2
    best_industries: list[str] = Field(default_factory=list)
    best_company_sizes: list[str] = Field(default_factory=list)
    best_founders: list[str] = Field(default_factory=list)
    best_service: str | None = None
    best_conversion_source: str | None = None
    evidence: list[str] = Field(default_factory=list)


class FounderWorkItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: str
    company_id: UUID | None = None
    company_name: str
    priority: str = "P1"
    summary: str
    due_at: datetime | None = None
    evidence: list[str] = Field(default_factory=list)


class MorningBrief(BaseModel):
    model_config = ConfigDict(frozen=True)

    priorities: list[str] = Field(default_factory=list)
    expected_meetings: list[dict[str, Any]] = Field(default_factory=list)
    expected_replies: list[dict[str, Any]] = Field(default_factory=list)
    high_risk_deals: list[dict[str, Any]] = Field(default_factory=list)
    companies_requiring_attention: list[dict[str, Any]] = Field(default_factory=list)
    revenue_forecast: float = 0.0
    follow_ups_due: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class FollowUpConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    follow_up_days: int = 2
    value_email_days: int = 5
    whatsapp_days: int = 8
    final_email_days: int = 12
    archive_days: int = 20


class AutonomousSalesAgentInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    industry: str | None = None
    company_size: str | None = None
    stage_hint: str | None = None
    priority_grade: str | None = None
    probability: float = 0.0
    buying_intent_score: float = 0.0
    days_since_last_touch: int = 0
    last_touch_channel: str | None = None
    has_decision_makers: bool = False
    has_sales_package: bool = False
    has_campaign: bool = False
    campaign_approved: bool = False
    email_sent: bool = False
    whatsapp_sent: bool = False
    reply_received: bool = False
    meeting_requested: bool = False
    meeting_booked: bool = False
    meeting_completed: bool = False
    proposal_pending: bool = False
    proposal_sent: bool = False
    negotiation: bool = False
    won: bool = False
    lost: bool = False
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    pains: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    vendors: list[str] = Field(default_factory=list)
    objections_seen: list[str] = Field(default_factory=list)
    recent_activity: list[str] = Field(default_factory=list)
    recommended_service: str | None = None
    expected_budget: str | None = None
    founder_notes: list[str] = Field(default_factory=list)
    timeline_seeds: list[dict[str, Any]] = Field(default_factory=list)
    meetings_today: list[dict[str, Any]] = Field(default_factory=list)
    pending_approvals: list[dict[str, Any]] = Field(default_factory=list)
    high_intent_replies: list[dict[str, Any]] = Field(default_factory=list)
    proposal_queue: list[dict[str, Any]] = Field(default_factory=list)
    negotiation_queue: list[dict[str, Any]] = Field(default_factory=list)
    follow_up_config: FollowUpConfig = Field(default_factory=FollowUpConfig)
    memory_signals: dict[str, Any] = Field(default_factory=dict)
    pipeline_value: float = 0.0
    now: datetime | None = None


class AutonomousSalesAgentDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    stage: SalesWorkflowStage
    transitions: list[WorkflowTransition] = Field(default_factory=list)
    follow_up: FollowUpRecommendation
    timeline: list[TimelineEvent] = Field(default_factory=list)
    meeting_intelligence: MeetingIntelligencePack | None = None
    next_best_action: NextBestAction
    case_study: CaseStudyRecommendation | None = None
    objections: list[ObjectionRecord] = Field(default_factory=list)
    sales_memory: SalesMemoryInsight
    work_queue: list[FounderWorkItem] = Field(default_factory=list)
    morning_brief: MorningBrief
    scoring_version: str = SCORING_VERSION
    evidence_chain: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
