"""Deterministic company activity engine — accept only if recent activity evidence exists."""

from __future__ import annotations

from datetime import UTC, datetime

from discovery_quality_engine.quality_engine import (
    QualityDecision,
    QualityGate,
    RejectionReason,
)

DEFAULT_MIN_ACTIVITY_SIGNALS: int = 1
DEFAULT_MAX_ACTIVITY_AGE_DAYS: int = 90


class ActivityEvidence:
    __slots__ = ("activity_type", "timestamp", "source", "title")

    def __init__(
        self,
        *,
        activity_type: str,
        timestamp: datetime,
        source: str = "",
        title: str = "",
    ) -> None:
        self.activity_type = activity_type
        self.timestamp = timestamp
        self.source = source
        self.title = title


class ActivityResult:
    __slots__ = ("decision", "reasons", "activity_count")

    def __init__(
        self,
        *,
        decision: QualityDecision,
        reasons: tuple[str, ...] = (),
        activity_count: int = 0,
    ) -> None:
        self.decision = decision
        self.reasons = reasons
        self.activity_count = activity_count


class ActivityEngine:
    def __init__(
        self,
        min_signals: int | None = None,
        max_age_days: int | None = None,
    ) -> None:
        self._min_signals = min_signals if min_signals is not None else DEFAULT_MIN_ACTIVITY_SIGNALS
        self._max_age_days = max_age_days if max_age_days is not None else DEFAULT_MAX_ACTIVITY_AGE_DAYS

    def evaluate(
        self,
        evidence: list[ActivityEvidence] | None = None,
        *,
        now: datetime | None = None,
    ) -> ActivityResult:
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)

        if not evidence:
            return ActivityResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    "No activity evidence found",
                    RejectionReason.NO_RECENT_ACTIVITY.value,
                ),
                activity_count=0,
            )

        recent: list[ActivityEvidence] = []
        for ev in evidence:
            ts = ev.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            age = (current - ts).days
            if age <= self._max_age_days:
                recent.append(ev)

        if len(recent) >= self._min_signals:
            return ActivityResult(
                decision=QualityDecision.ACCEPT,
                reasons=(
                    f"Found {len(recent)} recent activity signal(s) within {self._max_age_days}d",
                ),
                activity_count=len(recent),
            )

        return ActivityResult(
            decision=QualityDecision.REJECT,
            reasons=(
                f"Only {len(recent)} recent activity signal(s), need {self._min_signals}",
                RejectionReason.NO_RECENT_ACTIVITY.value,
            ),
            activity_count=len(recent),
        )

    def gate_name(self) -> str:
        return QualityGate.ACTIVITY_CHECK.value
