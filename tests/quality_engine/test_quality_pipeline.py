from datetime import UTC, datetime
from uuid import uuid4

from quality_engine import QualityDecision, QualityEvent, QualityPipeline
from quality_engine.models import SourceQualityProfile


def test_quality_pipeline_accepts_complete_business_signal() -> None:
    event = QualityEvent(
        id=uuid4(),
        source="rss",
        url="https://nike.com/news/support-expansion",
        title="Nike opens UK customer support office",
        content="Nike opened a new UK customer support office and is hiring support leaders.",
        published_at=datetime.now(UTC),
        collected_at=datetime.now(UTC),
        metadata={"company": "Nike", "language": "en"},
    )

    report = QualityPipeline().process(
        event,
        source_profile=SourceQualityProfile(source="rss", average_quality=88.0),
    )

    assert report.decision == QualityDecision.ACCEPT
    assert report.overall_quality_score >= 72
    assert report.normalized_event is not None
    assert report.normalized_event.source == "rss"
    assert len(report.stage_results) == 9


def test_quality_pipeline_rejects_spam_and_invalid_url() -> None:
    event = QualityEvent(
        id=uuid4(),
        source="reddit",
        url="not-a-url",
        title="Buy now buy now buy now",
        content="Buy now affiliate promo code click here limited time offer buy now.",
        published_at=datetime.now(UTC),
        metadata={},
    )

    report = QualityPipeline().process(
        event,
        source_profile=SourceQualityProfile(source="reddit", spam_rate=0.4),
    )

    assert report.decision == QualityDecision.REJECT
    assert "invalid_url" in report.reason_codes
    assert "spam_keyword_match" in report.reason_codes
