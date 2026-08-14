"""Tests for ValidationScheduler."""

from __future__ import annotations

from validation_engine.validation_scheduler import ValidationScheduler


class TestValidationSchedulerGetDailyReport:
    def test_get_daily_report(self) -> None:
        scheduler = ValidationScheduler()
        report = scheduler.get_daily_report()
        assert "report_date" in report
        assert "replies" in report
        assert "meetings" in report

    def test_daily_report_cached(self) -> None:
        scheduler = ValidationScheduler()
        report1 = scheduler.get_daily_report()
        report2 = scheduler.get_daily_report()
        assert report1 is report2

    def test_daily_report_force_refresh(self) -> None:
        scheduler = ValidationScheduler()
        report1 = scheduler.get_daily_report()
        report2 = scheduler.get_daily_report(force=True)
        assert report1 is not report2


class TestValidationSchedulerGetWeeklyReport:
    def test_get_weekly_report(self) -> None:
        scheduler = ValidationScheduler()
        report = scheduler.get_weekly_report()
        assert "week_end" in report
        assert "revenue" in report

    def test_weekly_report_cached(self) -> None:
        scheduler = ValidationScheduler()
        report1 = scheduler.get_weekly_report()
        report2 = scheduler.get_weekly_report()
        assert report1 is report2


class TestValidationSchedulerGetMonthlyReport:
    def test_get_monthly_report(self) -> None:
        scheduler = ValidationScheduler()
        report = scheduler.get_monthly_report()
        assert "month" in report
        assert "revenue" in report

    def test_monthly_report_cached(self) -> None:
        scheduler = ValidationScheduler()
        report1 = scheduler.get_monthly_report()
        report2 = scheduler.get_monthly_report()
        assert report1 is report2
