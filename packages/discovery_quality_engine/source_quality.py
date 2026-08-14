"""Deterministic source trust engine — reject low-trust sources."""

from __future__ import annotations

from discovery_quality_engine.quality_engine import (
    DEFAULT_MIN_SOURCE_TRUST,
    DEFAULT_SOURCE_TRUST,
    QualityDecision,
    QualityGate,
    RejectionReason,
)


class SourceTrustResult:
    __slots__ = ("decision", "reasons", "trust_score", "source")

    def __init__(
        self,
        *,
        decision: QualityDecision,
        reasons: tuple[str, ...] = (),
        trust_score: float = 0.0,
        source: str = "",
    ) -> None:
        self.decision = decision
        self.reasons = reasons
        self.trust_score = trust_score
        self.source = source


class SourceQualityEngine:
    def __init__(
        self,
        source_trust: dict[str, float] | None = None,
        min_trust: float | None = None,
    ) -> None:
        self._trust = {k.lower(): v for k, v in (source_trust or DEFAULT_SOURCE_TRUST).items()}
        self._min_trust = min_trust if min_trust is not None else DEFAULT_MIN_SOURCE_TRUST

    def evaluate(self, source: str) -> SourceTrustResult:
        normalized = source.lower().strip()
        trust = self._trust.get(normalized, 50.0)

        if trust >= self._min_trust:
            return SourceTrustResult(
                decision=QualityDecision.ACCEPT,
                reasons=(f"Source '{source}' trust {trust:.0f} >= {self._min_trust:.0f}",),
                trust_score=trust,
                source=source,
            )

        return SourceTrustResult(
            decision=QualityDecision.REJECT,
            reasons=(
                f"Source '{source}' trust {trust:.0f} below minimum {self._min_trust:.0f}",
                RejectionReason.LOW_SOURCE_TRUST.value,
            ),
            trust_score=trust,
            source=source,
        )

    def gate_name(self) -> str:
        return QualityGate.SOURCE_TRUST.value
