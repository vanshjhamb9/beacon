"""Deterministic freshness gate — reject stale opportunities."""

from __future__ import annotations

from datetime import UTC, datetime

from discovery_quality_engine.quality_engine import (
    DEFAULT_FRESHNESS_LIMITS,
    FreshnessLimit,
    QualityDecision,
    QualityGate,
    RejectionReason,
)


class FreshnessResult:
    __slots__ = ("decision", "age_days", "max_age_days", "signal_type", "reasons")

    def __init__(
        self,
        *,
        decision: QualityDecision,
        age_days: int,
        max_age_days: int,
        signal_type: str,
        reasons: tuple[str, ...] = (),
    ) -> None:
        self.decision = decision
        self.age_days = age_days
        self.max_age_days = max_age_days
        self.signal_type = signal_type
        self.reasons = reasons


class FreshnessEngine:
    def __init__(
        self,
        limits: list[FreshnessLimit] | None = None,
    ) -> None:
        self._limits = {
            limit.signal_type.upper(): limit.max_age_days
            for limit in (limits or DEFAULT_FRESHNESS_LIMITS)
        }

    def evaluate(
        self,
        signal_type: str,
        signal_timestamp: datetime,
        *,
        now: datetime | None = None,
    ) -> FreshnessResult:
        current = now or datetime.now(UTC)
        if signal_timestamp.tzinfo is None:
            signal_timestamp = signal_timestamp.replace(tzinfo=UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)

        age_days = max((current - signal_timestamp).days, 0)
        max_age = self._limits.get(signal_type.upper(), 90)

        if age_days <= max_age:
            return FreshnessResult(
                decision=QualityDecision.ACCEPT,
                age_days=age_days,
                max_age_days=max_age,
                signal_type=signal_type,
                reasons=(f"Signal age {age_days}d within limit {max_age}d",),
            )

        return FreshnessResult(
            decision=QualityDecision.REJECT,
            age_days=age_days,
            max_age_days=max_age,
            signal_type=signal_type,
            reasons=(
                f"Signal age {age_days}d exceeds maximum {max_age}d for {signal_type}",
                RejectionReason.STALE_SIGNAL.value,
            ),
        )

    def gate_name(self) -> str:
        return QualityGate.FRESHNESS.value
