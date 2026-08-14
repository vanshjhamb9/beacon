"""Intent detector — scores companies against intent patterns.

Returns intent_level, intent_score, matched_signals.
Does NOT assume intent from ICP signals (funding, industry, tech).
"""

from __future__ import annotations

from datetime import date

from packages.intent_engine.patterns import (
    ACTIVE_REQUIREMENT_PATTERNS,
    EARLY_INTENT_PATTERNS,
    EVALUATION_PATTERNS,
    COMPANY_OPPORTUNITY_PATTERNS,
    IntentPattern,
)
from packages.opportunity_intelligence.canonical import IntentLevel, IntentSignal


def detect_intent(
    text: str,
    business_unit: str | None = None,
    detection_date: date | None = None,
) -> list[IntentSignal]:
    """Detect intent signals from text content.

    Args:
        text: Lowercased company text (job postings, website, funding articles, etc.)
        business_unit: Optional filter to only match patterns for a specific BU.
        detection_date: Date of detection (defaults to today).

    Returns:
        List of IntentSignal sorted by score descending.
    """
    if detection_date is None:
        detection_date = date.today()

    text_lower = text.lower()
    signals: list[IntentSignal] = []

    all_patterns = (
        ACTIVE_REQUIREMENT_PATTERNS
        + EVALUATION_PATTERNS
        + EARLY_INTENT_PATTERNS
        + COMPANY_OPPORTUNITY_PATTERNS
    )

    for pattern in all_patterns:
        if business_unit and pattern.business_unit != business_unit:
            continue

        matched_keywords = [kw for kw in pattern.keywords if kw in text_lower]
        if not matched_keywords:
            continue

        # Score boost: more keywords matched = higher confidence
        keyword_boost = min(len(matched_keywords) * 3, 10)
        intent_score = min(pattern.base_score + keyword_boost, 100.0)

        intent_level = IntentLevel(pattern.intent_level)
        signal = IntentSignal(
            signal_text=f"Matched: {', '.join(matched_keywords[:3])}",
            signal_source=f"intent_pattern:{pattern.description}",
            signal_url="",
            intent_level=intent_level,
            intent_score=intent_score,
            detected_at=detection_date,
        )
        signals.append(signal)

    signals.sort(key=lambda s: s.intent_score, reverse=True)
    return signals


def classify_overall_intent(signals: list[IntentSignal]) -> tuple[IntentLevel, float]:
    """Classify overall intent from a list of signals.

    Takes the strongest signal as the overall intent level.
    Score is the max score found (not average — one strong signal > many weak ones).
    """
    if not signals:
        return IntentLevel.NO_INTENT, 0.0

    strongest = signals[0]
    return strongest.intent_level, strongest.intent_score
