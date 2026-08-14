from datetime import UTC, datetime

from intelligence.signal_classifier import RuleBasedSignalClassifier
from intelligence.types import RawSignal, SignalCategory


def test_rule_based_classifier_detects_multiple_business_signals() -> None:
    signal = RawSignal(
        source="reddit",
        url="https://reddit.com/r/startups/comments/1",
        title="Acme raised Series A and is hiring support",
        content="The company raised funding and opened a new office.",
        published_at=datetime(2026, 7, 10, tzinfo=UTC),
    )

    categories = {item.category for item in RuleBasedSignalClassifier().classify(signal)}

    assert SignalCategory.FUNDING in categories
    assert SignalCategory.HIRING in categories
    assert SignalCategory.EXPANSION in categories


def test_rule_based_classifier_falls_back_to_market_mention() -> None:
    signal = RawSignal(
        source="rss",
        url="https://example.com/post",
        title="Weekly roundup of industry links",
        content="A short digest without specialty keywords.",
        published_at=datetime(2026, 7, 10, tzinfo=UTC),
    )

    results = RuleBasedSignalClassifier().classify(signal)

    assert len(results) == 1
    assert results[0].category == SignalCategory.MARKET_MENTION
