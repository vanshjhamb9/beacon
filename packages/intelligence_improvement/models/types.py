from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FeedbackSource(StrEnum):
    HUMAN_REVIEW = "human_review"
    OPPORTUNITY_ACCEPTED = "opportunity_accepted"
    OPPORTUNITY_REJECTED = "opportunity_rejected"
    MEETING_BOOKED = "meeting_booked"
    PROPOSAL_SENT = "proposal_sent"
    WON = "won"
    LOST = "lost"
    MANUAL_CORRECTION = "manual_correction"
    FALSE_POSITIVE = "false_positive"
    FALSE_NEGATIVE = "false_negative"


class ImprovementArea(StrEnum):
    COLLECTOR = "collector"
    QUALITY_RULE = "quality_rule"
    CLASSIFIER = "classifier"
    CONTEXT = "context"
    OPPORTUNITY = "opportunity"
    RECOMMENDATION = "recommendation"


class FeedbackSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: FeedbackSource
    area: ImprovementArea
    entity_id: UUID | None = None
    entity_key: str
    outcome: str
    score: float
    occurred_at: datetime
    details: dict[str, Any] = Field(default_factory=dict)


class PerformanceMetric(BaseModel):
    model_config = ConfigDict(frozen=True)

    area: ImprovementArea
    entity_key: str
    precision: float
    recall: float
    conversion_rate: float
    average_confidence: float
    average_latency_ms: float
    sample_size: int
    trend: list[dict[str, Any]] = Field(default_factory=list)


class RulePerformanceMetric(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule_key: str
    rule_type: str
    times_fired: int
    correct_decisions: int
    incorrect_decisions: int
    override_rate: float
    confidence: float
    historical_trend: list[dict[str, Any]] = Field(default_factory=list)


class PredictionEvaluation(BaseModel):
    model_config = ConfigDict(frozen=True)

    opportunity_id: UUID
    predicted_score: float
    actual_outcome_score: float
    prediction_error: float
    outcome_label: str


class OptimizationRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    area: ImprovementArea
    target_key: str
    recommendation: str
    reason: str
    expected_impact: float
    confidence: float
    requires_approval: bool = True
    evidence: dict[str, Any] = Field(default_factory=dict)


class ExperimentDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    name: str
    area: ImprovementArea
    variant_a: dict[str, Any]
    variant_b: dict[str, Any]
    hypothesis: str


class ImprovementReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    generated_at: datetime
    overview: dict[str, float | int | str]
    collector_rankings: list[PerformanceMetric]
    rule_rankings: list[RulePerformanceMetric]
    opportunity_accuracy: dict[str, float | int]
    recommendations: list[OptimizationRecommendation]
