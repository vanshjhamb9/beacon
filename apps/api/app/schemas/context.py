from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class BusinessContextResponse(BaseModel):
    id: UUID
    company_id: UUID
    classified_signal_id: UUID
    raw_event_id: UUID
    quality_report_id: UUID
    business_urgency: str
    buying_stage: str
    decision_stage: str
    growth_stage: str
    digital_maturity: float
    ai_readiness: float
    automation_readiness: float
    budget_probability: float
    technology_maturity: float
    expansion_probability: float
    operational_pressure: float
    customer_experience_pressure: float
    support_pressure: float
    engineering_pressure: float
    marketing_pressure: float
    sales_pressure: float
    confidence: float
    evidence: dict[str, Any]
    created_at: datetime


class CompanyContextResponse(BaseModel):
    contexts: list[BusinessContextResponse]


class CompanyDNAResponse(BaseModel):
    id: UUID
    company_id: UUID
    industry: str | None
    business_model: str
    company_stage: str
    growth_pattern: str
    technology_stack: list[str]
    digital_maturity: float
    ai_adoption: float
    automation_adoption: float
    hiring_pattern: str
    expansion_pattern: str
    innovation_score: float
    support_maturity: float
    operational_maturity: float
    technology_maturity: float
    customer_maturity: float
    completeness_score: float
    evidence: dict[str, Any]
    created_at: datetime


class ContextInferenceResponse(BaseModel):
    id: UUID
    company_id: UUID
    business_context_id: UUID
    category: str
    value: str
    confidence: float
    evidence: dict[str, Any]
    created_at: datetime


class ContextInferenceListResponse(BaseModel):
    items: list[ContextInferenceResponse]


class ContextEvidenceResponse(BaseModel):
    id: UUID
    business_context_id: UUID
    evidence_type: str
    reference_id: UUID | None
    reference_key: str | None
    confidence: float
    details: dict[str, Any]
    created_at: datetime


class ContextEvidenceListResponse(BaseModel):
    evidence: list[ContextEvidenceResponse]


class ContextStatisticsResponse(BaseModel):
    statistics: dict[str, Any]


class ContextFeedbackRequest(BaseModel):
    business_context_id: UUID
    reviewer: str = Field(min_length=1, max_length=128)
    review_outcome: str = Field(min_length=1, max_length=64)
    corrected_fields: dict[str, Any] = Field(default_factory=dict)
    ground_truth: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class ContextFeedbackResponse(BaseModel):
    id: UUID
    business_context_id: UUID
    reviewer: str
    review_outcome: str
    corrected_fields: dict[str, Any]
    ground_truth: dict[str, Any]
    notes: str | None
    created_at: datetime
