"""Tests for QualityScheduler."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from discovery_quality_engine.quality_dashboard import QualityDashboard
from discovery_quality_engine.quality_scheduler import QualityScheduler


class TestQualityScheduler:
    def setup_method(self) -> None:
        self.dashboard = QualityDashboard()
        self.scheduler = QualityScheduler(dashboard=self.dashboard)

    def test_first_check_runs_daily(self) -> None:
        result = self.scheduler.check_and_run()
        assert "daily" in result

    def test_first_check_runs_weekly(self) -> None:
        result = self.scheduler.check_and_run()
        assert "weekly" in result

    def test_daily_not_run_twice_within_24h(self) -> None:
        now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        self.scheduler.check_and_run(now=now)
        result = self.scheduler.check_and_run(now=now + timedelta(hours=1))
        assert "daily" not in result

    def test_daily_run_after_24h(self) -> None:
        now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        self.scheduler.check_and_run(now=now)
        result = self.scheduler.check_and_run(now=now + timedelta(hours=25))
        assert "daily" in result

    def test_weekly_not_run_twice_within_7d(self) -> None:
        now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        self.scheduler.check_and_run(now=now)
        result = self.scheduler.check_and_run(now=now + timedelta(days=3))
        assert "weekly" not in result

    def test_weekly_run_after_7d(self) -> None:
        now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        self.scheduler.check_and_run(now=now)
        result = self.scheduler.check_and_run(now=now + timedelta(days=8))
        assert "weekly" in result

    def test_force_daily(self) -> None:
        now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        self.scheduler.check_and_run(now=now)
        result = self.scheduler.force_daily(now=now)
        assert "report_type" in result
        assert result["report_type"] == "daily"

    def test_force_weekly(self) -> None:
        now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        result = self.scheduler.force_weekly(now=now)
        assert result["report_type"] == "weekly"

    def test_on_snapshot_callback(self) -> None:
        snapshots: list[dict] = []
        scheduler = QualityScheduler(dashboard=self.dashboard, on_snapshot=snapshots.append)
        scheduler.force_daily()
        assert len(snapshots) == 1

    def test_default_now_used(self) -> None:
        result = self.scheduler.check_and_run()
        assert "daily" in result or "weekly" in result
