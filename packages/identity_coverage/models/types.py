"""ICE v1 types — identity coverage evidence only; never fabricate."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

UNKNOWN = "unknown"
SCORING_VERSION = "ice-v1"


class ProviderAction(StrEnum):
    KEEP = "KEEP"
    LIMIT = "LIMIT"
    DISABLE = "DISABLE"


class RecoveryReason(StrEnum):
    WEBSITE_MISSING = "Website Missing"
    HOMEPAGE_MISSING = "Homepage Missing"
    LOW_CONFIDENCE = "Low Confidence"
    ALIAS_CONFLICT = "Alias Conflict"
    NO_CONTACT = "No Contact"
    NO_DECISION_MAKER = "No Decision Maker"


class CoverageEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    field: str
    value: str
    confidence: float = 0.0
    collector: str = UNKNOWN
    timestamp: datetime | str | None = None
    verification: bool = False
    source: str = UNKNOWN
    priority: int = 50
    reason: str = ""
    evidence: list[str] = Field(default_factory=list)


class RankedField(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: str = UNKNOWN
    source: str = UNKNOWN
    collector: str = UNKNOWN
    confidence: float = 0.0
    verified: bool = False
    collected_at: datetime | str | None = None
    last_verified: datetime | str | None = None
    evidence_count: int = 0


class AliasNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    primary_name: str
    aliases: list[str] = Field(default_factory=list)
    official_domain: str | None = None
    merge_evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    reason: str = ""


class CollectorKpis(BaseModel):
    model_config = ConfigDict(frozen=True)

    collector: str
    signals: int = 0
    candidates: int = 0
    companies: int = 0
    official_websites: int = 0
    business_emails: int = 0
    decision_makers: int = 0
    sales_ready: int = 0
    revenue_ready: int = 0
    duplicate_rate: float = 0.0
    identity_precision: float = 0.0
    identity_recall: float = 0.0
    average_confidence: float = 0.0
    recommendation: ProviderAction = ProviderAction.KEEP


class FunnelStage(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    count: int = 0
    conversion_pct: float = 0.0
    drop_pct: float = 0.0
    reasons: list[str] = Field(default_factory=list)


class CoverageFunnel(BaseModel):
    model_config = ConfigDict(frozen=True)

    stages: list[FunnelStage] = Field(default_factory=list)
    scoring_version: str = SCORING_VERSION


class RecoveryItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    company_id: str | None = None
    reason: RecoveryReason
    domain: str | None = None
    attempts: int = 0
    payload: dict[str, Any] = Field(default_factory=dict)


class BusinessImpact(BaseModel):
    model_config = ConfigDict(frozen=True)

    revenue_ready: int = 0
    emails_ready: int = 0
    decision_makers_ready: int = 0
    meetings_possible: int = 0
    pipeline_value: str = "$0"
    revenue_yield: float = 0.0


class IceSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    source: str
    evidence: list[CoverageEvidence] = Field(default_factory=list)
    ranked: dict[str, RankedField] = Field(default_factory=dict)
    alias: AliasNode | None = None
    website: str | None = None
    domain: str | None = None
    recovery: list[RecoveryReason] = Field(default_factory=list)
    admitted_hint: bool = False
    scoring_version: str = SCORING_VERSION
    payload: dict[str, Any] = Field(default_factory=dict)


class IceAuditReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] = Field(default_factory=dict)
    funnel: CoverageFunnel = Field(default_factory=CoverageFunnel)
    collectors: list[CollectorKpis] = Field(default_factory=list)
    recovery_success_rate: float = 0.0
    coverage_pct: float = 0.0
    duplicate_pct: float = 0.0
    top_rejections: dict[str, int] = Field(default_factory=dict)
    business_impact: BusinessImpact = Field(default_factory=BusinessImpact)
    top_revenue_ready: list[dict[str, Any]] = Field(default_factory=list)
    vansh_ready_answer: str = "NO"
    scoring_version: str = SCORING_VERSION
