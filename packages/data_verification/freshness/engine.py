from __future__ import annotations

from datetime import UTC, datetime

from data_verification.models.types import FreshnessStatus


class FreshnessEngine:
    def __init__(
        self,
        *,
        fresh_days: float = 7.0,
        ageing_days: float = 30.0,
        stale_days: float = 60.0,
        expired_days: float = 90.0,
    ) -> None:
        self.fresh_days = fresh_days
        self.ageing_days = ageing_days
        self.stale_days = stale_days
        self.expired_days = expired_days

    def evaluate(
        self,
        collected_at: datetime | None,
        *,
        now: datetime | None = None,
    ) -> tuple[float, FreshnessStatus, float]:
        reference = now or datetime.now(UTC)
        if collected_at is None:
            return 25.0, FreshnessStatus.STALE, 999.0
        stamped = collected_at if collected_at.tzinfo else collected_at.replace(tzinfo=UTC)
        age_days = max(0.0, (reference.astimezone(UTC) - stamped.astimezone(UTC)).total_seconds() / 86_400)

        if age_days <= self.fresh_days:
            return 100.0, FreshnessStatus.FRESH, age_days
        if age_days <= self.ageing_days:
            score = 85.0 - ((age_days - self.fresh_days) / max(1.0, self.ageing_days - self.fresh_days) * 20.0)
            return round(score, 2), FreshnessStatus.AGEING, age_days
        if age_days <= self.stale_days:
            score = 65.0 - ((age_days - self.ageing_days) / max(1.0, self.stale_days - self.ageing_days) * 25.0)
            return round(score, 2), FreshnessStatus.STALE, age_days
        if age_days <= self.expired_days:
            score = 40.0 - ((age_days - self.stale_days) / max(1.0, self.expired_days - self.stale_days) * 25.0)
            return round(max(15.0, score), 2), FreshnessStatus.EXPIRED, age_days
        return 10.0, FreshnessStatus.EXPIRED, age_days
