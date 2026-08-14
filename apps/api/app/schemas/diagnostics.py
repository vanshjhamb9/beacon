from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CollectorDiagnostic(BaseModel):
    source: str
    enabled: bool
    health_status: str
    consecutive_failures: int
    average_latency_ms: float | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_error: str | None = None
    last_run_at: datetime | None = None
    last_run_success: bool | None = None
    last_collected: int | None = None
    last_emitted: int | None = None
    signals_24h: int = 0


class QueueDiagnostic(BaseModel):
    name: str
    length: int
    detail: str | None = None


class DatabaseCounts(BaseModel):
    raw_events: int
    raw_events_1h: int
    raw_events_24h: int
    raw_events_7d: int
    quality_reports: int
    quality_accepted: int
    quality_review: int
    quality_rejected: int
    companies: int
    classified_signals: int
    business_contexts: int
    opportunities: int
    solution_matches: int
    enrichment_reports: int
    verification_reports: int
    collector_runs: int
    knowledge_graph_nodes: int


class StageFunnel(BaseModel):
    stage: str
    entering: int
    leaving: int
    drop_off_percent: float
    notes: str | None = None


class WorkerDiagnostic(BaseModel):
    redis_reachable: bool
    celery_queue_length: int
    raw_event_stream_length: int
    scheduler_status: str
    worker_status: str
    detail: str | None = None


class DiagnosticsResponse(BaseModel):
    generated_at: datetime
    collectors: list[CollectorDiagnostic]
    queues: list[QueueDiagnostic]
    database: DatabaseCounts
    funnel: list[StageFunnel]
    worker: WorkerDiagnostic
    last_successful_collection: datetime | None = None
    last_processed_opportunity: datetime | None = None
    last_error: str | None = None
    top_failing_connectors: list[str] = Field(default_factory=list)
    missing_env: list[str] = Field(default_factory=list)
    quality_reason_breakdown: dict[str, int] = Field(default_factory=dict)
    average_quality_processing_ms: float | None = None
    extras: dict[str, Any] = Field(default_factory=dict)
