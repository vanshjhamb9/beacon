"""Deterministic freshness scoring."""

from __future__ import annotations

from datetime import UTC, datetime

from opportunity_intelligence.constants import FRESHNESS_BUCKETS
from opportunity_intelligence.schemas import FreshnessResult


class FreshnessEngine:
    def calculate(self, timestamp: datetime, *, now: datetime | None = None) -> FreshnessResult:
        current = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        age_days = max((current - timestamp).days, 0)
        for start, end, score, bucket in FRESHNESS_BUCKETS:
            if age_days >= start and (end is None or age_days <= end):
                return FreshnessResult(score=score, age_days=age_days, bucket=bucket)
        last = FRESHNESS_BUCKETS[-1]
        return FreshnessResult(score=last[2], age_days=age_days, bucket=last[3])
