"""OFC v2 types — outreach workspace. No GPT. Analytics never auto-change scoring."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

VERSION = "ofc-v2"
UNKNOWN = "unknown"
DEFAULT_PIPELINE_VALUE = 5000.0


class OutreachStatus(StrEnum):
    READY = "READY"
    CONTACTED = "CONTACTED"
    REPLIED = "REPLIED"
    MEETING_BOOKED = "MEETING_BOOKED"
    PROPOSAL_SENT = "PROPOSAL_SENT"
    NEGOTIATION = "NEGOTIATION"
    WON = "WON"
    LOST = "LOST"
    PAUSED = "PAUSED"


ALLOWED_TRANSITIONS: dict[OutreachStatus, frozenset[OutreachStatus]] = {
    OutreachStatus.READY: frozenset(
        {OutreachStatus.CONTACTED, OutreachStatus.PAUSED, OutreachStatus.LOST}
    ),
    OutreachStatus.CONTACTED: frozenset(
        {
            OutreachStatus.REPLIED,
            OutreachStatus.PAUSED,
            OutreachStatus.LOST,
            OutreachStatus.READY,
        }
    ),
    OutreachStatus.REPLIED: frozenset(
        {
            OutreachStatus.MEETING_BOOKED,
            OutreachStatus.PAUSED,
            OutreachStatus.LOST,
            OutreachStatus.CONTACTED,
        }
    ),
    OutreachStatus.MEETING_BOOKED: frozenset(
        {
            OutreachStatus.PROPOSAL_SENT,
            OutreachStatus.PAUSED,
            OutreachStatus.LOST,
            OutreachStatus.REPLIED,
        }
    ),
    OutreachStatus.PROPOSAL_SENT: frozenset(
        {
            OutreachStatus.NEGOTIATION,
            OutreachStatus.WON,
            OutreachStatus.LOST,
            OutreachStatus.PAUSED,
        }
    ),
    OutreachStatus.NEGOTIATION: frozenset(
        {OutreachStatus.WON, OutreachStatus.LOST, OutreachStatus.PAUSED, OutreachStatus.PROPOSAL_SENT}
    ),
    OutreachStatus.WON: frozenset(),
    OutreachStatus.LOST: frozenset({OutreachStatus.READY, OutreachStatus.PAUSED}),
    OutreachStatus.PAUSED: frozenset({OutreachStatus.READY, OutreachStatus.CONTACTED, OutreachStatus.LOST}),
}


class TimelineEventType(StrEnum):
    EMAIL_SENT = "Email sent"
    REPLY_RECEIVED = "Reply received"
    MEETING_BOOKED = "Meeting booked"
    FOLLOW_UP = "Follow-up"
    PROPOSAL = "Proposal"
    WON = "Won"
    LOST = "Lost"
    STATUS_CHANGE = "Status change"
    NOTE = "Note"


class ObjectionLabel(StrEnum):
    NO_BUDGET = "No Budget"
    ALREADY_USING_COMPETITOR = "Already using competitor"
    NO_REPLY = "No Reply"
    WRONG_CONTACT = "Wrong Contact"
    NOT_PRIORITY = "Not Priority"
    INTERESTED = "Interested"
    MEETING_SCHEDULED = "Meeting Scheduled"


class StatusTransition(BaseModel):
    status: OutreachStatus
    at: str
    note: str | None = None


class OutreachBrief(BaseModel):
    company: str
    website: str | None = None
    industry: str = UNKNOWN
    decision_maker: str = UNKNOWN
    decision_maker_email: str | None = None
    business_email: str | None = None
    why_now: str = UNKNOWN
    recommended_service: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    trust: float = 0.0
    revenue_ready_score: float = 0.0
    recent_signals: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    recommended_cta: str = UNKNOWN
    first_message_template: str | None = None


class DailyAction(BaseModel):
    action: str
    company: str | None = None
    company_id: str | None = None
    status: str | None = None
    why: str
    channel: str | None = None
    priority: int = 1
