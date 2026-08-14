from __future__ import annotations

from typing import Any

from revenue_data_recovery.models.types import IntentIntelligenceResult, IntentScore

# Deterministic intent corpus — expand beyond weak SRE defaults
INTENT_WEIGHTS: dict[str, float] = {
    "hiring ai": 14.0,
    "hiring support": 12.0,
    "hiring developers": 10.0,
    "digital transformation": 14.0,
    "customer support growth": 12.0,
    "migration": 11.0,
    "funding": 18.0,
    "cloud": 9.0,
    "automation": 11.0,
    "manual process": 10.0,
    "legacy software": 12.0,
    "scaling": 9.0,
    "expansion": 9.0,
    "international growth": 10.0,
    "new product": 10.0,
    "crm": 8.0,
    "erp": 8.0,
    "operations": 7.0,
    "chatbots": 10.0,
    "openai": 12.0,
    "anthropic": 12.0,
    "gemini": 10.0,
    "llms": 11.0,
    "llm": 11.0,
    "hiring": 8.0,
    "customer support": 10.0,
    "zendesk": 9.0,
    "intercom": 8.0,
    "salesforce": 8.0,
    "hubspot": 8.0,
}


class IntentIntelligenceEngine:
    """Deterministic intent scoring from observed evidence only."""

    def score(self, payload: dict[str, Any]) -> IntentIntelligenceResult:
        corpus = self._corpus(payload)
        signals: list[IntentScore] = []
        total = 0.0
        evidence: list[str] = []

        for key, weight in INTENT_WEIGHTS.items():
            matched = key in corpus
            if matched:
                total += weight
                evidence.append(f"intent:{key}:{weight}")
            signals.append(
                IntentScore(
                    signal=key,
                    weight=weight,
                    matched=matched,
                    evidence=[f"matched:{key}"] if matched else [f"absent:{key}"],
                )
            )

        score = min(100.0, round(total, 2))
        matched_count = sum(1 for s in signals if s.matched)
        return IntentIntelligenceResult(
            score=score,
            level=self._level(score),
            signals=signals,
            matched_count=matched_count,
            evidence=evidence or ["no_intent_signals"],
        )

    def _level(self, score: float) -> str:
        if score >= 70:
            return "Very High"
        if score >= 45:
            return "High"
        if score >= 25:
            return "Medium"
        return "Low"

    def _corpus(self, payload: dict[str, Any]) -> str:
        parts: list[str] = [
            str(payload.get("narrative") or "").lower(),
            str(payload.get("memory_summary") or "").lower(),
            str(payload.get("description") or "").lower(),
        ]
        for s in payload.get("signals") or []:
            parts.append(str(s.get("value") if isinstance(s, dict) else s).lower())
        for row in payload.get("timeline") or []:
            if isinstance(row, dict):
                parts.append(str(row.get("signal_type") or "").lower())
                parts.append(str(row.get("summary") or "").lower())
            else:
                parts.append(str(row).lower())
        for t in payload.get("technologies") or []:
            parts.append(str(t.get("name") if isinstance(t, dict) else t).lower())
        for item in payload.get("evidence") or []:
            if isinstance(item, dict):
                parts.append(str(item.get("summary") or item.get("text") or "").lower())
            else:
                parts.append(str(item).lower())
        return " ".join(parts)
