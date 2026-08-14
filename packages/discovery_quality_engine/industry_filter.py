"""Deterministic industry filter — reject companies outside allowed industries."""

from __future__ import annotations

from discovery_quality_engine.quality_engine import (
    QualityDecision,
    QualityGate,
    RejectionReason,
)


DEFAULT_ALLOWED_INDUSTRIES: frozenset[str] = frozenset({
    "technology",
    "software",
    "saas",
    "fintech",
    "healthtech",
    "edtech",
    "ecommerce",
    "retail",
    "manufacturing",
    "healthcare",
    "finance",
    "insurance",
    "real estate",
    "construction",
    "energy",
    "utilities",
    "transportation",
    "logistics",
    "telecommunications",
    "media",
    "entertainment",
    "education",
    "professional services",
    "consulting",
    "legal",
    "accounting",
    "marketing",
    "advertising",
    "nonprofit",
    "government",
    "agriculture",
    "mining",
    "automotive",
    "aerospace",
    "defense",
    "pharmaceuticals",
    "biotechnology",
    "food and beverage",
    "hospitality",
    "travel",
    "sports",
    "recreation",
})


class IndustryFilterResult:
    __slots__ = ("decision", "reasons", "industry")

    def __init__(
        self,
        *,
        decision: QualityDecision,
        reasons: tuple[str, ...] = (),
        industry: str = "",
    ) -> None:
        self.decision = decision
        self.reasons = reasons
        self.industry = industry


class IndustryFilter:
    def __init__(
        self,
        allowed_industries: frozenset[str] | None = None,
    ) -> None:
        self._allowed = {i.lower() for i in (allowed_industries or DEFAULT_ALLOWED_INDUSTRIES)}

    def evaluate(self, industry: str | None) -> IndustryFilterResult:
        if not industry or not industry.strip():
            return IndustryFilterResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    "Missing industry",
                    RejectionReason.OUTSIDE_ICP.value,
                ),
            )

        normalized = industry.lower().strip()
        if not self._allowed:
            return IndustryFilterResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    f"No allowed industries configured; '{industry}' rejected",
                    RejectionReason.OUTSIDE_ICP.value,
                ),
                industry=normalized,
            )

        normalized = industry.lower().strip()
        if normalized in self._allowed:
            return IndustryFilterResult(
                decision=QualityDecision.ACCEPT,
                reasons=(f"Industry '{industry}' is allowed",),
                industry=normalized,
            )

        for allowed in self._allowed:
            if allowed in normalized or normalized in allowed:
                return IndustryFilterResult(
                    decision=QualityDecision.ACCEPT,
                    reasons=(f"Industry '{industry}' matches allowed '{allowed}'",),
                    industry=normalized,
                )

        return IndustryFilterResult(
            decision=QualityDecision.REJECT,
            reasons=(
                f"Industry '{industry}' is not in allowed list",
                RejectionReason.OUTSIDE_ICP.value,
            ),
            industry=normalized,
        )

    def gate_name(self) -> str:
        return QualityGate.INDUSTRY_RULES.value
