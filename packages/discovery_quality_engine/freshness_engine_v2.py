"""DQE v2 Freshness Engine — deterministic freshness evaluation with borderline concept."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from discovery_quality_engine.v2_schemas import FreshnessEvaluation, FreshnessStatus


class FreshnessEngineV2:
    """Evaluates signal freshness with accepted/borderline/expired states."""

    def __init__(
        self,
        *,
        accepted_threshold_days: int = 90,
        borderline_threshold_days: int = 180,
    ) -> None:
        self._accepted_threshold = accepted_threshold_days
        self._borderline_threshold = borderline_threshold_days

    @property
    def accepted_threshold_days(self) -> int:
        return self._accepted_threshold

    @property
    def borderline_threshold_days(self) -> int:
        return self._borderline_threshold

    def evaluate(
        self,
        *,
        signal_timestamp: datetime,
        now: datetime | None = None,
    ) -> FreshnessEvaluation:
        current = now or datetime.now(UTC)
        if signal_timestamp.tzinfo is None:
            signal_timestamp = signal_timestamp.replace(tzinfo=UTC)

        age = current - signal_timestamp
        age_days = age.days

        if age_days <= self._accepted_threshold:
            status = FreshnessStatus.ACCEPTED
            reasons = [f"Signal is {age_days} days old (within {self._accepted_threshold} day threshold)"]
        elif age_days <= self._borderline_threshold:
            status = FreshnessStatus.BORDERLINE
            reasons = [
                f"Signal is {age_days} days old",
                f"Between accepted ({self._accepted_threshold}) and borderline ({self._borderline_threshold}) thresholds",
            ]
        else:
            status = FreshnessStatus.EXPIRED
            reasons = [f"Signal is {age_days} days old (exceeds {self._borderline_threshold} day borderline threshold)"]

        evidence = [
            f"Signal age: {age_days} days",
            f"Status: {status.value}",
            f"Accepted threshold: {self._accepted_threshold} days",
            f"Borderline threshold: {self._borderline_threshold} days",
        ]

        return FreshnessEvaluation(
            status=status,
            signal_age_days=age_days,
            thresholds={
                "accepted": self._accepted_threshold,
                "borderline": self._borderline_threshold,
            },
            reasons=reasons,
            evidence=evidence,
        )

    def get_score_multiplier(self, status: FreshnessStatus) -> float:
        """Get score multiplier based on freshness status."""
        if status == FreshnessStatus.ACCEPTED:
            return 1.0
        elif status == FreshnessStatus.BORDERLINE:
            return 0.5
        else:
            return 0.0

    def should_reject(self, status: FreshnessStatus) -> bool:
        """Check if a freshness status should trigger rejection."""
        return status == FreshnessStatus.EXPIRED

    def should_hold(self, status: FreshnessStatus) -> bool:
        """Check if a freshness status should trigger HOLD."""
        return status == FreshnessStatus.BORDERLINE
