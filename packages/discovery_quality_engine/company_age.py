"""Deterministic company age filter."""

from __future__ import annotations

from discovery_quality_engine.quality_engine import (
    QualityDecision,
    QualityGate,
    RejectionReason,
)

DEFAULT_MIN_COMPANY_AGE_DAYS: int = 30
DEFAULT_MAX_COMPANY_AGE_DAYS: int = 36500


class CompanyAgeResult:
    __slots__ = ("decision", "reasons", "age_days")

    def __init__(
        self,
        *,
        decision: QualityDecision,
        reasons: tuple[str, ...] = (),
        age_days: int = 0,
    ) -> None:
        self.decision = decision
        self.reasons = reasons
        self.age_days = age_days


class CompanyAgeFilter:
    def __init__(
        self,
        min_age_days: int | None = None,
        max_age_days: int | None = None,
    ) -> None:
        self._min_age = min_age_days if min_age_days is not None else DEFAULT_MIN_COMPANY_AGE_DAYS
        self._max_age = max_age_days if max_age_days is not None else DEFAULT_MAX_COMPANY_AGE_DAYS

    def evaluate(self, age_days: int | None) -> CompanyAgeResult:
        if age_days is None:
            return CompanyAgeResult(
                decision=QualityDecision.ACCEPT,
                reasons=("Company age unknown — passing through",),
                age_days=0,
            )

        if age_days < self._min_age:
            return CompanyAgeResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    f"Company age {age_days}d below minimum {self._min_age}d",
                    RejectionReason.OUTSIDE_ICP.value,
                ),
                age_days=age_days,
            )

        if age_days > self._max_age:
            return CompanyAgeResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    f"Company age {age_days}d above maximum {self._max_age}d",
                    RejectionReason.OUTSIDE_ICP.value,
                ),
                age_days=age_days,
            )

        return CompanyAgeResult(
            decision=QualityDecision.ACCEPT,
            reasons=(f"Company age {age_days}d within range [{self._min_age}, {self._max_age}]",),
            age_days=age_days,
        )

    def gate_name(self) -> str:
        return QualityGate.ICP_FILTER.value
