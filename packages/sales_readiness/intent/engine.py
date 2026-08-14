from __future__ import annotations

from typing import Any

from sales_readiness.models.types import AttributedField, BuyingIntent, BuyingIntentLevel

INTENT_WEIGHTS: dict[str, float] = {
    "hiring": 12.0,
    "funding": 18.0,
    "product_launch": 14.0,
    "product launch": 14.0,
    "ai": 10.0,
    "openai": 12.0,
    "anthropic": 12.0,
    "gemini": 10.0,
    "automation": 10.0,
    "scaling": 8.0,
    "expansion": 8.0,
    "new_office": 8.0,
    "new offices": 8.0,
    "job": 6.0,
    "job openings": 8.0,
    "migration": 10.0,
    "cloud migration": 12.0,
    "customer support": 10.0,
    "sales hiring": 10.0,
    "engineering hiring": 8.0,
    "digital transformation": 12.0,
    "support hiring": 10.0,
}


class BuyingIntentEngine:
    """Deterministic buying intent from observed signals — never invent intent."""

    def evaluate(self, payload: dict[str, Any]) -> BuyingIntent:
        raw_signals = list(payload.get("signals") or []) + list(payload.get("intent_signals") or [])
        timeline = payload.get("timeline") or []
        for row in timeline:
            if isinstance(row, dict):
                raw_signals.append(row.get("signal_type") or row.get("summary") or "")
            else:
                raw_signals.append(str(row))

        narrative = str(payload.get("narrative") or payload.get("memory_summary") or "").lower()
        collected = payload.get("collected_at") or payload.get("last_seen_at")
        source = str(payload.get("source") or "timeline")

        matched: list[AttributedField] = []
        score = 0.0
        evidence: list[str] = []
        seen: set[str] = set()

        corpus = " ".join(str(s).lower() for s in raw_signals if s) + " " + narrative
        for key, weight in INTENT_WEIGHTS.items():
            if key in corpus and key not in seen:
                seen.add(key)
                score += weight
                matched.append(
                    AttributedField.of(
                        key,
                        source=source,
                        collected_at=collected,
                        confidence=min(95.0, 60.0 + weight),
                        evidence=[f"signal:{key}"],
                    )
                )
                evidence.append(f"intent:{key}:{weight}")

        score = min(100.0, round(score, 2))
        level = self._level(score)
        return BuyingIntent(level=level, score=score, signals=matched, evidence=evidence or ["no_intent_signals"])

    def _level(self, score: float) -> BuyingIntentLevel:
        if score >= 70:
            return BuyingIntentLevel.VERY_HIGH
        if score >= 45:
            return BuyingIntentLevel.HIGH
        if score >= 25:
            return BuyingIntentLevel.MEDIUM
        return BuyingIntentLevel.LOW
