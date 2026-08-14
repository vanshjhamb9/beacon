from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChannelKind(StrEnum):
    EMAIL = "email"
    WHATSAPP_BUSINESS = "whatsapp_business"
    LINKEDIN = "linkedin"
    PHONE_CALL = "phone_call"
    PERSONALIZED_VIDEO = "personalized_video"
    CALENDAR_INVITATION = "calendar_invitation"


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class CampaignPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StepKind(StrEnum):
    INITIAL = "initial"
    FOLLOW_UP = "follow_up"
    VIDEO = "video"
    CALL = "call"
    MEETING_INVITE = "meeting_invite"


class EvidenceItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: str
    summary: str
    source: str
    confidence: float = Field(default=0.0, ge=0.0, le=100.0)
    reference_id: str | None = None


class ChannelCapability(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: ChannelKind
    label: str
    supports_async: bool = True
    supports_attachments: bool = False
    requires_opt_in: bool = False
    max_daily_sends: int = 50
    min_gap_hours: float = 24.0
    business_hours_only: bool = True
    constraints: list[str] = Field(default_factory=list)
    delivery_ready: bool = False  # Sprint 14: never true for live send


class ScheduleRules(BaseModel):
    model_config = ConfigDict(frozen=True)

    timezone: str = "UTC"
    business_hours_start: int = Field(default=9, ge=0, le=23)
    business_hours_end: int = Field(default=17, ge=1, le=24)
    working_days: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])  # Mon-Fri
    rate_limit_per_day: int = 20
    sequence_delay_hours: list[float] = Field(default_factory=lambda: [0.0, 48.0, 96.0, 168.0])
    retry_window_hours: float = 24.0
    exclude_holidays: bool = True
    holiday_calendars: list[str] = Field(default_factory=lambda: ["US"])


class CampaignStepPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    sequence: int
    kind: StepKind
    channel: ChannelKind
    delay_hours: float
    draft_kind: str
    draft_style: str
    subject_preview: str = ""
    body_preview: str = ""
    message_selection_reason: str
    timing_reason: str
    confidence: float = Field(ge=0.0, le=100.0)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    sales_draft_ref: dict[str, Any] = Field(default_factory=dict)


class CampaignPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    opportunity_id: UUID
    sales_package_id: UUID | None = None
    company_name: str
    status: CampaignStatus = CampaignStatus.NEEDS_REVIEW
    priority: CampaignPriority
    primary_channel: ChannelKind
    secondary_channel: ChannelKind | None = None
    outreach_sequence: list[CampaignStepPlan] = Field(default_factory=list)
    follow_up_count: int = 0
    delay_hours_between_messages: list[float] = Field(default_factory=list)
    expected_confidence: float = Field(ge=0.0, le=100.0)
    channel_choice_reason: str
    timing_reason: str
    message_selection_reason: str
    schedule_rules: ScheduleRules
    recommended_service: str = ""
    business_pain: str = ""
    buyer_persona: str | None = None
    industry: str | None = None
    communication_style: str = "professional"
    evidence: list[EvidenceItem] = Field(default_factory=list)
    quality: dict[str, Any] = Field(default_factory=dict)
    plan_payload: dict[str, Any] = Field(default_factory=dict)


class CampaignInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    opportunity_id: UUID
    company_name: str
    industry: str | None = None
    company_size: str | None = None
    timezone: str = "UTC"
    opportunity_score: float = 0.0
    opportunity_status: str = ""
    opportunity_urgency: float = 0.0
    recommended_service: str = ""
    business_pain: str = ""
    buyer_persona: str | None = None
    sales_package: dict[str, Any] = Field(default_factory=dict)
    decision_discovery: dict[str, Any] = Field(default_factory=dict)
    revenue: dict[str, Any] = Field(default_factory=dict)
    opportunity: dict[str, Any] = Field(default_factory=dict)
    verification: dict[str, Any] = Field(default_factory=dict)
    outcomes: dict[str, Any] = Field(default_factory=dict)
    force_refresh: bool = False
