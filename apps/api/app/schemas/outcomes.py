from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OutcomeUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_id: UUID
    company_id: UUID | None = None
    lifecycle_stage: str
    notes: str | None = None
    reason: str | None = None
    owner: str | None = None
    revenue: float | None = None
    close_date: datetime | None = None
    contacted_at: datetime | None = None
    replied_at: datetime | None = None
    meeting_at: datetime | None = None
    proposal_at: datetime | None = None
    channel: str | None = None
    meeting_type: str | None = None
    proposal_value: float | None = None
    deal_value: float | None = None
    feedback_score: float | None = None
    feedback_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor: str = "operator"


class OutcomeUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    opportunity_id: UUID
    company_id: UUID
    lifecycle_stage: str
    notes: str | None = None
    reason: str | None = None
    owner: str | None = None
    revenue: float | None = None
    close_date: datetime | None = None
    opportunity_score: float
    recommended_service: str | None = None
    buyer_persona: str | None = None
    industry: str | None = None
    collector: str | None = None
    technology: str | None = None
    decision_maker_role: str | None = None
    created_at: datetime
    updated_at: datetime


class FunnelStageResponse(BaseModel):
    stage: str
    count: int
    conversion_from_previous: float


class RateMetricsResponse(BaseModel):
    meeting_rate: float
    reply_rate: float
    proposal_rate: float
    close_rate: float
    contacted_count: int
    replied_count: int
    meeting_count: int
    proposal_count: int
    won_count: int
    lost_count: int
    total_opportunities: int


class RevenueMetricsResponse(BaseModel):
    total_revenue: float
    average_deal_size: float
    average_sales_cycle_days: float
    open_pipeline_value: float
    won_deals: int


class DimensionRevenueResponse(BaseModel):
    dimension: str
    key: str
    revenue: float
    deals: int
    average_deal_size: float
    win_rate: float


class AccuracyMetricResponse(BaseModel):
    category: str
    key: str
    sample_size: int
    accuracy_score: float
    precision: float
    recall: float
    average_prediction_error: float
    details: dict[str, Any] = Field(default_factory=dict)


class LearningRecommendationResponse(BaseModel):
    area: str
    target_key: str
    recommendation: str
    reason: str
    expected_impact: float
    confidence: float
    requires_approval: bool
    evidence: dict[str, Any] = Field(default_factory=dict)


class OutcomeDashboardResponse(BaseModel):
    generated_at: datetime
    funnel: list[FunnelStageResponse]
    rates: RateMetricsResponse
    revenue: RevenueMetricsResponse
    revenue_by_collector: list[DimensionRevenueResponse]
    revenue_by_industry: list[DimensionRevenueResponse]
    revenue_by_service: list[DimensionRevenueResponse]
    revenue_by_persona: list[DimensionRevenueResponse]
    revenue_by_technology: list[DimensionRevenueResponse]
    prediction_accuracy: list[AccuracyMetricResponse]
    service_accuracy: list[AccuracyMetricResponse]
    collector_accuracy: list[AccuracyMetricResponse]
    persona_accuracy: list[AccuracyMetricResponse]
    industry_accuracy: list[AccuracyMetricResponse]
    roi: dict[str, float | int]
    learning_recommendations: list[LearningRecommendationResponse]


class CompanyOutcomeResponse(BaseModel):
    company_id: UUID
    company_name: str
    outcomes: list[dict[str, Any]]
    contact_attempts: list[dict[str, Any]]
    meetings: list[dict[str, Any]]
    proposals: list[dict[str, Any]]
    deals: list[dict[str, Any]]
    feedback: list[dict[str, Any]]
    totals: dict[str, float | int]


class OutcomeAnalyticsResponse(BaseModel):
    generated_at: datetime
    rates: RateMetricsResponse
    revenue: RevenueMetricsResponse
    funnel: list[FunnelStageResponse]
    accuracy_summary: dict[str, float | int]
    top_services: list[DimensionRevenueResponse]
    top_collectors: list[DimensionRevenueResponse]
    top_industries: list[DimensionRevenueResponse]
    learning_recommendations: list[LearningRecommendationResponse]
