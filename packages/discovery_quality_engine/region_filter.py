"""Deterministic region filter — reject companies in unsupported regions."""

from __future__ import annotations

from discovery_quality_engine.quality_engine import (
    DEFAULT_SUPPORTED_REGIONS,
    QualityDecision,
    QualityGate,
    RejectionReason,
)


class RegionFilterResult:
    __slots__ = ("decision", "reasons", "region")

    def __init__(
        self,
        *,
        decision: QualityDecision,
        reasons: tuple[str, ...] = (),
        region: str = "",
    ) -> None:
        self.decision = decision
        self.reasons = reasons
        self.region = region


class RegionFilter:
    def __init__(
        self,
        supported_regions: list[str] | None = None,
    ) -> None:
        self._supported = {r.upper() for r in (supported_regions or DEFAULT_SUPPORTED_REGIONS)}

    def evaluate(self, country: str | None) -> RegionFilterResult:
        if not country or not country.strip():
            return RegionFilterResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    "Missing country/region",
                    RejectionReason.UNSUPPORTED_REGION.value,
                ),
            )

        code = country.strip().upper()
        if code in self._supported:
            return RegionFilterResult(
                decision=QualityDecision.ACCEPT,
                reasons=(f"Region '{code}' is supported",),
                region=code,
            )

        return RegionFilterResult(
            decision=QualityDecision.REJECT,
            reasons=(
                f"Region '{code}' is not supported",
                RejectionReason.UNSUPPORTED_REGION.value,
            ),
            region=code,
        )

    def gate_name(self) -> str:
        return QualityGate.REGION_RULES.value
