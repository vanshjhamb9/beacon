"""CLR v1 types — closed-loop revenue validation. Analytics only. No GPT."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

VERSION = "clr-v1"
UNKNOWN = "unknown"


class OutcomeType(StrEnum):
    READY = "READY"
    CONTACTED = "CONTACTED"
    EMAIL_SENT = "EMAIL_SENT"
    OPENED = "OPENED"
    CLICKED = "CLICKED"
    REPLIED = "REPLIED"
    POSITIVE_REPLY = "POSITIVE_REPLY"
    NEGATIVE_REPLY = "NEGATIVE_REPLY"
    MEETING_BOOKED = "MEETING_BOOKED"
    MEETING_COMPLETED = "MEETING_COMPLETED"
    PROPOSAL_SENT = "PROPOSAL_SENT"
    NEGOTIATION = "NEGOTIATION"
    WON = "WON"
    LOST = "LOST"
    NO_RESPONSE = "NO_RESPONSE"
    FOLLOW_UP_REQUIRED = "FOLLOW_UP_REQUIRED"
    FOLLOW_UP_SENT = "FOLLOW_UP_SENT"


# OFC status → CLR outcome mapping (compose only)
OFC_TO_OUTCOME = {
    "READY": OutcomeType.READY,
    "CONTACTED": OutcomeType.CONTACTED,
    "REPLIED": OutcomeType.REPLIED,
    "MEETING_BOOKED": OutcomeType.MEETING_BOOKED,
    "PROPOSAL_SENT": OutcomeType.PROPOSAL_SENT,
    "NEGOTIATION": OutcomeType.NEGOTIATION,
    "WON": OutcomeType.WON,
    "LOST": OutcomeType.LOST,
    "PAUSED": OutcomeType.NO_RESPONSE,
}


class TriState(StrEnum):
    YES = "YES"
    PARTIAL = "PARTIAL"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class BinaryState(StrEnum):
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class HealthTone(StrEnum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class OutcomeEvent(BaseModel):
    company_id: str
    outreach_record_id: str | None = None
    outcome: OutcomeType
    timestamp: str
    actor: str = "founder"
    source: str = "clr"
    notes: str | None = None
    previous_state: str | None = None
    new_state: str | None = None


class RevenueAttribution(BaseModel):
    company: str
    company_id: str
    service_sold: str = UNKNOWN
    revenue_amount: float = 0.0
    currency: str = "USD"
    close_date: str | None = None
    sales_cycle_days: float | None = None
    proposal_value: float = 0.0
    expected_revenue: float = 0.0
    actual_revenue: float = 0.0
    founder: str = "Vansh"
    source_connector: str = UNKNOWN
    revenue_ready_snapshot_id: str | None = None


class PredictionValidation(BaseModel):
    company_id: str
    company: str
    interested: TriState = TriState.UNKNOWN
    decision_maker_correct: TriState = TriState.UNKNOWN
    why_now_accurate: TriState = TriState.UNKNOWN
    service_accepted: TriState = TriState.UNKNOWN
    confidence_realistic: BinaryState = BinaryState.UNKNOWN
    notes: str | None = None


class DailyBriefCard(BaseModel):
    company: str
    company_id: str
    decision_maker: str = UNKNOWN
    email: str | None = None
    why_today: str = UNKNOWN
    last_activity: str | None = None
    suggested_next_step: str = UNKNOWN
    priority: int = 1


class ProductionHealth(BaseModel):
    metric: str
    value: float | int | str
    tone: HealthTone
    detail: str = ""
