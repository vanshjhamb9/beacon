from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ImprovementOverviewResponse(BaseModel):
    overview: dict[str, Any]


class CollectorPerformanceResponse(BaseModel):
    id: UUID
    collector: str
    precision: float
    recall: float
    spam_rate: float
    duplicate_rate: float
    conversion_rate: float
    average_quality: float
    average_confidence: float
    latency_ms: float
    ranking: int
    details: dict[str, Any]
    created_at: datetime


class CollectorPerformanceListResponse(BaseModel):
    collectors: list[CollectorPerformanceResponse]


class RulePerformanceResponse(BaseModel):
    id: UUID
    rule_key: str
    times_fired: int
    correct_decisions: int
    incorrect_decisions: int
    override_rate: float
    confidence: float
    historical_trend: list[dict[str, Any]]
    created_at: datetime


class RulePerformanceListResponse(BaseModel):
    rules: list[RulePerformanceResponse]


class OpportunityAccuracyResponse(BaseModel):
    id: UUID
    opportunity_id: UUID | None
    predicted_score: float
    actual_outcome_score: float
    prediction_error: float
    outcome_label: str
    created_at: datetime


class OpportunityAccuracyListResponse(BaseModel):
    opportunities: list[OpportunityAccuracyResponse]


class ExperimentRunResponse(BaseModel):
    id: UUID
    experiment_key: str
    name: str
    area: str
    variant_a: dict[str, Any]
    variant_b: dict[str, Any]
    hypothesis: str
    status: str
    created_at: datetime


class ExperimentListResponse(BaseModel):
    experiments: list[ExperimentRunResponse]


class OptimizationRecommendationResponse(BaseModel):
    id: UUID
    target_type: str
    target_key: str
    current_weight: float | None
    recommended_weight: float | None
    recommendation: str
    reason: str
    confidence: float
    requires_approval: str
    created_at: datetime


class OptimizationRecommendationListResponse(BaseModel):
    recommendations: list[OptimizationRecommendationResponse]
