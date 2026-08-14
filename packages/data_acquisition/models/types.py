from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AlertSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ConnectorAuditItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    enabled: bool
    health_status: str
    consecutive_failures: int
    average_latency_ms: float | None
    last_success_at: datetime | None
    last_failure_at: datetime | None
    last_error: str | None
    signals_collected_24h: int
    companies_discovered_24h: int
    opportunities_produced_24h: int
    high_value_opportunities_24h: int
    duplicate_rate_24h: float
    failure_rate_24h: float
    coverage_score: float
    extraction_quality_avg: float


class ConnectorBenchmark(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    quality_score: float = Field(ge=0.0, le=100.0)
    opportunity_yield: float
    high_value_yield: float
    company_discovery_rate: float
    duplicate_rate: float
    failure_rate: float
    average_latency_ms: float
    rank: int
    explanation: str


class AcquisitionRunMetric(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    collected: int
    emitted: int
    duplicates: int
    rate_limited: bool
    success: bool
    latency_ms: float
    error: str | None = None
    trace_id: str | None = None
    recorded_at: datetime


class ConnectorAlert(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    severity: AlertSeverity
    code: str
    message: str
    consecutive_failures: int
    details: dict[str, Any] = Field(default_factory=dict)


class DailyAcquisitionReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    report_date: str
    new_companies: int
    new_opportunities: int
    high_value_opportunities: int
    signals_collected: int
    signals_persisted: int
    duplicate_rate: float
    coverage_growth: float
    collector_performance: list[ConnectorAuditItem]
    benchmarks: list[ConnectorBenchmark]
    missing_data_trends: dict[str, int]
    alerts: list[ConnectorAlert]
    summary: str


class AcquisitionDashboard(BaseModel):
    model_config = ConfigDict(frozen=True)

    overall_coverage_score: float
    active_connectors: int
    healthy_connectors: int
    degraded_connectors: int
    down_connectors: int
    signals_24h: int
    companies_24h: int
    opportunities_24h: int
    high_value_opportunities_24h: int
    average_duplicate_rate: float
    average_failure_rate: float
    open_alerts: int
    connectors: list[ConnectorAuditItem]
    leaderboard: list[ConnectorBenchmark]
    latest_daily_report: DailyAcquisitionReport | None = None


class AcquisitionSnapshotInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    enabled: bool
    health_status: str = "unknown"
    consecutive_failures: int = 0
    average_latency_ms: float | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_error: str | None = None
    runs_24h: int = 0
    successful_runs_24h: int = 0
    failed_runs_24h: int = 0
    collected_24h: int = 0
    emitted_24h: int = 0
    duplicates_24h: int = 0
    rate_limited_runs_24h: int = 0
    companies_discovered_24h: int = 0
    opportunities_produced_24h: int = 0
    high_value_opportunities_24h: int = 0
    extraction_quality_avg: float = 0.0
