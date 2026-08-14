from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RuntimeOpsResponse(BaseModel):
    generated_at: datetime
    scoring_version: str
    infrastructure: list[dict[str, Any]] = Field(default_factory=list)
    redis: dict[str, Any]
    migrations: dict[str, Any]
    celery: dict[str, Any]
    pipeline: list[dict[str, Any]] = Field(default_factory=list)
    collectors: list[dict[str, Any]] = Field(default_factory=list)
    enrichment: dict[str, Any] = Field(default_factory=dict)
    freshness: dict[str, Any] = Field(default_factory=dict)
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    production_gate: dict[str, Any]
    readiness_score: float


class RuntimeOpsReportsResponse(BaseModel):
    generated_at: datetime
    reports: dict[str, str]
