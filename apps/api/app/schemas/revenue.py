from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class RevenueCompanySummary(BaseModel):
    id: UUID
    name: str
    industry: str | None = None


class RevenueBuyerPersonaResponse(BaseModel):
    persona: str
    confidence: float
    explanation: str


class RevenuePlaybookResponse(BaseModel):
    business_pain: str
    recommended_service: str
    why: str
    conversation_angle: str
    decision_maker: str
    expected_outcome: str
    risk: str


class RevenueOpportunityItemResponse(BaseModel):
    company: RevenueCompanySummary
    opportunity_id: UUID
    solution_match_id: UUID
    opportunity_score: float
    business_pain: str | None
    recommended_service: str
    secondary_service: str | None
    buyer_persona: RevenueBuyerPersonaResponse | None
    buyer_personas: list[RevenueBuyerPersonaResponse]
    estimated_budget_range: str | None
    project_size: str | None
    implementation_complexity: str | None
    priority: str | None
    confidence: float
    evidence: dict[str, Any]
    reason: str
    playbook: RevenuePlaybookResponse | None
    created_at: datetime


class RevenueOpportunitiesResponse(BaseModel):
    opportunities: list[RevenueOpportunityItemResponse]


class RevenueCompanyResponse(BaseModel):
    company: RevenueCompanySummary
    opportunity_id: UUID
    solution_match_id: UUID
    opportunity_score: float
    business_pain: str | None
    recommended_service: str
    secondary_service: str | None
    buyer_persona: RevenueBuyerPersonaResponse | None
    buyer_personas: list[RevenueBuyerPersonaResponse]
    estimated_budget_range: str | None
    project_size: str | None
    implementation_complexity: str | None
    priority: str | None
    confidence: float
    evidence: dict[str, Any]
    reason: str
    playbook: RevenuePlaybookResponse | None
    created_at: datetime


class RevenuePlaybookDetailResponse(BaseModel):
    company_id: UUID
    opportunity_id: UUID
    solution_match_id: UUID
    business_pain: str
    recommended_service: str
    why: str
    conversation_angle: str
    decision_maker: str
    expected_outcome: str
    risk: str
    created_at: datetime


class RevenueStatisticsResponse(BaseModel):
    statistics: dict[str, Any]
