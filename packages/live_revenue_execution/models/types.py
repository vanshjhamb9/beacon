from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


SCORING_VERSION = "lre-v1"


class LREStage(StrEnum):
    DISCOVERED = "discovered"
    VERIFIED = "verified"
    ENRICHED = "enriched"
    DECISION_MAKER_FOUND = "decision_maker_found"
    RANKED_A_PLUS = "ranked_a_plus"
    STRATEGY_READY = "strategy_ready"
    OUTREACH_READY = "outreach_ready"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    EMAIL_SENT = "email_sent"
    OPENED = "opened"
    CLICKED = "clicked"
    WHATSAPP_SENT = "whatsapp_sent"
    REPLIED = "replied"
    MEETING_BOOKED = "meeting_booked"
    MEETING_PACK_READY = "meeting_pack_ready"
    PROPOSAL_READY = "proposal_ready"
    PROPOSAL_SENT = "proposal_sent"
    WON = "won"
    LOST = "lost"
    STOPPED = "stopped"


class ApprovalAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"
    SEND_LATER = "send_later"


class ChannelPreference(StrEnum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    EMAIL_THEN_WHATSAPP = "email_then_whatsapp"


class ProductionEmailPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    subject: str
    body_text: str
    body_html: str
    from_address: str | None = None
    to_address: str
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    calendly_url: str | None = None
    tracking_id: str
    unsubscribe_url: str | None = None
    open_pixel_url: str | None = None
    evidence: list[str] = Field(default_factory=list)


class WhatsAppPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    to_address: str
    body_text: str
    template_name: str | None = None
    template_language: str = "en_US"
    buttons: list[dict[str, str]] = Field(default_factory=list)
    media: list[dict[str, Any]] = Field(default_factory=list)
    calendly_url: str | None = None
    requires_founder_approval: bool = True
    evidence: list[str] = Field(default_factory=list)


class ApprovalCard(BaseModel):
    model_config = ConfigDict(frozen=True)

    campaign_id: UUID
    company_id: UUID
    company_name: str
    decision_maker: dict[str, Any] = Field(default_factory=dict)
    pain_points: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    email_preview: ProductionEmailPlan | None = None
    whatsapp_preview: WhatsAppPlan | None = None
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    calendly_preview: str | None = None
    probability: float = 0.0
    risk_score: float = 0.0
    priority: str = "B"
    recommended_action: ApprovalAction = ApprovalAction.APPROVE


class MeetingAutomationPack(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    company_summary: str
    pain_points: list[str] = Field(default_factory=list)
    dossier_highlights: list[str] = Field(default_factory=list)
    buying_intent_score: float = 0.0
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    past_emails: list[dict[str, Any]] = Field(default_factory=list)
    reply_history: list[dict[str, Any]] = Field(default_factory=list)
    recommended_questions: list[str] = Field(default_factory=list)
    likely_objections: list[str] = Field(default_factory=list)
    recommended_offer: str | None = None
    estimated_budget: str | None = None
    suggested_pricing: str | None = None
    competitor_signals: list[str] = Field(default_factory=list)
    case_studies: list[str] = Field(default_factory=list)
    meeting_timeline: list[str] = Field(default_factory=list)
    follow_up_tasks: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ProposalPackage(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    title: str
    version: str
    services: list[str] = Field(default_factory=list)
    timeline: str
    pricing: str
    case_studies: list[str] = Field(default_factory=list)
    roi: str
    deliverables: list[str] = Field(default_factory=list)
    terms: list[str] = Field(default_factory=list)
    outline: list[str] = Field(default_factory=list)
    pdf_base64: str | None = None
    tracking_id: str
    evidence: list[str] = Field(default_factory=list)


class RevenueAnalyticsSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    companies_found: int = 0
    qualified: int = 0
    sales_ready: int = 0
    campaigns: int = 0
    emails: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    replies: int = 0
    meetings: int = 0
    proposals: int = 0
    won: int = 0
    lost: int = 0
    revenue_closed: float = 0.0
    pipeline_value: float = 0.0
    avg_response_hours: float = 0.0
    avg_sales_cycle_days: float = 0.0
    daily: list[dict[str, Any]] = Field(default_factory=list)
    weekly: list[dict[str, Any]] = Field(default_factory=list)
    monthly: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class OutcomeLearningHint(BaseModel):
    model_config = ConfigDict(frozen=True)

    metric: str
    observation: str
    recommendation: str
    requires_human_approval: bool = True
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class LREInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    campaign_id: UUID | None = None
    opportunity_id: UUID | None = None
    industry: str | None = None
    priority_grade: str | None = None
    probability: float = 0.0
    risk_score: float = 0.0
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    email_subject: str | None = None
    email_body: str | None = None
    whatsapp_body: str | None = None
    to_email: str | None = None
    to_whatsapp: str | None = None
    from_email: str | None = None
    calendly_url: str | None = None
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    recommended_service: str | None = None
    expected_budget: str | None = None
    buying_intent_score: float = 0.0
    dossier_highlights: list[str] = Field(default_factory=list)
    past_emails: list[dict[str, Any]] = Field(default_factory=list)
    reply_history: list[dict[str, Any]] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    case_studies: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    funnel_counts: dict[str, int] = Field(default_factory=dict)
    revenue_closed: float = 0.0
    pipeline_value: float = 0.0
    channel_preference: ChannelPreference = ChannelPreference.EMAIL_THEN_WHATSAPP
    tracking_base_url: str = "https://beacon.local/t"
    unsubscribe_base_url: str = "https://beacon.local/unsubscribe"
    now: datetime | None = None


class LREDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    campaign_id: UUID | None = None
    stage: LREStage
    approval_card: ApprovalCard | None = None
    email_plan: ProductionEmailPlan | None = None
    whatsapp_plan: WhatsAppPlan | None = None
    meeting_pack: MeetingAutomationPack | None = None
    proposal: ProposalPackage | None = None
    analytics: RevenueAnalyticsSnapshot | None = None
    learning_hints: list[OutcomeLearningHint] = Field(default_factory=list)
    lifecycle_events: list[dict[str, Any]] = Field(default_factory=list)
    scoring_version: str = SCORING_VERSION
    evidence_chain: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
