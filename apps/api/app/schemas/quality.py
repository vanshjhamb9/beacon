from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class QualityMetricResponse(BaseModel):
    id: UUID
    stage: str
    metric_name: str
    metric_value: float
    passed: bool
    duration_ms: float
    reason_codes: list[str]
    details: dict[str, Any]


class QualityReportResponse(BaseModel):
    id: UUID
    raw_event_id: UUID
    source: str
    decision: str
    grade: str
    schema_score: float
    spam_score: float
    trust_score: float
    freshness_score: float
    completeness_score: float
    entity_confidence_score: float
    duplicate_probability: float
    overall_quality_score: float
    processing_time_ms: float
    queue_time_ms: float | None
    reason_codes: list[str]
    explanation: dict[str, Any]
    created_at: datetime
    metrics: list[QualityMetricResponse] = Field(default_factory=list)


class QualityEventsResponse(BaseModel):
    events: list[QualityReportResponse]


class QualityRulesResponse(BaseModel):
    rules: list[dict[str, Any]]


class QualityStatisticsResponse(BaseModel):
    statistics: dict[str, Any]


class QualitySourcesResponse(BaseModel):
    sources: list[dict[str, Any]]


class QualityDashboardResponse(BaseModel):
    dashboard: dict[str, Any]


class QualityReviewRequest(BaseModel):
    quality_report_id: UUID
    reviewer: str = Field(min_length=1, max_length=128)
    review_outcome: str = Field(min_length=1, max_length=64)
    corrected_decision: str | None = None
    corrected_reason_codes: list[str] = Field(default_factory=list)
    notes: str | None = None


class QualityReviewResponse(BaseModel):
    id: UUID
    quality_report_id: UUID
    raw_event_id: UUID
    reviewer: str
    review_outcome: str
    corrected_decision: str | None
    corrected_reason_codes: list[str]
    notes: str | None
    created_at: datetime
