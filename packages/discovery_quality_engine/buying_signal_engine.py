"""Deterministic buying signal gate — reject companies without real buying signals."""

from __future__ import annotations

from discovery_quality_engine.quality_engine import (
    QualityDecision,
    QualityGate,
    RejectionReason,
)

VALID_BUYING_SIGNALS: frozenset[str] = frozenset({
    "HIRING",
    "EXPANSION",
    "FUNDING",
    "TECHNOLOGY_ADOPTION",
    "COMPLIANCE",
    "EXECUTIVE_HIRING",
    "OFFICE_EXPANSION",
    "ACQUISITION",
    "INFRASTRUCTURE_UPGRADE",
    "SECURITY_INCIDENT",
    "API_RELEASE",
    "MARKETPLACE_EXPANSION",
    "PRODUCT_LAUNCH",
    "PARTNERSHIP",
})


class BuyingSignalResult:
    __slots__ = ("decision", "signals_found", "reasons")

    def __init__(
        self,
        *,
        decision: QualityDecision,
        signals_found: list[str],
        reasons: tuple[str, ...] = (),
    ) -> None:
        self.decision = decision
        self.signals_found = signals_found
        self.reasons = reasons


class BuyingSignalEngine:
    def __init__(self, valid_signals: frozenset[str] | None = None) -> None:
        self._valid_signals = valid_signals or VALID_BUYING_SIGNALS

    def evaluate(self, signal_types: list[str]) -> BuyingSignalResult:
        found = [s for s in signal_types if s.upper() in self._valid_signals]

        if found:
            return BuyingSignalResult(
                decision=QualityDecision.ACCEPT,
                signals_found=found,
                reasons=(f"Found {len(found)} valid buying signal(s): {', '.join(found)}",),
            )

        return BuyingSignalResult(
            decision=QualityDecision.REJECT,
            signals_found=[],
            reasons=(
                "No valid buying signals found",
                RejectionReason.NO_BUYING_SIGNAL.value,
            ),
        )

    def gate_name(self) -> str:
        return QualityGate.BUYING_SIGNAL.value
