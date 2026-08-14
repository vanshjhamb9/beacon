"""DQE v2 Buying Signal Engine — explicit allowed/not-allowed signal lists."""

from __future__ import annotations

from discovery_quality_engine.v2_schemas import BuyingSignalEvaluation, BuyingSignalVerdict


VALID_BUYING_SIGNALS = [
    "Hiring",
    "Expansion",
    "Migration",
    "Funding",
    "Compliance",
    "Digital Transformation",
    "Infrastructure Upgrade",
    "Cloud Migration",
    "Automation",
    "New Office",
    "ERP Migration",
    "CRM Migration",
    "Technology Replacement",
    "Executive Hiring",
    "Partnership",
    "API Launch",
    "Marketplace Launch",
]

NOT_BUYING_SIGNALS = [
    "Blog posts",
    "Marketing articles",
    "Random tweets",
    "Motivational posts",
    "Old Product Hunt launches",
]


class BuyingSignalEngineV2:
    """Evaluates buying signals against explicit allowed/not-allowed lists."""

    def __init__(
        self,
        *,
        valid_signals: list[str] | None = None,
        not_valid_signals: list[str] | None = None,
    ) -> None:
        self._valid_signals = [s.lower() for s in (valid_signals or VALID_BUYING_SIGNALS)]
        self._not_valid_signals = [s.lower() for s in (not_valid_signals or NOT_BUYING_SIGNALS)]

    @property
    def valid_signals(self) -> list[str]:
        return list(VALID_BUYING_SIGNALS)

    @property
    def not_valid_signals(self) -> list[str]:
        return list(NOT_BUYING_SIGNALS)

    def evaluate(
        self,
        *,
        signal_types: list[str],
    ) -> BuyingSignalEvaluation:
        valid: list[str] = []
        not_valid: list[str] = []
        borderline: list[str] = []

        for signal in signal_types:
            signal_lower = signal.lower().strip()
            if signal_lower in self._valid_signals:
                valid.append(signal)
            elif signal_lower in self._not_valid_signals:
                not_valid.append(signal)
            else:
                borderline.append(signal)

        reasons: list[str] = []
        evidence: list[str] = []

        if valid:
            reasons.append(f"Found {len(valid)} valid buying signal(s)")
            evidence.append(f"Valid signals: {', '.join(valid)}")
        if not_valid:
            reasons.append(f"Found {len(not_valid)} non-buying signal(s)")
            evidence.append(f"Not valid signals: {', '.join(not_valid)}")
        if borderline:
            reasons.append(f"Found {len(borderline)} borderline signal(s)")
            evidence.append(f"Borderline signals: {', '.join(borderline)}")

        verdict = self._determine_verdict(valid, not_valid, borderline)

        return BuyingSignalEvaluation(
            verdict=verdict,
            valid_signals=valid,
            not_valid_signals=not_valid,
            borderline_signals=borderline,
            reasons=reasons,
            evidence=evidence,
        )

    def _determine_verdict(
        self,
        valid: list[str],
        not_valid: list[str],
        borderline: list[str],
    ) -> BuyingSignalVerdict:
        if valid and not not_valid:
            return BuyingSignalVerdict.VALID
        elif not_valid and not valid:
            return BuyingSignalVerdict.NOT_VALID
        elif valid and not_valid:
            return BuyingSignalVerdict.BORDERLINE
        elif borderline and not valid and not not_valid:
            return BuyingSignalVerdict.BORDERLINE
        else:
            return BuyingSignalVerdict.NOT_VALID

    def is_valid_signal(self, signal_type: str) -> bool:
        """Check if a signal type is in the valid list."""
        return signal_type.lower().strip() in self._valid_signals

    def is_not_valid_signal(self, signal_type: str) -> bool:
        """Check if a signal type is in the not-valid list."""
        return signal_type.lower().strip() in self._not_valid_signals

    def should_reject(self, verdict: BuyingSignalVerdict) -> bool:
        """Check if a verdict should trigger rejection."""
        return verdict == BuyingSignalVerdict.NOT_VALID

    def should_hold(self, verdict: BuyingSignalVerdict) -> bool:
        """Check if a verdict should trigger HOLD."""
        return verdict == BuyingSignalVerdict.BORDERLINE
