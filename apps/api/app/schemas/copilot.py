from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class QualityScoresResponse(BaseModel):
    personalization: float
    evidence_coverage: float
    readability: float
    professional_tone: float
    length: float
    call_to_action: float
    confidence: float
    overall: float


class SectionResponse(BaseModel):
    key: str
    title: str
    content: str
    attribution: dict[str, Any] = Field(default_factory=dict)


class DraftResponse(BaseModel):
    id: UUID | None = None
    kind: str
    style: str
    title: str
    body: str
    subject_lines: list[str] = Field(default_factory=list)
    attribution: dict[str, Any] = Field(default_factory=dict)


class StyleVariantResponse(BaseModel):
    style: str
    drafts: list[DraftResponse] = Field(default_factory=list)


class GenerationMetaResponse(BaseModel):
    prompt_version: str
    llm_provider: str
    llm_model: str
    temperature: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    generation_time_ms: float
    cost_estimate_usd: float


class SalesPackageResponse(BaseModel):
    id: UUID
    company_id: UUID
    opportunity_id: UUID
    company_name: str
    opportunity_score: float
    recommended_service: str
    business_pain: str
    version: int
    review_status: str
    is_favorite: bool
    sections: list[SectionResponse] = Field(default_factory=list)
    style_variants: list[StyleVariantResponse] = Field(default_factory=list)
    drafts: list[DraftResponse] = Field(default_factory=list)
    evidence_chain: list[dict[str, Any]] = Field(default_factory=list)
    quality: QualityScoresResponse
    generation: GenerationMetaResponse
    package_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SalesPackageHistoryItem(BaseModel):
    id: UUID
    company_id: UUID
    opportunity_id: UUID
    version: int
    review_status: str
    is_favorite: bool
    prompt_version: str
    llm_provider: str
    llm_model: str
    quality_overall: float
    created_at: datetime


class SalesPackageHistoryResponse(BaseModel):
    results: list[SalesPackageHistoryItem]


class GenerateResponse(BaseModel):
    generated: bool
    package: SalesPackageResponse | None = None


class ReviewRequestBody(BaseModel):
    action: str
    reviewer: str = "operator"
    notes: str = ""
    rating: float | None = Field(default=None, ge=0.0, le=5.0)


class ReviewResponse(BaseModel):
    reviewed: bool
    package: SalesPackageResponse | None = None
