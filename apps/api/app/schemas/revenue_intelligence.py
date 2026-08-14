from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RevenueIntelligenceResponse(BaseModel):
    id: str
    ecommerce_lead_id: str
    company_name: str
    website: str
    domain: str
    platform: str
    category: str
    country: str
    pain_score: float
    pain_signals: list = Field(default_factory=list)
    growth_score: float
    growth_signals: list = Field(default_factory=list)
    buying_intent: float
    intent_signals: list = Field(default_factory=list)
    technology_gap: float
    tech_gaps: list = Field(default_factory=list)
    support_gap: float
    support_gaps: list = Field(default_factory=list)
    icp_match: bool
    icp_score: float
    icp_reasons: list = Field(default_factory=list)
    rejection_reasons: list = Field(default_factory=list)
    revenue_potential: float
    probability_to_buy: float
    probability_reasons: list = Field(default_factory=list)
    why_comai: str
    recommended_pitch: str
    priority: str
    traffic_score: float
    review_score: float
    social_growth: float
    whatsapp_score: float
    founder_score: float
    evidence_json: list = Field(default_factory=list)
    product_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v: Any) -> str:
        return str(v) if v is not None else ""


class RevenueIntelligenceListResponse(BaseModel):
    leads: list[RevenueIntelligenceResponse]
    total: int
    page: int
    page_size: int


class RevenueDashboardResponse(BaseModel):
    total_analyzed: int
    hot_leads: int
    warm_leads: int
    low_leads: int
    rejected: int
    avg_probability: float
    avg_pain_score: float
    avg_growth_score: int = 0
    top_buyers: list[dict[str, Any]] = Field(default_factory=list)
    top_pain: list[dict[str, Any]] = Field(default_factory=list)
    fastest_growing: list[dict[str, Any]] = Field(default_factory=list)
    platforms: dict[str, int] = Field(default_factory=dict)
    categories: dict[str, int] = Field(default_factory=dict)


class RevenueAnalyzeRequest(BaseModel):
    limit: int = 500
    country: str = "India"


class RevenueAnalyzeResponse(BaseModel):
    status: str
    message: str
    processed: int = 0
