from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OpportunityStatus(StrEnum):
    OBSERVED = "observed"
    WATCHING = "watching"
    EMERGING = "emerging"
    QUALIFIED = "qualified"
    HIGH_INTENT = "high_intent"
    CONTACTED = "contacted"
    MEETING = "meeting"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"
    ARCHIVED = "archived"


class RecommendationAction(StrEnum):
    IGNORE = "ignore"
    WATCH = "watch"
    COLLECT_MORE_EVIDENCE = "collect_more_evidence"
    CONTACT_WITHIN_30_DAYS = "contact_within_30_days"
    CONTACT_WITHIN_7_DAYS = "contact_within_7_days"
    CONTACT_TODAY = "contact_today"
    ESCALATE = "escalate"
    ARCHIVE = "archive"


class OpportunityEvidenceItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_type: str
    reference_id: UUID
    category: str
    summary: str
    confidence: float
    occurred_at: datetime
    polarity: str = "supporting"
    weight: float = 1.0
    details: dict[str, Any] = Field(default_factory=dict)


class CompanyOpportunityInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    business_context_ids: list[UUID]
    latest_context_at: datetime
    contexts: list[dict[str, Any]]
    company_profile: dict[str, Any]
    signals: list[dict[str, Any]]
    timeline: list[dict[str, Any]]
    pains: list[dict[str, Any]]
    goals: list[dict[str, Any]]
    technologies: list[dict[str, Any]]
    evidence: list[OpportunityEvidenceItem]
    previous_opportunity_id: UUID | None = None
    previous_score: float | None = None
    previous_status: OpportunityStatus | None = None


class ScoreComponent(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    value: float
    weight: float
    explanation: str
    evidence_ids: list[UUID] = Field(default_factory=list)


class OpportunityConflict(BaseModel):
    model_config = ConfigDict(frozen=True)

    conflict_type: str
    supporting_signal: str
    contradicting_signal: str
    severity: float
    explanation: str
    evidence_ids: list[UUID] = Field(default_factory=list)


class OpportunityDelta(BaseModel):
    model_config = ConfigDict(frozen=True)

    score_change: float
    direction: str
    new_evidence: list[UUID] = Field(default_factory=list)
    expired_evidence: list[UUID] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class OpportunityRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    action: RecommendationAction
    confidence: float
    reasons: list[str]
    next_step: str


class OpportunityDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    status: OpportunityStatus
    recommendation: OpportunityRecommendation
    opportunity_score: float
    timing_score: float
    confidence_score: float
    urgency_score: float
    growth_score: float
    technology_fit_score: float
    ai_readiness_score: float
    automation_readiness_score: float
    decision_confidence_score: float
    budget_probability_score: float
    score_breakdown: list[ScoreComponent]
    evidence: list[OpportunityEvidenceItem]
    supporting_signals: list[OpportunityEvidenceItem]
    contradicting_signals: list[OpportunityEvidenceItem]
    conflicts: list[OpportunityConflict]
    delta: OpportunityDelta
    narrative: str
    created_from_context_ids: list[UUID]
    scoring_latency_ms: float
    decision_latency_ms: float
