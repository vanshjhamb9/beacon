from datetime import UTC, datetime, timedelta
from uuid import uuid4

from quality_engine.models import QualityEvent, SourceQualityProfile
from quality_engine.pipelines.quality_pipeline import QualityPipeline
from quality_engine.rules.defaults import default_rule_catalog
from quality_engine.scoring.duplicate import DuplicateScorer
from quality_engine.services.normalization import EventNormalizer


def test_normalization_removes_html_markdown_and_duplicate_whitespace() -> None:
    event = QualityEvent(
        id=uuid4(),
        source="RSS",
        url="https://example.com",
        title="<b>Nike</b>   launches",
        content="Nike [launches](https://example.com)    <i>support automation</i>",
        published_at=datetime.now(UTC),
    )

    normalized, _ = EventNormalizer().normalize(event)

    assert normalized.source == "rss"
    assert normalized.title == "Nike launches"
    assert normalized.content == "Nike launches support automation"


def test_duplicate_scorer_detects_exact_content_hash() -> None:
    event = QualityEvent(
        id=uuid4(),
        source="rss",
        url="https://example.com/nike",
        title="Nike opens UK office",
        content="Nike opened a UK support office with new hiring.",
        published_at=datetime.now(UTC),
    )
    normalized, _ = EventNormalizer().normalize(event)

    result = DuplicateScorer().score(normalized, known_hashes={normalized.content_hash})

    assert result.score == 100
    assert "exact_duplicate" in result.reason_codes


def test_expired_signal_is_not_fresh() -> None:
    event = QualityEvent(
        id=uuid4(),
        source="rss",
        url="https://example.com/old",
        title="Nike opened office",
        content="Nike opened a support office many months ago.",
        published_at=datetime.now(UTC) - timedelta(days=120),
        metadata={"company": "Nike"},
    )

    report = QualityPipeline(rules=default_rule_catalog()).process(
        event,
        source_profile=SourceQualityProfile(source="rss"),
    )

    assert "signal_expired" in report.reason_codes
    assert report.freshness_score == 10
