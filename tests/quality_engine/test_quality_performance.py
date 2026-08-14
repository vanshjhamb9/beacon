from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from quality_engine import QualityEvent, QualityPipeline
from quality_engine.models import SourceQualityProfile


def test_quality_pipeline_processes_batch_with_low_latency() -> None:
    pipeline = QualityPipeline()
    events = [
        QualityEvent(
            id=uuid4(),
            source="rss",
            url=f"https://example.com/signal-{index}",
            title=f"Nike opens support office {index}",
            content="Nike opened a support office and is hiring customer support leaders.",
            published_at=datetime.now(UTC),
            metadata={"company": "Nike"},
        )
        for index in range(25)
    ]

    started = perf_counter()
    reports = [
        pipeline.process(event, source_profile=SourceQualityProfile(source="rss"))
        for event in events
    ]
    elapsed_ms = (perf_counter() - started) * 1000

    assert len(reports) == 25
    assert elapsed_ms < 500
