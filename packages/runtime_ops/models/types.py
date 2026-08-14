from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AlertSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class HealthTone(StrEnum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    UNKNOWN = "unknown"


class OperationalAlert(BaseModel):
    code: str
    severity: AlertSeverity
    cause: str
    evidence: list[str] = Field(default_factory=list)
    recommended_fix: str


class ComponentStatus(BaseModel):
    name: str
    status: HealthTone
    detail: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class RedisValidationResult(BaseModel):
    ok: bool
    version: str | None = None
    major: int | None = None
    streams_ok: bool = False
    consumer_groups_ok: bool = False
    pubsub_ok: bool = False
    latency_ms: float | None = None
    errors: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class MigrationValidationResult(BaseModel):
    ok: bool
    current_revision: str | None = None
    head_revision: str
    pending_revisions: list[str] = Field(default_factory=list)
    missing_tables: list[str] = Field(default_factory=list)
    present_tables: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class PipelineStageStatus(BaseModel):
    stage: str
    input_count: int = 0
    output_count: int = 0
    dropped_count: int = 0
    success_percent: float = 0.0
    average_time_ms: float | None = None
    last_run_at: datetime | None = None
    worker_task: str | None = None
    failures: int = 0
    retry_count: int = 0
    status: HealthTone = HealthTone.UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class CeleryRuntimeStatus(BaseModel):
    worker_online: bool = False
    beat_online: bool = False
    broker_ok: bool = False
    active_tasks: int = 0
    scheduled_tasks: int = 0
    registered_task_count: int = 0
    queue_depth: int = 0
    worker_memory_mb: float | None = None
    worker_cpu_percent: float | None = None
    last_heartbeat_at: datetime | None = None
    evidence: list[str] = Field(default_factory=list)


class ProductionGateDecision(BaseModel):
    allow_production: bool
    score: float
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    checked_at: datetime


class RuntimeOpsSnapshot(BaseModel):
    generated_at: datetime
    scoring_version: str = "runtime-ops-v1"
    infrastructure: list[ComponentStatus] = Field(default_factory=list)
    redis: RedisValidationResult
    migrations: MigrationValidationResult
    celery: CeleryRuntimeStatus
    pipeline: list[PipelineStageStatus] = Field(default_factory=list)
    collectors: list[dict[str, Any]] = Field(default_factory=list)
    enrichment: dict[str, Any] = Field(default_factory=dict)
    freshness: dict[str, Any] = Field(default_factory=dict)
    alerts: list[OperationalAlert] = Field(default_factory=list)
    production_gate: ProductionGateDecision
    readiness_score: float = 0.0
