from __future__ import annotations

from datetime import date

from data_acquisition.models.types import (
    ConnectorAlert,
    ConnectorAuditItem,
    ConnectorBenchmark,
    DailyAcquisitionReport,
)


class DailyReportBuilder:
    def build(
        self,
        *,
        report_date: date,
        new_companies: int,
        new_opportunities: int,
        high_value_opportunities: int,
        signals_collected: int,
        signals_persisted: int,
        duplicate_rate: float,
        previous_companies: int,
        audits: list[ConnectorAuditItem],
        benchmarks: list[ConnectorBenchmark],
        missing_data_trends: dict[str, int],
        alerts: list[ConnectorAlert],
    ) -> DailyAcquisitionReport:
        coverage_growth = 0.0
        if previous_companies > 0:
            coverage_growth = round(((new_companies) / previous_companies) * 100.0, 2)
        elif new_companies > 0:
            coverage_growth = 100.0

        top = benchmarks[0].source if benchmarks else "none"
        summary = (
            f"{report_date.isoformat()}: {new_companies} new companies, "
            f"{new_opportunities} opportunities ({high_value_opportunities} high-value), "
            f"{signals_persisted} persisted signals. Top source: {top}."
        )
        return DailyAcquisitionReport(
            report_date=report_date.isoformat(),
            new_companies=new_companies,
            new_opportunities=new_opportunities,
            high_value_opportunities=high_value_opportunities,
            signals_collected=signals_collected,
            signals_persisted=signals_persisted,
            duplicate_rate=round(duplicate_rate, 2),
            coverage_growth=coverage_growth,
            collector_performance=audits,
            benchmarks=benchmarks,
            missing_data_trends=missing_data_trends,
            alerts=alerts,
            summary=summary,
        )
