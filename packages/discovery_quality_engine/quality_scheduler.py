"""Quality scheduler — triggers periodic quality evaluations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable

from discovery_quality_engine.quality_dashboard import QualityDashboard
from discovery_quality_engine.quality_reports import QualityReportGenerator


class QualityScheduler:
    def __init__(
        self,
        dashboard: QualityDashboard,
        on_snapshot: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self._dashboard = dashboard
        self._report_gen = QualityReportGenerator(dashboard)
        self._on_snapshot = on_snapshot
        self._last_daily: datetime | None = None
        self._last_weekly: datetime | None = None

    def check_and_run(self, *, now: datetime | None = None) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        result: dict[str, Any] = {}

        if self._should_run_daily(current):
            report = self._report_gen.daily_report(date=current)
            self._last_daily = current
            result["daily"] = report
            if self._on_snapshot:
                self._on_snapshot(report)

        if self._should_run_weekly(current):
            report = self._report_gen.weekly_report(week_ending=current)
            self._last_weekly = current
            result["weekly"] = report
            if self._on_snapshot:
                self._on_snapshot(report)

        return result

    def force_daily(self, *, now: datetime | None = None) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        report = self._report_gen.daily_report(date=current)
        self._last_daily = current
        if self._on_snapshot:
            self._on_snapshot(report)
        return report

    def force_weekly(self, *, now: datetime | None = None) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        report = self._report_gen.weekly_report(week_ending=current)
        self._last_weekly = current
        if self._on_snapshot:
            self._on_snapshot(report)
        return report

    def _should_run_daily(self, now: datetime) -> bool:
        if self._last_daily is None:
            return True
        elapsed = (now - self._last_daily).total_seconds()
        return elapsed >= 86400

    def _should_run_weekly(self, now: datetime) -> bool:
        if self._last_weekly is None:
            return True
        elapsed = (now - self._last_weekly).total_seconds()
        return elapsed >= 604800
