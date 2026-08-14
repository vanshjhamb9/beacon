from __future__ import annotations

from datetime import date

from data_acquisition.alerting.engine import AlertEngine
from data_acquisition.audit.engine import ConnectorAuditEngine
from data_acquisition.benchmarking.engine import ConnectorBenchmarkEngine
from data_acquisition.models.types import (
    AcquisitionDashboard,
    AcquisitionSnapshotInput,
    DailyAcquisitionReport,
)
from data_acquisition.reports.daily import DailyReportBuilder


class AcquisitionAnalyticsPipeline:
    def __init__(
        self,
        *,
        audit_engine: ConnectorAuditEngine | None = None,
        benchmark_engine: ConnectorBenchmarkEngine | None = None,
        report_builder: DailyReportBuilder | None = None,
        alerter: AlertEngine | None = None,
    ) -> None:
        self.alerter = alerter or AlertEngine()
        self.audit_engine = audit_engine or ConnectorAuditEngine(alerter=self.alerter)
        self.benchmark_engine = benchmark_engine or ConnectorBenchmarkEngine()
        self.report_builder = report_builder or DailyReportBuilder()

    def build_dashboard(
        self,
        snapshots: list[AcquisitionSnapshotInput],
        *,
        latest_report: DailyAcquisitionReport | None = None,
    ) -> AcquisitionDashboard:
        audits, alerts = self.audit_engine.audit(snapshots)
        leaderboard = self.benchmark_engine.rank(audits)
        enabled = [item for item in audits if item.enabled]
        return AcquisitionDashboard(
            overall_coverage_score=round(
                sum(item.coverage_score for item in enabled) / len(enabled), 2
            )
            if enabled
            else 0.0,
            active_connectors=len(enabled),
            healthy_connectors=sum(1 for item in enabled if item.health_status == "healthy"),
            degraded_connectors=sum(1 for item in enabled if item.health_status == "degraded"),
            down_connectors=sum(1 for item in enabled if item.health_status == "down"),
            signals_24h=sum(item.signals_collected_24h for item in audits),
            companies_24h=sum(item.companies_discovered_24h for item in audits),
            opportunities_24h=sum(item.opportunities_produced_24h for item in audits),
            high_value_opportunities_24h=sum(item.high_value_opportunities_24h for item in audits),
            average_duplicate_rate=round(
                sum(item.duplicate_rate_24h for item in enabled) / len(enabled), 2
            )
            if enabled
            else 0.0,
            average_failure_rate=round(
                sum(item.failure_rate_24h for item in enabled) / len(enabled), 2
            )
            if enabled
            else 0.0,
            open_alerts=len(alerts),
            connectors=audits,
            leaderboard=leaderboard,
            latest_daily_report=latest_report,
        )

    def build_daily_report(
        self,
        snapshots: list[AcquisitionSnapshotInput],
        *,
        report_date: date,
        new_companies: int,
        new_opportunities: int,
        high_value_opportunities: int,
        signals_collected: int,
        signals_persisted: int,
        duplicate_rate: float,
        previous_companies: int,
        missing_data_trends: dict[str, int],
    ) -> DailyAcquisitionReport:
        audits, alerts = self.audit_engine.audit(snapshots)
        benchmarks = self.benchmark_engine.rank(audits)
        return self.report_builder.build(
            report_date=report_date,
            new_companies=new_companies,
            new_opportunities=new_opportunities,
            high_value_opportunities=high_value_opportunities,
            signals_collected=signals_collected,
            signals_persisted=signals_persisted,
            duplicate_rate=duplicate_rate,
            previous_companies=previous_companies,
            audits=audits,
            benchmarks=benchmarks,
            missing_data_trends=missing_data_trends,
            alerts=alerts,
        )
