"""Validation scheduler — schedules validation report generation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from validation_engine.validation_reports import ValidationReportService


class ValidationScheduler:
    """Schedules and caches validation reports."""

    def __init__(self, report_service: ValidationReportService | None = None) -> None:
        self.report_service = report_service or ValidationReportService()
        self._daily_cache: dict[str, Any] = {}
        self._weekly_cache: dict[str, Any] = {}
        self._monthly_cache: dict[str, Any] = {}

    def get_daily_report(self, force: bool = False) -> dict[str, Any]:
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        if not force and today in self._daily_cache:
            return self._daily_cache[today]
        report = self.report_service.generate_daily_report()
        payload = {
            "report_date": report.report_date,
            "signals": report.signals,
            "companies": report.companies,
            "revenue_ready": report.revenue_ready,
            "emails_sent": report.emails_sent,
            "replies": report.replies,
            "meetings": report.meetings,
            "proposals": report.proposals,
            "won": report.won,
            "lost": report.lost,
            "revenue": report.revenue,
            "best_connector": report.best_connector,
            "worst_connector": report.worst_connector,
            "best_industry": report.best_industry,
            "worst_industry": report.worst_industry,
            "top_objections": report.top_objections,
            "biggest_bottleneck": report.biggest_bottleneck,
        }
        self._daily_cache[today] = payload
        return payload

    def get_weekly_report(self, force: bool = False) -> dict[str, Any]:
        now = datetime.now(UTC)
        week_key = f"{now.year}-W{now.isocalendar()[1]}"
        if not force and week_key in self._weekly_cache:
            return self._weekly_cache[week_key]
        report = self.report_service.generate_weekly_report()
        payload = {
            "week_start": report.week_start,
            "week_end": report.week_end,
            "revenue": report.revenue,
            "meetings": report.meetings,
            "deals": report.deals,
            "connector_ranking": [
                {"connector": c.connector, "revenue": c.revenue, "meetings": c.meetings}
                for c in report.connector_ranking
            ],
            "industry_ranking": [
                {"industry": i.industry, "revenue": i.revenue, "win_rate": i.win_rate}
                for i in report.industry_ranking
            ],
            "service_ranking": [
                {"service": s.service, "revenue": s.revenue, "win_rate": s.win_rate}
                for s in report.service_ranking
            ],
        }
        self._weekly_cache[week_key] = payload
        return payload

    def get_monthly_report(self, force: bool = False) -> dict[str, Any]:
        month_key = datetime.now(UTC).strftime("%Y-%m")
        if not force and month_key in self._monthly_cache:
            return self._monthly_cache[month_key]
        report = self.report_service.generate_monthly_report()
        payload = {
            "month": report.month,
            "revenue": report.revenue,
            "avg_deal_size": report.avg_deal_size,
            "avg_sales_cycle_days": report.avg_sales_cycle_days,
            "reply_rate": report.reply_rate,
            "meeting_rate": report.meeting_rate,
            "proposal_rate": report.proposal_rate,
            "win_rate": report.win_rate,
            "revenue_per_connector": report.revenue_per_connector,
            "revenue_per_industry": report.revenue_per_industry,
            "revenue_per_service": report.revenue_per_service,
        }
        self._monthly_cache[month_key] = payload
        return payload
