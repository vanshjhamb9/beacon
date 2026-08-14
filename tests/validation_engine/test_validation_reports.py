"""Tests for ValidationReports."""

from __future__ import annotations

from validation_engine.validation_reports import ValidationReportService


class TestValidationReportServiceDailyReport:
    def test_generate_daily_report(self) -> None:
        service = ValidationReportService()
        report = service.generate_daily_report()
        assert report.report_date is not None
        assert report.replies == 0
        assert report.meetings == 0
        assert report.proposals == 0
        assert report.won == 0
        assert report.lost == 0
        assert report.revenue == 0.0

    def test_daily_report_with_data(self) -> None:
        service = ValidationReportService()
        service.reply_tracker.record_reply("company_1", "positive")
        service.meeting_tracker.record_meeting("company_1", "completed")
        service.deal_tracker.record_deal("company_1", "won", revenue=50000.0)
        report = service.generate_daily_report()
        assert report.replies == 1
        assert report.meetings == 1
        assert report.won == 1
        assert report.revenue == 50000.0


class TestValidationReportServiceWeeklyReport:
    def test_generate_weekly_report(self) -> None:
        service = ValidationReportService()
        report = service.generate_weekly_report()
        assert report.week_end is not None
        assert report.revenue == 0.0
        assert report.meetings == 0
        assert report.deals == 0


class TestValidationReportServiceMonthlyReport:
    def test_generate_monthly_report(self) -> None:
        service = ValidationReportService()
        report = service.generate_monthly_report()
        assert report.month is not None
        assert report.revenue == 0.0
        assert report.win_rate == 0.0

    def test_monthly_report_with_data(self) -> None:
        service = ValidationReportService()
        service.deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        service.deal_tracker.record_deal("company_2", "won", revenue=50000.0)
        report = service.generate_monthly_report()
        assert report.revenue == 150000.0
        assert report.avg_deal_size == 75000.0
