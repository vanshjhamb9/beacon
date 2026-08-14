from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


SCORING_VERSION = "si-v1"


class BuyingStage(StrEnum):
    UNAWARE = "unaware"
    PROBLEM_AWARE = "problem_aware"
    SOLUTION_AWARE = "solution_aware"
    VENDOR_EVALUATION = "vendor_evaluation"
    NEGOTIATION = "negotiation"
    COMMITTED = "committed"


class UrgencyLevel(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class BudgetBand(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    ENTERPRISE = "Enterprise"


class CommunicationStyle(StrEnum):
    DIRECT = "direct"
    CONSULTATIVE = "consultative"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"
    FRIENDLY = "friendly"


class ObjectionType(StrEnum):
    BUDGET = "Budget"
    TIMELINE = "Timeline"
    SECURITY = "Security"
    COMPLIANCE = "Compliance"
    EXISTING_VENDOR = "Existing Vendor"
    INTERNAL_TEAM = "Internal Team"
    ROI = "ROI"
    TRUST = "Trust"
    TECHNICAL_COMPLEXITY = "Technical Complexity"


class OfferType(StrEnum):
    AI_AUTOMATION = "AI Automation"
    AI_CUSTOMER_SUPPORT = "AI Customer Support"
    CUSTOM_SAAS = "Custom SaaS"
    MARKETPLACE = "Marketplace"
    MOBILE_APP = "Mobile App"
    WEBSITE = "Website"
    MVP = "MVP"
    CONSULTING = "Consulting"
    DIGITAL_TRANSFORMATION = "Digital Transformation"


class ReplyClass(StrEnum):
    INTERESTED = "Interested"
    NEED_PROPOSAL = "Need Proposal"
    NEED_MEETING = "Need Meeting"
    TECHNICAL_QUESTION = "Technical Question"
    BUDGET_CONCERN = "Budget Concern"
    SECURITY_CONCERN = "Security Concern"
    TIMING_ISSUE = "Timing Issue"
    WRONG_CONTACT = "Wrong Contact"
    NOT_INTERESTED = "Not Interested"
    UNKNOWN = "Unknown"


class MemoryEventType(StrEnum):
    EMAIL = "email"
    REPLY = "reply"
    MEETING = "meeting"
    PROPOSAL = "proposal"
    OBJECTION = "objection"
    FOLLOW_UP = "follow_up"
    NOTE = "note"
    OUTCOME = "outcome"


class BuyingIntentResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    buying_intent_score: float = Field(ge=0.0, le=100.0)
    buying_stage: BuyingStage
    urgency: UrgencyLevel
    budget_probability: BudgetBand
    decision_window_days: int
    decision_complexity: str
    buying_confidence: float = Field(ge=0.0, le=100.0)
    evidence_chain: list[str] = Field(default_factory=list)


class PsychologyProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    buyer_motivation: str
    risk_tolerance: str
    innovation_level: str
    growth_focus: str
    cost_sensitivity: str
    automation_readiness: float = Field(ge=0.0, le=100.0)
    pain_intensity: float = Field(ge=0.0, le=100.0)
    preferred_communication_style: CommunicationStyle
    evidence: list[str] = Field(default_factory=list)


class PredictedObjection(BaseModel):
    model_config = ConfigDict(frozen=True)

    objection: ObjectionType
    likelihood: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=100.0)
    suggested_response: str
    evidence: list[str] = Field(default_factory=list)


class OfferRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    primary_offer: OfferType
    secondary_offer: OfferType | None = None
    cross_sell: list[OfferType] = Field(default_factory=list)
    expected_value: str
    ranking: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class TrustAsset(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: str
    title: str
    relevance: float = Field(ge=0.0, le=100.0)
    evidence: list[str] = Field(default_factory=list)


class TrustBuilderResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_studies: list[TrustAsset] = Field(default_factory=list)
    portfolio_items: list[TrustAsset] = Field(default_factory=list)
    testimonials: list[TrustAsset] = Field(default_factory=list)
    industries_served: list[str] = Field(default_factory=list)
    technology_stack: list[str] = Field(default_factory=list)
    success_stories: list[TrustAsset] = Field(default_factory=list)


class ProposalIntelligence(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposal_outline: list[str] = Field(default_factory=list)
    scope: list[str] = Field(default_factory=list)
    timeline: str
    deliverables: list[str] = Field(default_factory=list)
    architecture: list[str] = Field(default_factory=list)
    budget_range: str
    roi_estimate: str
    implementation_plan: list[str] = Field(default_factory=list)
    risk_assessment: list[dict[str, str]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class MeetingCoachPack(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_summary: str
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    business_pain: list[str] = Field(default_factory=list)
    buying_signals: list[str] = Field(default_factory=list)
    discovery_questions: list[str] = Field(default_factory=list)
    likely_objections: list[str] = Field(default_factory=list)
    closing_strategy: str
    meeting_goals: list[str] = Field(default_factory=list)
    follow_up_plan: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ReplyIntelligenceResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    classification: ReplyClass
    best_response: str
    confidence: float = Field(ge=0.0, le=100.0)
    reason: str
    evidence: list[str] = Field(default_factory=list)
    reply_ref: str | None = None


class MemoryEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: MemoryEventType
    title: str
    detail: str = ""
    occurred_at: datetime | None = None
    refs: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class SalesMemory(BaseModel):
    model_config = ConfigDict(frozen=True)

    events: list[MemoryEvent] = Field(default_factory=list)
    relationship_timeline: list[dict[str, Any]] = Field(default_factory=list)
    buying_journey: list[dict[str, Any]] = Field(default_factory=list)


class SalesScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    deal_probability: float = Field(ge=0.0, le=100.0)
    revenue_probability: float = Field(ge=0.0, le=100.0)
    expected_deal_size: str
    sales_health: float = Field(ge=0.0, le=100.0)
    relationship_health: float = Field(ge=0.0, le=100.0)
    competition_risk: float = Field(ge=0.0, le=100.0)
    close_probability: float = Field(ge=0.0, le=100.0)
    evidence: list[str] = Field(default_factory=list)


class SalesIntelligenceInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    opportunity_id: UUID | None = None
    industry: str | None = None
    country: str | None = None
    employee_count: int | None = None
    funding_stage: str | None = None
    funding_days_ago: int | None = None
    revenue_band: str | None = None
    technologies: list[str] = Field(default_factory=list)
    pains: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    hiring_roles: list[str] = Field(default_factory=list)
    hiring_count: int = 0
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    recommended_service: str | None = None
    expected_budget: str | None = None
    opportunity_score: float = 0.0
    priority_grade: str | None = None
    probability: float = 0.0
    website_opportunities: list[str] = Field(default_factory=list)
    replies: list[dict[str, Any]] = Field(default_factory=list)
    emails: list[dict[str, Any]] = Field(default_factory=list)
    meetings: list[dict[str, Any]] = Field(default_factory=list)
    proposals: list[dict[str, Any]] = Field(default_factory=list)
    objections_seen: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    outcomes: list[dict[str, Any]] = Field(default_factory=list)
    follow_ups: list[dict[str, Any]] = Field(default_factory=list)
    vendors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    now: datetime | None = None


class SalesIntelligenceDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    opportunity_id: UUID | None = None
    buying_intent: BuyingIntentResult
    psychology: PsychologyProfile
    objections: list[PredictedObjection] = Field(default_factory=list)
    offer: OfferRecommendation
    trust: TrustBuilderResult
    proposal: ProposalIntelligence
    meeting_coach: MeetingCoachPack
    reply_intelligence: list[ReplyIntelligenceResult] = Field(default_factory=list)
    memory: SalesMemory
    score: SalesScore
    scoring_version: str = SCORING_VERSION
    evidence_chain: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
