from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


SCORING_VERSION = "goi-v1"


class JourneyStage(StrEnum):
    DISCOVERED = "discovered"
    QUALIFIED = "qualified"
    ENRICHED = "enriched"
    DECISION_MAKERS = "decision_makers"
    OUTREACH_READY = "outreach_ready"
    CAMPAIGN_ACTIVE = "campaign_active"
    CONTACTED = "contacted"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    MEETING_SCHEDULED = "meeting_scheduled"
    PROPOSAL_REQUESTED = "proposal_requested"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    DORMANT = "dormant"
    REACTIVATED = "reactivated"


class AccountHealthCategory(StrEnum):
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"
    PRIORITY = "priority"
    CRITICAL = "critical"
    DORMANT = "dormant"
    RECOVERED = "recovered"


class CommitteeRole(StrEnum):
    CHAMPION = "champion"
    ECONOMIC_BUYER = "economic_buyer"
    TECHNICAL_BUYER = "technical_buyer"
    INFLUENCER = "influencer"
    LEGAL = "legal"
    PROCUREMENT = "procurement"
    OPERATIONS = "operations"


class FollowUpChannel(StrEnum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    FOLLOW_UP_EMAIL = "follow_up_email"
    REMINDER = "reminder"
    MEETING = "meeting"
    PROPOSAL = "proposal"
    FOUNDER_FOLLOW_UP = "founder_follow_up"
    WAIT = "wait"


class ReplyClass(StrEnum):
    INTERESTED = "interested"
    NEED_PROPOSAL = "need_proposal"
    BUDGET_CONCERN = "budget_concern"
    TIMING_CONCERN = "timing_concern"
    NOT_NOW = "not_now"
    COMPETITOR = "competitor"
    WRONG_CONTACT = "wrong_contact"
    SPAM = "spam"
    MEETING_REQUESTED = "meeting_requested"
    UNKNOWN = "unknown"


class JourneyTransition(BaseModel):
    model_config = ConfigDict(frozen=True)

    from_stage: JourneyStage | None
    to_stage: JourneyStage
    timestamp: datetime
    reason: str
    evidence: list[str] = Field(default_factory=list)
    actor: str = "system"


class InteractionSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: str
    weight: float
    polarity: str = "positive"
    detail: str = ""
    evidence: list[str] = Field(default_factory=list)


class OutreachIntelligence(BaseModel):
    model_config = ConfigDict(frozen=True)

    signals: list[InteractionSignal] = Field(default_factory=list)
    positive_score: float = 0.0
    negative_score: float = 0.0
    ghosting: bool = False
    account_health_delta: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class TouchStep(BaseModel):
    model_config = ConfigDict(frozen=True)

    channel: FollowUpChannel
    sequence: int
    delay_hours: float
    message_type: str
    reason: str
    requires_founder_approval: bool = True
    evidence: list[str] = Field(default_factory=list)


class MultiTouchPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    steps: list[TouchStep] = Field(default_factory=list)
    adaptive: bool = True
    evidence: list[str] = Field(default_factory=list)


class EngagementScores(BaseModel):
    model_config = ConfigDict(frozen=True)

    open_score: float = Field(ge=0.0, le=100.0, default=0.0)
    reply_score: float = Field(ge=0.0, le=100.0, default=0.0)
    intent_score: float = Field(ge=0.0, le=100.0, default=0.0)
    meeting_score: float = Field(ge=0.0, le=100.0, default=0.0)
    relationship_score: float = Field(ge=0.0, le=100.0, default=0.0)
    account_temperature: float = Field(ge=0.0, le=100.0, default=0.0)
    overall_engagement: float = Field(ge=0.0, le=100.0, default=0.0)
    evidence: list[str] = Field(default_factory=list)


class AccountHealth(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: AccountHealthCategory
    score: float = Field(ge=0.0, le=100.0)
    reason: str
    evidence: list[str] = Field(default_factory=list)


class CommitteeMember(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    role: CommitteeRole
    title: str | None = None
    email: str | None = None
    relationship_strength: float = Field(ge=0.0, le=100.0, default=40.0)
    evidence: list[str] = Field(default_factory=list)


class BuyingCommittee(BaseModel):
    model_config = ConfigDict(frozen=True)

    members: list[CommitteeMember] = Field(default_factory=list)
    coverage: float = Field(ge=0.0, le=100.0, default=0.0)
    missing_roles: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class FollowUpPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    next_action: str
    best_timing_hours: float
    channel: FollowUpChannel
    message_type: str
    urgency: str
    reason: str
    requires_founder_approval: bool = True
    evidence: list[str] = Field(default_factory=list)


class CampaignAnalyticsSlice(BaseModel):
    model_config = ConfigDict(frozen=True)

    dimension: str
    key: str
    reply_pct: float = 0.0
    meeting_pct: float = 0.0
    proposal_pct: float = 0.0
    close_pct: float = 0.0
    revenue: float = 0.0
    accounts: int = 0
    evidence: list[str] = Field(default_factory=list)


class CampaignAnalytics(BaseModel):
    model_config = ConfigDict(frozen=True)

    by_country: list[CampaignAnalyticsSlice] = Field(default_factory=list)
    by_industry: list[CampaignAnalyticsSlice] = Field(default_factory=list)
    by_company_size: list[CampaignAnalyticsSlice] = Field(default_factory=list)
    by_technology: list[CampaignAnalyticsSlice] = Field(default_factory=list)
    by_service: list[CampaignAnalyticsSlice] = Field(default_factory=list)
    by_campaign: list[CampaignAnalyticsSlice] = Field(default_factory=list)
    by_decision_maker_role: list[CampaignAnalyticsSlice] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ReplyClassification(BaseModel):
    model_config = ConfigDict(frozen=True)

    classification: ReplyClass
    confidence: float = Field(ge=0.0, le=100.0)
    structured_outcome: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_type: str
    title: str
    detail: str = ""
    occurred_at: datetime | None = None
    actor: str = "system"
    evidence: list[str] = Field(default_factory=list)


class AccountJourneyInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    industry: str | None = None
    country: str | None = None
    company_size: str | None = None
    technologies: list[str] = Field(default_factory=list)
    service: str | None = None
    campaign_name: str | None = None
    stage_hint: str | None = None
    probability: float = 0.0
    buying_intent: float = 0.0
    qualified: bool = False
    enriched: bool = False
    has_decision_makers: bool = False
    outreach_ready: bool = False
    campaign_active: bool = False
    emailed: bool = False
    whatsapp_sent: bool = False
    opened: bool = False
    clicked: bool = False
    replied: bool = False
    no_reply_days: int = 0
    cta_clicks: int = 0
    video_watched: bool = False
    calendly_opened: bool = False
    calendar_booked: bool = False
    meeting_scheduled: bool = False
    proposal_requested: bool = False
    negotiation: bool = False
    won: bool = False
    lost: bool = False
    dormant_days: int = 0
    reactivated: bool = False
    reply_text: str = ""
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    founder_notes: list[str] = Field(default_factory=list)
    timeline_seeds: list[dict[str, Any]] = Field(default_factory=list)
    cohort_accounts: list[dict[str, Any]] = Field(default_factory=list)
    now: datetime | None = None


class AccountJourneyDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    stage: JourneyStage
    transitions: list[JourneyTransition] = Field(default_factory=list)
    outreach: OutreachIntelligence
    multi_touch: MultiTouchPlan
    engagement: EngagementScores
    health: AccountHealth
    buying_committee: BuyingCommittee
    follow_up: FollowUpPlan
    analytics: CampaignAnalytics
    reply: ReplyClassification | None = None
    timeline: list[TimelineEvent] = Field(default_factory=list)
    scoring_version: str = SCORING_VERSION
    evidence_chain: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
