from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AsaScheduleHints:
    """Celery beat cadence hints — worker owns actual scheduling."""

    morning_brief_seconds: int = 86_400
    work_queue_refresh_seconds: int = 180
    company_refresh_batch_seconds: int = 300


def default_schedule() -> AsaScheduleHints:
    return AsaScheduleHints()
