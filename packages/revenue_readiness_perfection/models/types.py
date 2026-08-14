"""RRP types — quality gates for Sales Ready → Revenue Ready."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SCORING_VERSION = "rrp-v1"
UNKNOWN = "unknown"


class ContactCategory(StrEnum):
    DECISION_MAKER_EMAIL = "Decision Maker Email"
    BUSINESS_EMAIL = "Business Email"
    SUPPORT = "Support"
    SALES = "Sales"
    PRIVACY = "Privacy"
    LEGAL = "Legal"
    PRESS = "Press"


class FounderReviewLabel(StrEnum):
    PERFECT = "Perfect"
    GOOD = "Good"
    WRONG_CONTACT = "Wrong Contact"
    WRONG_SERVICE = "Wrong Service"
    WRONG_INTENT = "Wrong Intent"
    NOT_INTERESTED = "Not Interested"


class DecisionMakerRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    full_name: str
    job_title: str
    source_url: str
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    last_verified: str
    generic: bool = False


class ClassifiedContact(BaseModel):
    model_config = ConfigDict(frozen=True)

    email: str
    category: ContactCategory
    confidence: float = 0.0


class OpportunitySummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    company: str
    industry: str
    employees: str = UNKNOWN
    recommended_service: str
    reason: str
    buying_intent: float
    decision_maker: str
    business_email: str
    decision_maker_email: str | None = None
    website: str
    evidence: list[str] = Field(default_factory=list)
    recommended_first_message: str
    why_now: str
    confidence: float
    trust: float
    revenue_ready: bool


class Blocker(StrEnum):
    MISSING_DECISION_MAKER = "Missing Decision Maker"
    GENERIC_DECISION_MAKER = "Generic Decision Maker"
    MISSING_EMAIL = "Missing Email"
    MISSING_INTENT = "Missing Intent"
    MISSING_SERVICE_MATCH = "Missing Service Match"
    MISSING_IDENTITY = "Missing Identity"
    LOW_CONFIDENCE = "Low Confidence"
    LOW_TRUST = "Low Trust"
    WEBSITE_UNVERIFIED = "Website Unverified"


class PerfectedCompany(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: str
    company: str
    revenue_ready: bool
    sales_ready: bool
    blockers: list[Blocker] = Field(default_factory=list)
    opportunity: OpportunitySummary | None = None
    decision_maker: DecisionMakerRecord | None = None
    contacts: list[ClassifiedContact] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
