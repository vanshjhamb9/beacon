"""RDAP v1 — revenue data acquisition types. Never fabricate."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

UNKNOWN = "unknown"
SCORING_VERSION = "rdap-v1"


class SourceClass(StrEnum):
    IDENTITY = "IDENTITY"
    CONTACT = "CONTACT"
    INTENT = "INTENT"
    TECH = "TECH"
    HIRING = "HIRING"
    FUNDING = "FUNDING"
    COMMUNITY = "COMMUNITY"
    REVIEWS = "REVIEWS"
    NEWS = "NEWS"
    SOCIAL = "SOCIAL"


class ConnectorGrade(StrEnum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    AVERAGE = "Average"
    POOR = "Poor"
    DISABLED = "Disabled"


class RecoveryReason(StrEnum):
    WEBSITE_MISSING = "Website Missing"
    EMAIL_MISSING = "Email Missing"
    DECISION_MAKER_MISSING = "Decision Maker Missing"
    LOW_CONFIDENCE = "Low Confidence"
    ALIAS_CONFLICT = "Alias Conflict"
    IDENTITY_CONFLICT = "Identity Conflict"
    NO_BUYING_INTENT = "No Buying Intent"
    LOW_TRUST = "Low Trust"
    DUPLICATE = "Duplicate"


class AttributedValue(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: str
    source: str = UNKNOWN
    collector: str = UNKNOWN
    confidence: float = 0.0
    verified: bool = False
    verified_at: datetime | str | None = None
    evidence: list[str] = Field(default_factory=list)


class ConnectorScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    connector: str
    grade: ConnectorGrade = ConnectorGrade.AVERAGE
    signals: int = 0
    candidates: int = 0
    verified_companies: int = 0
    official_websites: int = 0
    business_emails: int = 0
    decision_makers: int = 0
    sales_ready: int = 0
    revenue_ready: int = 0
    duplicate_pct: float = 0.0
    website_recovery_pct: float = 0.0
    email_recovery_pct: float = 0.0
    dm_recovery_pct: float = 0.0
    average_confidence: float = 0.0
    revenue_yield: float = 0.0
    roles: list[SourceClass] = Field(default_factory=list)


class FunnelStage(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    count: int = 0
    conversion_pct: float = 0.0


class RevenueYield(BaseModel):
    model_config = ConfigDict(frozen=True)

    connector: str
    signals: int = 0
    websites: int = 0
    companies: int = 0
    emails: int = 0
    decision_makers: int = 0
    revenue_ready: int = 0
    yield_pct: float = 0.0


class CompanyDossier(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: str | None = None
    identity: dict[str, Any] = Field(default_factory=dict)
    website: AttributedValue | None = None
    business: dict[str, Any] = Field(default_factory=dict)
    buying_signals: list[str] = Field(default_factory=list)
    technology: list[str] = Field(default_factory=list)
    contacts: list[AttributedValue] = Field(default_factory=list)
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    service_match: str | None = None
    evidence_timeline: list[str] = Field(default_factory=list)
    trust_score: float = 0.0
    sales_ready: bool = False
    revenue_ready: bool = False


class RdapSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    source: str
    roles: list[SourceClass] = Field(default_factory=list)
    can_create_identity: bool = False
    website: str | None = None
    domain: str | None = None
    emails: list[AttributedValue] = Field(default_factory=list)
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    dossier: CompanyDossier | None = None
    recovery: list[RecoveryReason] = Field(default_factory=list)
    confidence: float = 0.0
    scoring_version: str = SCORING_VERSION
    payload: dict[str, Any] = Field(default_factory=dict)


class RdapAudit(BaseModel):
    model_config = ConfigDict(frozen=True)

    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] = Field(default_factory=dict)
    funnel: list[FunnelStage] = Field(default_factory=list)
    connectors: list[ConnectorScore] = Field(default_factory=list)
    yields: list[RevenueYield] = Field(default_factory=list)
    top_rejections: dict[str, int] = Field(default_factory=dict)
    top_revenue_ready: list[dict[str, Any]] = Field(default_factory=list)
    vansh_ready_answer: str = "NO"
    scoring_version: str = SCORING_VERSION
