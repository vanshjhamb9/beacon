from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from campaign_intelligence.models.types import ScheduleRules


# Lightweight holiday exclusion set (UTC dates as YYYY-MM-DD). Expandable later.
DEFAULT_HOLIDAYS: set[str] = {
    "2026-01-01",
    "2026-07-04",
    "2026-12-25",
    "2027-01-01",
    "2027-07-04",
    "2027-12-25",
}


class ScheduleEngine:
    """Provider-agnostic scheduling rules. Does not enqueue real sends."""

    def __init__(self, holidays: set[str] | None = None) -> None:
        self.holidays = holidays or DEFAULT_HOLIDAYS

    def normalize_rules(self, rules: ScheduleRules | None, *, timezone: str = "UTC") -> ScheduleRules:
        base = rules or ScheduleRules()
        if timezone and timezone != base.timezone:
            return base.model_copy(update={"timezone": timezone})
        return base

    def next_send_window(
        self,
        *,
        rules: ScheduleRules,
        from_time: datetime | None = None,
        delay_hours: float = 0.0,
    ) -> datetime:
        start = from_time or datetime.now(UTC)
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        candidate = start + timedelta(hours=delay_hours)
        try:
            tz = ZoneInfo(rules.timezone)
        except Exception:
            tz = ZoneInfo("UTC")
        local = candidate.astimezone(tz)

        for _ in range(60):
            if rules.exclude_holidays and local.date().isoformat() in self.holidays:
                local = local.replace(hour=rules.business_hours_start, minute=0, second=0, microsecond=0)
                local = local + timedelta(days=1)
                continue
            if local.weekday() not in rules.working_days:
                local = local.replace(hour=rules.business_hours_start, minute=0, second=0, microsecond=0)
                local = local + timedelta(days=1)
                continue
            if local.hour < rules.business_hours_start:
                local = local.replace(hour=rules.business_hours_start, minute=0, second=0, microsecond=0)
                break
            if local.hour >= rules.business_hours_end:
                local = local.replace(hour=rules.business_hours_start, minute=0, second=0, microsecond=0)
                local = local + timedelta(days=1)
                continue
            break
        return local.astimezone(UTC)

    def plan_step_times(
        self,
        *,
        rules: ScheduleRules,
        delay_hours: list[float],
        from_time: datetime | None = None,
    ) -> list[datetime]:
        times: list[datetime] = []
        cursor = from_time or datetime.now(UTC)
        for delay in delay_hours:
            slot = self.next_send_window(rules=rules, from_time=cursor if delay == 0 else cursor, delay_hours=delay if not times else delay)
            # For subsequent steps, base from first planned start with cumulative delays
            if not times:
                slot = self.next_send_window(rules=rules, from_time=from_time, delay_hours=delay)
            else:
                slot = self.next_send_window(rules=rules, from_time=from_time, delay_hours=delay)
            times.append(slot)
        return times

    def timing_reason(self, rules: ScheduleRules) -> str:
        days = ", ".join(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d] for d in rules.working_days)
        holiday = "excluding holidays" if rules.exclude_holidays else "including holidays"
        return (
            f"Schedule uses {rules.timezone} business hours "
            f"{rules.business_hours_start:02d}:00–{rules.business_hours_end:02d}:00 on {days}, "
            f"{holiday}, rate limit {rules.rate_limit_per_day}/day, "
            f"retry window {rules.retry_window_hours:.0f}h. No provider delivery in Sprint 14."
        )

    def as_payload(self, rules: ScheduleRules, planned_times: list[datetime]) -> dict[str, Any]:
        return {
            "timezone": rules.timezone,
            "business_hours": [rules.business_hours_start, rules.business_hours_end],
            "working_days": list(rules.working_days),
            "rate_limit_per_day": rules.rate_limit_per_day,
            "retry_window_hours": rules.retry_window_hours,
            "exclude_holidays": rules.exclude_holidays,
            "planned_utc": [item.isoformat() for item in planned_times],
            "delivery_enabled": False,
        }
