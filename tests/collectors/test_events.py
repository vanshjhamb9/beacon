from datetime import UTC, datetime

from collectors.events import NormalizedEvent


def test_normalized_event_generates_stable_idempotency_key() -> None:
    event = NormalizedEvent(
        source="Reddit",
        url="https://example.com/a",
        title=" Hiring Support ",
        content="Team is hiring support leaders",
        published_at=datetime(2026, 7, 10, 9, 0, tzinfo=UTC),
        metadata={"company": "Nike"},
    )

    same_event = NormalizedEvent(
        source="reddit",
        url="https://example.com/a",
        title="Hiring Support",
        content="Team is hiring support leaders",
        published_at=datetime(2026, 7, 10, 9, 0, tzinfo=UTC),
        metadata={"company": "Nike"},
    )

    assert event.source == "reddit"
    assert event.title == "Hiring Support"
    assert event.idempotency_key == same_event.idempotency_key
    assert event.stream_payload("trace-1")["event"]
