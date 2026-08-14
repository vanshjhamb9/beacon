from typing import Any

from pydantic import BaseModel, Field


class ConnectorAuditResponse(BaseModel):
    source: str
    enabled: bool
    health_status: str
    consecutive_failures: int
    average_latency_ms: float | None = None
    last_success_at: str | None = None
    last_failure_at: str | None = None
    last_error: str | None = None
    signals_collected_24h: int
    companies_discovered_24h: int
    opportunities_produced_24h: int
    high_value_opportunities_24h: int
    duplicate_rate_24h: float
    failure_rate_24h: float
    coverage_score: float
    extraction_quality_avg: float


class ConnectorBenchmarkResponse(BaseModel):
    source: str
    quality_score: float
    opportunity_yield: float
    high_value_yield: float
    company_discovery_rate: float
    duplicate_rate: float
    failure_rate: float
    average_latency_ms: float
    rank: int
    explanation: str


class AcquisitionDashboardResponse(BaseModel):
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
    connectors: list[ConnectorAuditResponse]
    leaderboard: list[ConnectorBenchmarkResponse]
    latest_daily_report: dict[str, Any] | None = None


class AcquisitionAuditResponse(BaseModel):
    connectors: list[dict[str, Any]]
    open_alerts: int
    generated_at: str


class AcquisitionBenchmarksResponse(BaseModel):
    leaderboard: list[dict[str, Any]]
    generated_at: str


class AcquisitionAlertsResponse(BaseModel):
    alerts: list[dict[str, Any]] = Field(default_factory=list)


class AcquisitionDailyReportResponse(BaseModel):
    report: dict[str, Any]
