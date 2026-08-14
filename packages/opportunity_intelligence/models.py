"""Immutable domain models for Opportunity Intelligence."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import Field

from opportunity_intelligence.enums import BuyingWindow, OpportunityStatus, SignalCategory
from opportunity_intelligence.schemas import ImmutableModel


class OpportunityEvidence(ImmutableModel):
    id: UUID = Field(default_factory=uuid4)
    opportunity_id: UUID
    provider: str
    source_type: str
    url: str | None = None
    title: str
    description: str = ""
    captured_at: datetime
    trust: float
    confidence: float


class OpportunityScoreRecord(ImmutableModel):
    id: UUID = Field(default_factory=uuid4)
    opportunity_id: UUID
    intent: float
    budget: float
    growth: float
    timing: float
    pain: float
    freshness: float
    evidence: float
    icp: float
    final_score: float
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Opportunity(ImmutableModel):
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID
    company_name: str
    website: str | None = None
    industry: str | None = None
    country: str | None = None
    signal_type: str
    signal_source: str
    signal_category: SignalCategory
    signal_title: str
    signal_summary: str = ""
    signal_url: str | None = None
    signal_timestamp: datetime
    signal_age_days: int
    buying_window: BuyingWindow
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
    status: OpportunityStatus = OpportunityStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    evidence: tuple[OpportunityEvidence, ...] = Field(default_factory=tuple)
    score_record: OpportunityScoreRecord | None = None
    reasons: tuple[str, ...] = Field(default_factory=tuple)
    dedupe_key: str
