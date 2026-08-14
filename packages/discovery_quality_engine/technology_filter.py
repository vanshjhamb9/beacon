"""Deterministic technology filter — reject AI companies by default."""

from __future__ import annotations

from discovery_quality_engine.quality_engine import (
    DEFAULT_AI_KEYWORDS,
    QualityDecision,
    QualityGate,
    RejectionReason,
)


class TechnologyFilterResult:
    __slots__ = ("decision", "reasons", "matched_keywords")

    def __init__(
        self,
        *,
        decision: QualityDecision,
        reasons: tuple[str, ...] = (),
        matched_keywords: list[str] | None = None,
    ) -> None:
        self.decision = decision
        self.reasons = reasons
        self.matched_keywords = matched_keywords or []


class TechnologyFilter:
    def __init__(
        self,
        ai_keywords: list[str] | None = None,
        enabled: bool = True,
    ) -> None:
        self._ai_keywords = [k.lower() for k in (ai_keywords or DEFAULT_AI_KEYWORDS)]
        self._enabled = enabled

    def evaluate(
        self,
        *,
        description: str | None = None,
        industry: str | None = None,
        tags: list[str] | None = None,
        company_name: str | None = None,
    ) -> TechnologyFilterResult:
        if not self._enabled:
            return TechnologyFilterResult(
                decision=QualityDecision.ACCEPT,
                reasons=("Technology filter disabled",),
            )

        texts = [t.lower() for t in filter(None, [description, industry, company_name])]
        if tags:
            texts.extend(t.lower() for t in tags)

        combined = " ".join(texts)
        matched = [kw for kw in self._ai_keywords if kw in combined]

        if matched:
            return TechnologyFilterResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    f"AI company detected — matched {len(matched)} keyword(s): {', '.join(matched[:3])}",
                    RejectionReason.AI_COMPANY.value,
                ),
                matched_keywords=matched,
            )

        return TechnologyFilterResult(
            decision=QualityDecision.ACCEPT,
            reasons=("No AI company keywords detected",),
        )

    def gate_name(self) -> str:
        return QualityGate.AI_COMPANY_FILTER.value
