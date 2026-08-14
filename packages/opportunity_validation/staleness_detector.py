"""Staleness detector — determines signal age and freshness.

Answer: How old is the signal?
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from .v1_schemas import StalenessStatus


class StalenessDetector:
    """Detects signal staleness based on configurable thresholds."""

    # Default thresholds (days)
    FRESH_THRESHOLD = 30
    AGING_THRESHOLD = 90
    STALE_THRESHOLD = 120
    ANCIENT_THRESHOLD = 365

    def __init__(
        self,
        fresh_threshold: int | None = None,
        aging_threshold: int | None = None,
        stale_threshold: int | None = None,
        ancient_threshold: int | None = None,
    ):
        self.fresh_threshold = fresh_threshold or self.FRESH_THRESHOLD
        self.aging_threshold = aging_threshold or self.AGING_THRESHOLD
        self.stale_threshold = stale_threshold or self.STALE_THRESHOLD
        self.ancient_threshold = ancient_threshold or self.ANCIENT_THRESHOLD

    def detect(
        self,
        signal_timestamp: datetime,
        current_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Detect staleness of a signal."""
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        # Calculate age
        if signal_timestamp.tzinfo is None:
            signal_timestamp = signal_timestamp.replace(tzinfo=timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        delta = current_time - signal_timestamp
        age_days = delta.days

        # Determine status
        status = self._get_status(age_days)

        # Build explanation
        explanation = self._build_explanation(age_days, status)

        return {
            "signal_timestamp": signal_timestamp.isoformat(),
            "current_time": current_time.isoformat(),
            "age_days": age_days,
            "status": status.value,
            "explanation": explanation,
            "thresholds": {
                "fresh": self.fresh_threshold,
                "aging": self.aging_threshold,
                "stale": self.stale_threshold,
                "ancient": self.ancient_threshold,
            },
        }

    def detect_from_age(self, age_days: int) -> dict[str, Any]:
        """Detect staleness from pre-calculated age."""
        status = self._get_status(age_days)
        explanation = self._build_explanation(age_days, status)

        return {
            "age_days": age_days,
            "status": status.value,
            "explanation": explanation,
            "thresholds": {
                "fresh": self.fresh_threshold,
                "aging": self.aging_threshold,
                "stale": self.stale_threshold,
                "ancient": self.ancient_threshold,
            },
        }

    def _get_status(self, age_days: int) -> StalenessStatus:
        """Get staleness status from age."""
        if age_days <= self.fresh_threshold:
            return StalenessStatus.FRESH
        elif age_days <= self.aging_threshold:
            return StalenessStatus.AGING
        elif age_days <= self.stale_threshold:
            return StalenessStatus.STALE
        else:
            return StalenessStatus.ANCIENT

    def _build_explanation(self, age_days: int, status: StalenessStatus) -> str:
        """Build human-readable explanation."""
        if status == StalenessStatus.FRESH:
            return f"Signal is {age_days} days old — fresh and actionable"
        elif status == StalenessStatus.AGING:
            return f"Signal is {age_days} days old — aging but still relevant"
        elif status == StalenessStatus.STALE:
            return f"Signal is {age_days} days old — stale, may be outdated"
        else:
            return f"Signal is {age_days} days old — ancient, likely irrelevant"

    def should_reject(self, age_days: int) -> bool:
        """Should opportunity be rejected based on age?"""
        return age_days > self.stale_threshold

    def should_hold(self, age_days: int) -> bool:
        """Should opportunity be held for re-evaluation?"""
        return self.fresh_threshold < age_days <= self.stale_threshold

    def get_score_multiplier(self, age_days: int) -> float:
        """Get score multiplier based on age."""
        if age_days <= self.fresh_threshold:
            return 1.0
        elif age_days <= self.aging_threshold:
            return 0.8
        elif age_days <= self.stale_threshold:
            return 0.5
        else:
            return 0.2

    def get_statistics(self) -> dict[str, Any]:
        """Get staleness detection statistics."""
        return {
            "thresholds": {
                "fresh": self.fresh_threshold,
                "aging": self.aging_threshold,
                "stale": self.stale_threshold,
                "ancient": self.ancient_threshold,
            },
            "statuses": [s.value for s in StalenessStatus],
        }
