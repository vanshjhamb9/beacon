"""ODU types — acquisition quality only. Never fabricate."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SCORING_VERSION = "odu-v1"
UNKNOWN = "unknown"


class ConnectorHealthStatus(StrEnum):
    HEALTHY = "Healthy"
    RATE_LIMITED = "Rate Limited"
    MISSING_TOKEN = "Missing Token"
    BLOCKED = "Blocked"
    DISABLED = "Disabled"
    CLOUDFLARE = "Cloudflare"


class ConnectorMetric(BaseModel):
    model_config = ConfigDict(frozen=True)

    connector: str
    signals: int = 0
    websites: int = 0
    companies: int = 0
    emails: int = 0
    decision_makers: int = 0
    sales_ready: int = 0
    revenue_ready: int = 0
    yield_pct: float = 0.0
    duplicates: int = 0
    health: ConnectorHealthStatus = ConnectorHealthStatus.HEALTHY
    note: str = ""


class OduAudit(BaseModel):
    model_config = ConfigDict(frozen=True)

    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] = Field(default_factory=dict)
    connectors: list[ConnectorMetric] = Field(default_factory=list)
    top_failures: dict[str, int] = Field(default_factory=dict)
    top_companies: list[dict[str, Any]] = Field(default_factory=list)
    websites_recovered: int = 0
    emails_recovered: int = 0
    dms_recovered: int = 0
    sales_ready_delta: int = 0
    revenue_ready_delta: int = 0
    highest_yield_connector: str = UNKNOWN
    disable_connectors: list[str] = Field(default_factory=list)
    vansh_ready_answer: str = "NO"
    scoring_version: str = SCORING_VERSION
