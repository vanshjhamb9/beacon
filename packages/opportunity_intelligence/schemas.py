"""Pydantic contracts for Opportunity Intelligence."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from opportunity_intelligence.enums import BuyingWindow, FreshnessBucket, OpportunityStatus, SignalCategory


class ImmutableModel(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)


class CompanyInput(ImmutableModel):
    id: UUID
    name: str = Field(min_length=1, max_length=255)
    website: str | None = None
    industry: str | None = None
    country: str | None = None
    icp_score: float | None = Field(default=None, ge=0, le=100)


class SignalInput(ImmutableModel):
    type: str = Field(min_length=1, max_length=128)
    source: str = Field(min_length=1, max_length=128)
    category: SignalCategory
    title: str = Field(min_length=1, max_length=255)
    summary: str = Field(default="", max_length=4000)
    url: HttpUrl | str | None = None
    timestamp: datetime


class EvidenceInput(ImmutableModel):
    provider: str = Field(min_length=1, max_length=128)
    source_type: str = Field(min_length=1, max_length=128)
    url: HttpUrl | str | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=4000)
    captured_at: datetime
    trust: float = Field(default=50, ge=0, le=100)
    confidence: float = Field(default=50, ge=0, le=100)


class FreshnessResult(ImmutableModel):
    score: float
    age_days: int
    bucket: FreshnessBucket


class ScoreResult(ImmutableModel):
    score: float
    breakdown: dict[str, float]
    weighted_breakdown: dict[str, float]
    reasons: list[str]
    version: str


class Recommendation(ImmutableModel):
    why_contact: str
    why_now: str
    supporting_evidence: list[str]
    buying_window: BuyingWindow
    score_breakdown: dict[str, float]


class OpportunityResponse(ImmutableModel):
    id: UUID
    company_id: UUID
    company_name: str
    website: str | None = None
    industry: str | None = None
    country: str | None = None
    signal_type: str
    signal_source: str
    signal_category: SignalCategory | str
    signal_title: str
    signal_summary: str = ""
    signal_url: str | None = None
    signal_timestamp: datetime
    signal_age_days: int
    buying_window: BuyingWindow | str
    intent_score: float
    pain_score: float
    budget_score: float
    growth_score: float
    timing_score: float
    freshness_score: float
    evidence_score: float
    icp_score: float
    opportunity_score: float
    confidence: float
    trust: float
    status: OpportunityStatus | str = OpportunityStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
