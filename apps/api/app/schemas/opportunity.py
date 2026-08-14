from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class OpportunityResponse(BaseModel):
    id: UUID
    company_id: UUID
    company_name: str
    status: str
    recommendation: str
    opportunity_score: float
    confidence_score: float
    timing_score: float
    urgency_score: float
    narrative: str
    created_from_context_ids: list[str]
    score_breakdown: dict[str, Any]
    delta: dict[str, Any]
    created_at: datetime


class OpportunitiesResponse(BaseModel):
    opportunities: list[OpportunityResponse]


class OpportunityHistoryResponse(BaseModel):
    id: UUID
    opportunity_id: UUID | None
    company_id: UUID
    action: str
    actor: str
    details: dict[str, Any]
    created_at: datetime


class OpportunityHistoryListResponse(BaseModel):
    history: list[OpportunityHistoryResponse]


class OpportunityEvidenceResponse(BaseModel):
    id: UUID
    opportunity_id: UUID
    company_id: UUID
    source_type: str
    reference_id: UUID
    category: str
    summary: str
    confidence: float
    polarity: str
    weight: float
    details: dict[str, Any]
    created_at: datetime


class OpportunityEvidenceListResponse(BaseModel):
    evidence: list[OpportunityEvidenceResponse]


class OpportunityTimelineResponse(BaseModel):
    id: UUID
    opportunity_id: UUID
    company_id: UUID
    event_type: str
    summary: str
    reference_id: UUID | None
    details: dict[str, Any]
    created_at: datetime


class OpportunityTimelineListResponse(BaseModel):
    timeline: list[OpportunityTimelineResponse]


class OpportunityRecommendationResponse(BaseModel):
    id: UUID
    opportunity_id: UUID
    company_id: UUID
    action: str
    confidence: float
    reasons: list[str]
    next_step: str
    created_at: datetime


class OpportunityStatisticsResponse(BaseModel):
    statistics: dict[str, Any]


class OpportunityFeedbackRequest(BaseModel):
    opportunity_id: UUID
    reviewer: str = Field(min_length=1, max_length=128)
    review_outcome: str = Field(min_length=1, max_length=64)
    corrected_fields: dict[str, Any] = Field(default_factory=dict)
    outcome_label: str | None = None
    notes: str | None = None


class OpportunityFeedbackResponse(BaseModel):
    id: UUID
    opportunity_id: UUID
    reviewer: str
    review_outcome: str
    corrected_fields: dict[str, Any]
    outcome_label: str | None
    notes: str | None
    created_at: datetime
