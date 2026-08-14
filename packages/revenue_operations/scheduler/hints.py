from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RocScheduleHints:
    refresh_dashboard_seconds: int = 120
    refresh_forecast_seconds: int = 300
    refresh_alerts_seconds: int = 60
    daily_learning_seconds: int = 86_400


def default_schedule() -> RocScheduleHints:
    return RocScheduleHints()
