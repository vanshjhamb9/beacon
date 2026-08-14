"""Freshness and expiration rules for live opportunities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

MAX_EVENT_AGE_DAYS = 21
PRIORITY_EVENT_DAYS = 3
PREFERRED_EVENT_DAYS = 7
OPPORTUNITY_EXPIRATION_DAYS = 45
LIVE_REFRESH_MINUTES = 15


@dataclass(frozen=True, slots=True)
class FreshnessDecision:
    accepted: bool
    age_days: int
    score: float
    bucket: str
    expires_at: datetime


class FreshnessFilter:
    def evaluate(self, event_timestamp: datetime, *, now: datetime | None = None) -> FreshnessDecision:
        current = now or datetime.now(UTC)
        if event_timestamp.tzinfo is None:
            event_timestamp = event_timestamp.replace(tzinfo=UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        age_days = max((current - event_timestamp).days, 0)
        if age_days > MAX_EVENT_AGE_DAYS:
            return FreshnessDecision(False, age_days, 0.0, "expired_event", event_timestamp)
        if age_days <= PRIORITY_EVENT_DAYS:
            score, bucket = 100.0, "priority"
        elif age_days <= PREFERRED_EVENT_DAYS:
            score, bucket = 90.0, "preferred"
        elif age_days <= 14:
            score, bucket = 72.0, "fresh"
        else:
            score, bucket = 55.0, "aging"
        return FreshnessDecision(
            True,
            age_days,
            score,
            bucket,
            event_timestamp + timedelta(days=OPPORTUNITY_EXPIRATION_DAYS),
        )
