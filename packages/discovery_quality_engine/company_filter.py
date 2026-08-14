"""Deterministic company validation gate."""

from __future__ import annotations

from discovery_quality_engine.quality_engine import (
    QualityDecision,
    QualityGate,
    RejectionReason,
)


class CompanyValidationResult:
    __slots__ = ("decision", "reasons")

    def __init__(
        self,
        *,
        decision: QualityDecision,
        reasons: tuple[str, ...] = (),
    ) -> None:
        self.decision = decision
        self.reasons = reasons


class CompanyFilter:
    def evaluate(
        self,
        *,
        company_name: str | None = None,
        website: str | None = None,
        domain: str | None = None,
    ) -> CompanyValidationResult:
        reasons: list[str] = []

        if not company_name or not company_name.strip():
            reasons.append("Missing company name")
            reasons.append(RejectionReason.UNKNOWN.value)
            return CompanyValidationResult(
                decision=QualityDecision.REJECT,
                reasons=tuple(reasons),
            )

        name = company_name.strip()
        if len(name) < 2:
            reasons.append("Company name too short")
            reasons.append(RejectionReason.UNKNOWN.value)
            return CompanyValidationResult(
                decision=QualityDecision.REJECT,
                reasons=tuple(reasons),
            )

        reasons.append("Company name validated")
        return CompanyValidationResult(
            decision=QualityDecision.ACCEPT,
            reasons=tuple(reasons),
        )

    def gate_name(self) -> str:
        return QualityGate.COMPANY_VALIDATION.value
