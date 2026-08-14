from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OutcomeLifecycle(StrEnum):
    NEW = "new"
    REVIEWED = "reviewed"
    CONTACTED = "contacted"
    REPLIED = "replied"
    MEETING_SCHEDULED = "meeting_scheduled"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    ARCHIVED = "archived"


class OutcomeUpdateInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    opportunity_id: UUID
    company_id: UUID | None = None
    lifecycle_stage: OutcomeLifecycle
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


class FunnelStageMetric(BaseModel):
    model_config = ConfigDict(frozen=True)

    stage: str
    count: int
    conversion_from_previous: float


class RateMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

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


class RevenueMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_revenue: float
    average_deal_size: float
    average_sales_cycle_days: float
    open_pipeline_value: float
    won_deals: int


class DimensionRevenue(BaseModel):
    model_config = ConfigDict(frozen=True)

    dimension: str
    key: str
    revenue: float
    deals: int
    average_deal_size: float
    win_rate: float


class AccuracyMetric(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: str
    key: str
    sample_size: int
    accuracy_score: float
    precision: float
    recall: float
    average_prediction_error: float
    details: dict[str, Any] = Field(default_factory=dict)


class LearningRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    area: str
    target_key: str
    recommendation: str
    reason: str
    expected_impact: float
    confidence: float
    requires_approval: bool = True
    evidence: dict[str, Any] = Field(default_factory=dict)


class OutcomeDashboard(BaseModel):
    model_config = ConfigDict(frozen=True)

    generated_at: datetime
    funnel: list[FunnelStageMetric]
    rates: RateMetrics
    revenue: RevenueMetrics
    revenue_by_collector: list[DimensionRevenue]
    revenue_by_industry: list[DimensionRevenue]
    revenue_by_service: list[DimensionRevenue]
    revenue_by_persona: list[DimensionRevenue]
    revenue_by_technology: list[DimensionRevenue]
    prediction_accuracy: list[AccuracyMetric]
    service_accuracy: list[AccuracyMetric]
    collector_accuracy: list[AccuracyMetric]
    persona_accuracy: list[AccuracyMetric]
    industry_accuracy: list[AccuracyMetric]
    roi: dict[str, float | int]
    learning_recommendations: list[LearningRecommendation]


class CompanyOutcomeReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    outcomes: list[dict[str, Any]]
    contact_attempts: list[dict[str, Any]]
    meetings: list[dict[str, Any]]
    proposals: list[dict[str, Any]]
    deals: list[dict[str, Any]]
    feedback: list[dict[str, Any]]
    totals: dict[str, float | int]


class OutcomeAnalytics(BaseModel):
    model_config = ConfigDict(frozen=True)

    generated_at: datetime
    rates: RateMetrics
    revenue: RevenueMetrics
    funnel: list[FunnelStageMetric]
    accuracy_summary: dict[str, float | int]
    top_services: list[DimensionRevenue]
    top_collectors: list[DimensionRevenue]
    top_industries: list[DimensionRevenue]
    learning_recommendations: list[LearningRecommendation]
