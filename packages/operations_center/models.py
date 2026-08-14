"""Typed domain models for Beacon Operations Center."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


PIPELINE_STAGES: tuple[str, ...] = (
    "signals",
    "identity_candidates",
    "verified_websites",
    "companies",
    "emails",
    "decision_makers",
    "sales_ready",
    "revenue_ready",
    "contacted",
    "meetings",
    "won",
)

KNOWN_CONNECTORS: tuple[str, ...] = (
    "github_trending",
    "product_hunt",
    "hacker_news",
    "reddit",
    "rss",
    "indie_hackers",
    "devto",
    "sec_edgar",
    "yc",
    "app_store",
    "google_play",
    "linkedin",
    "hunter",
    "apollo",
    "people_data_labs",
    "crunchbase",
    "clearbit",
    "builtwith",
    "wappalyzer",
    "google_maps",
)

KNOWN_WORKERS: tuple[str, ...] = (
    "collector",
    "identity",
    "enrichment",
    "decision_maker",
    "sales_readiness",
    "revenue_ready",
    "outreach",
)

KNOWN_QUEUES: tuple[str, ...] = (
    "identity",
    "email",
    "decision",
    "revenue",
    "enrichment",
    "default",
)


@dataclass(slots=True)
class StageMetric:
    stage: str
    current: int = 0
    today: int = 0
    yesterday: int = 0
    hour: int = 0
    trend_7d: list[int] = field(default_factory=list)
    delta_pct: float | None = None


@dataclass(slots=True)
class ConversionStep:
    from_stage: str
    to_stage: str
    from_count: int
    to_count: int
    conversion_pct: float
    drop_pct: float


@dataclass(slots=True)
class ConnectorHealthView:
    connector: str
    enabled: bool = False
    healthy: bool = False
    status: str = "unknown"
    last_run: datetime | None = None
    last_success: datetime | None = None
    last_failure: datetime | None = None
    success_rate: float = 0.0
    error_count: int = 0
    records_today: int = 0
    records_total: int = 0
    avg_runtime: float = 0.0
    rate_limited: bool = False
    detail: str = ""


@dataclass(slots=True)
class WorkerHealthView:
    worker_name: str
    running: bool = False
    queue_size: int = 0
    jobs_completed: int = 0
    jobs_failed: int = 0
    avg_duration: float = 0.0
    last_execution: datetime | None = None
    status: str = "unknown"


@dataclass(slots=True)
class QueueView:
    name: str
    pending: int = 0


@dataclass(slots=True)
class FailureView:
    reason: str
    count: int = 0


@dataclass(slots=True)
class FeedEvent:
    timestamp: datetime
    kind: str
    message: str
    collector: str | None = None
    company: str | None = None
    status: str | None = None
    count: int | None = None


@dataclass(slots=True)
class HourlyTimelineEntry:
    hour: str
    collected: int = 0
    verified: int = 0
    emails: int = 0
    decision_makers: int = 0
    sales_ready: int = 0
    revenue_ready: int = 0


@dataclass(slots=True)
class SourceMapNode:
    connector: str
    signals: int = 0
    verified: int = 0
    emails: int = 0
    decision_makers: int = 0
    revenue_ready: int = 0


@dataclass(slots=True)
class TodayProgress:
    started_revenue_ready: int = 0
    current_revenue_ready: int = 0
    difference: int = 0


@dataclass(slots=True)
class RevenueEngineView:
    pipeline: float = 0.0
    projected: float = 0.0
    meetings: int = 0
    won: int = 0


@dataclass(slots=True)
class HealthSummary:
    collecting: bool = False
    pipeline_healthy: bool = False
    connectors_healthy: int = 0
    connectors_total: int = 0
    workers_running: int = 0
    workers_total: int = 0
    biggest_bottleneck: str | None = None
    tone: str = "YELLOW"
    summary: str = ""


@dataclass(slots=True)
class LiveDashboard:
    generated_at: datetime
    cards: dict[str, Any]
    pipeline: list[StageMetric]
    conversions: list[ConversionStep]
    connectors: list[ConnectorHealthView]
    workers: list[WorkerHealthView]
    queues: list[QueueView]
    failures: list[FailureView]
    feed: list[FeedEvent]
    timeline: list[HourlyTimelineEntry]
    progress: TodayProgress
    revenue: RevenueEngineView
    source_map: list[SourceMapNode]
    health: HealthSummary
    scoring_version: str = "boc-v1"
