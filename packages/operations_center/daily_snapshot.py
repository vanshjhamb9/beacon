"""Hourly / daily snapshot helpers."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from operations_center.models import HourlyTimelineEntry


SNAPSHOT_FIELDS: tuple[str, ...] = (
    "signals",
    "verified_companies",
    "emails",
    "decision_makers",
    "sales_ready",
    "revenue_ready",
)


def build_hourly_timeline(
    points: list[dict[str, Any]],
    *,
    day_start: datetime,
) -> list[HourlyTimelineEntry]:
    """Collapse timestamped counters into hourly buckets for the day."""
    buckets: dict[int, dict[str, int]] = defaultdict(
        lambda: {
            "collected": 0,
            "verified": 0,
            "emails": 0,
            "decision_makers": 0,
            "sales_ready": 0,
            "revenue_ready": 0,
        }
    )
    for point in points:
        ts = point.get("created_at") or point.get("hour")
        if not isinstance(ts, datetime):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        if ts < day_start:
            continue
        hour = ts.hour
        bucket = buckets[hour]
        bucket["collected"] += int(point.get("collected") or point.get("signals") or 0)
        bucket["verified"] += int(point.get("verified") or point.get("verified_companies") or 0)
        bucket["emails"] += int(point.get("emails") or 0)
        bucket["decision_makers"] += int(point.get("decision_makers") or 0)
        bucket["sales_ready"] += int(point.get("sales_ready") or 0)
        bucket["revenue_ready"] += int(point.get("revenue_ready") or 0)

    now_hour = datetime.now(UTC).hour
    out: list[HourlyTimelineEntry] = []
    for hour in range(24):
        data = buckets.get(hour)
        if not data:
            if hour > now_hour:
                continue
            data = {
                "collected": 0,
                "verified": 0,
                "emails": 0,
                "decision_makers": 0,
                "sales_ready": 0,
                "revenue_ready": 0,
            }
        out.append(
            HourlyTimelineEntry(
                hour=f"{hour:02d}:00",
                collected=data["collected"],
                verified=data["verified"],
                emails=data["emails"],
                decision_makers=data["decision_makers"],
                sales_ready=data["sales_ready"],
                revenue_ready=data["revenue_ready"],
            )
        )
    return out


def snapshot_payload(
    *,
    signals: int,
    verified_companies: int,
    emails: int,
    decision_makers: int,
    sales_ready: int,
    revenue_ready: int,
) -> dict[str, int]:
    return {
        "signals": int(signals or 0),
        "verified_companies": int(verified_companies or 0),
        "emails": int(emails or 0),
        "decision_makers": int(decision_makers or 0),
        "sales_ready": int(sales_ready or 0),
        "revenue_ready": int(revenue_ready or 0),
    }
