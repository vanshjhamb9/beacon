"""Reports — generates revenue operations reports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class Report:
    """Single report."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.report_type: str = data.get("report_type", "unknown")
        self.title: str = data.get("title", "Unknown Report")
        self.data: dict[str, Any] = data.get("data", {})
        self.generated_at: datetime = data.get("generated_at", datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "report_type": self.report_type,
            "title": self.title,
            "data": self.data,
            "generated_at": self.generated_at.isoformat(),
        }


class ReportGenerator:
    """Generates revenue operations reports."""

    def __init__(self):
        self._reports: list[Report] = []

    def generate_daily_summary(
        self,
        inbox_stats: dict[str, Any],
        pipeline_stats: dict[str, Any],
        outreach_stats: dict[str, Any],
        revenue_stats: dict[str, Any],
    ) -> Report:
        """Generate daily summary report."""
        report = Report({
            "report_type": "daily_summary",
            "title": f"Daily Summary - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
            "data": {
                "inbox": inbox_stats,
                "pipeline": pipeline_stats,
                "outreach": outreach_stats,
                "revenue": revenue_stats,
            },
        })
        self._reports.append(report)
        return report

    def generate_connector_performance(
        self,
        connector_stats: dict[str, Any],
    ) -> Report:
        """Generate connector performance report."""
        report = Report({
            "report_type": "connector_performance",
            "title": "Connector Performance Report",
            "data": connector_stats,
        })
        self._reports.append(report)
        return report

    def generate_pipeline_health(
        self,
        pipeline_data: dict[str, Any],
    ) -> Report:
        """Generate pipeline health report."""
        report = Report({
            "report_type": "pipeline_health",
            "title": "Pipeline Health Report",
            "data": pipeline_data,
        })
        self._reports.append(report)
        return report

    def generate_revenue_forecast(
        self,
        revenue_data: dict[str, Any],
    ) -> Report:
        """Generate revenue forecast report."""
        report = Report({
            "report_type": "revenue_forecast",
            "title": "Revenue Forecast Report",
            "data": revenue_data,
        })
        self._reports.append(report)
        return report

    def get_reports(self) -> list[Report]:
        """Get all reports."""
        return list(self._reports)

    def get_latest_report(self, report_type: str | None = None) -> Report | None:
        """Get latest report, optionally filtered by type."""
        if report_type:
            filtered = [r for r in self._reports if r.report_type == report_type]
            return filtered[-1] if filtered else None
        return self._reports[-1] if self._reports else None
