from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class PhaseStatus(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


class CollectionSourceRow(BaseModel):
    source: str
    status: str
    today_collected: int = 0
    today_emitted: int = 0
    today_duplicates: int = 0
    today_failed_runs: int = 0
    today_runs: int = 0
    qualified_estimate: int = 0
    rejected_estimate: int = 0
    reject_reasons: list[str] = Field(default_factory=list)
    avg_quality_score: float | None = None
    avg_intent_score: float | None = None
    duplicate_rate: float = 0.0
    freshness_minutes: float | None = None
    last_successful_run: datetime | str | None = None
    error_rate: float = 0.0
    avg_latency_ms: float | None = None
    last_error: str | None = None
    evidence: list[str] = Field(default_factory=list)


class OpportunityAuditRow(BaseModel):
    opportunity_id: str
    company_id: str
    company_name: str
    explainable: bool
    hide: bool
    why_collected: str | None = None
    why_interesting: str | None = None
    why_now: str | None = None
    evidence_count: int = 0
    source: str | None = None
    collector: str | None = None
    collected_at: datetime | str | None = None
    rules_matched: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)


class MetricTarget(BaseModel):
    name: str
    target: float
    actual: float | None = None
    unit: str = "%"
    hit: bool = False
    evidence: list[str] = Field(default_factory=list)


class PhaseResult(BaseModel):
    phase: str
    title: str
    status: PhaseStatus
    summary: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class MilestoneReport(BaseModel):
    scoring_version: str = "m1-v1"
    generated_at: datetime | str | None = None
    north_star: str = (
        "If 100 real companies enter Beacon today, how many become high-confidence, "
        "outreach-ready accounts you would personally contact?"
    )
    estimated_qualified_per_100: float | None = None
    phases: list[PhaseResult] = Field(default_factory=list)
    success_metrics: list[MetricTarget] = Field(default_factory=list)
    production_allowed: bool = False
    overall_status: PhaseStatus = PhaseStatus.FAIL
    recommendations: list[str] = Field(default_factory=list)
