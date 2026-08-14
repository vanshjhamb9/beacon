"""Deterministic signal filter — validates signal data integrity."""

from __future__ import annotations

from datetime import UTC, datetime

from discovery_quality_engine.quality_engine import (
    QualityDecision,
    QualityGate,
    RejectionReason,
)


class SignalFilterResult:
    __slots__ = ("decision", "reasons")

    def __init__(
        self,
        *,
        decision: QualityDecision,
        reasons: tuple[str, ...] = (),
    ) -> None:
        self.decision = decision
        self.reasons = reasons


class SignalFilter:
    def evaluate(
        self,
        *,
        signal_type: str | None = None,
        signal_source: str | None = None,
        signal_title: str | None = None,
        signal_timestamp: datetime | None = None,
    ) -> SignalFilterResult:
        reasons: list[str] = []

        if not signal_type or not signal_type.strip():
            reasons.append("Missing signal type")
            reasons.append(RejectionReason.UNKNOWN.value)
            return SignalFilterResult(
                decision=QualityDecision.REJECT,
                reasons=tuple(reasons),
            )

        if not signal_source or not signal_source.strip():
            reasons.append("Missing signal source")
            reasons.append(RejectionReason.UNKNOWN.value)
            return SignalFilterResult(
                decision=QualityDecision.REJECT,
                reasons=tuple(reasons),
            )

        if not signal_title or not signal_title.strip():
            reasons.append("Missing signal title")
            reasons.append(RejectionReason.UNKNOWN.value)
            return SignalFilterResult(
                decision=QualityDecision.REJECT,
                reasons=tuple(reasons),
            )

        if signal_timestamp is None:
            reasons.append("Missing signal timestamp")
            reasons.append(RejectionReason.UNKNOWN.value)
            return SignalFilterResult(
                decision=QualityDecision.REJECT,
                reasons=tuple(reasons),
            )

        now = datetime.now(UTC)
        if signal_timestamp.tzinfo is None:
            signal_timestamp = signal_timestamp.replace(tzinfo=UTC)
        if signal_timestamp > now:
            reasons.append("Signal timestamp is in the future")
            reasons.append(RejectionReason.UNKNOWN.value)
            return SignalFilterResult(
                decision=QualityDecision.REJECT,
                reasons=tuple(reasons),
            )

        reasons.append("Signal data validated")
        return SignalFilterResult(
            decision=QualityDecision.ACCEPT,
            reasons=tuple(reasons),
        )

    def gate_name(self) -> str:
        return "SIGNAL_DATA_INTEGRITY"
