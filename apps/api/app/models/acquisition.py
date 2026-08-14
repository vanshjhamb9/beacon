from datetime import date, datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CollectorRun(BaseModel):
    __tablename__ = "collector_runs"
    __table_args__ = (
        Index("ix_collector_runs_source_created", "source", "created_at"),
        Index("ix_collector_runs_success_created", "success", "created_at"),
    )

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    collected: Mapped[int] = mapped_column(Integer, nullable=False)
    emitted: Mapped[int] = mapped_column(Integer, nullable=False)
    duplicates: Mapped[int] = mapped_column(Integer, nullable=False)
    rate_limited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    trace_id: Mapped[str | None] = mapped_column(String(64))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ConnectorAlertRecord(BaseModel):
    __tablename__ = "connector_alerts"
    __table_args__ = (
        Index("ix_connector_alerts_source_created", "source", "created_at"),
        Index("ix_connector_alerts_open_severity", "resolved_at", "severity"),
    )

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AcquisitionDailyReport(BaseModel):
    __tablename__ = "acquisition_daily_reports"
    __table_args__ = (Index("ix_acquisition_daily_reports_date", "report_date"),)

    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    new_companies: Mapped[int] = mapped_column(Integer, nullable=False)
    new_opportunities: Mapped[int] = mapped_column(Integer, nullable=False)
    high_value_opportunities: Mapped[int] = mapped_column(Integer, nullable=False)
    signals_collected: Mapped[int] = mapped_column(Integer, nullable=False)
    signals_persisted: Mapped[int] = mapped_column(Integer, nullable=False)
    duplicate_rate: Mapped[float] = mapped_column(Float, nullable=False)
    coverage_growth: Mapped[float] = mapped_column(Float, nullable=False)
    missing_data_trends: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    collector_performance: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    benchmarks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    alerts: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ConnectorBenchmarkSnapshot(BaseModel):
    __tablename__ = "connector_benchmark_snapshots"
    __table_args__ = (Index("ix_connector_benchmark_snapshots_source_created", "source", "created_at"),)

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    report_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("acquisition_daily_reports.id")
    )
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    opportunity_yield: Mapped[float] = mapped_column(Float, nullable=False)
    high_value_yield: Mapped[float] = mapped_column(Float, nullable=False)
    company_discovery_rate: Mapped[float] = mapped_column(Float, nullable=False)
    duplicate_rate: Mapped[float] = mapped_column(Float, nullable=False)
    failure_rate: Mapped[float] = mapped_column(Float, nullable=False)
    average_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
