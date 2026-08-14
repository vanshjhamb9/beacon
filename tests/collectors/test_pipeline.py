from datetime import UTC, datetime

import pytest

from app.core.config import CollectorSourceConfig, Settings
from collectors.base import BaseCollector
from collectors.events import NormalizedEvent
from collectors.pipeline import CollectionPipeline


class FakeRedis:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    async def xadd(
        self,
        name: str,
        fields: dict[str, str],
        *,
        maxlen: int,
        approximate: bool,
    ) -> str:
        self.messages.append(fields)
        return "1-0"


class AllowAllRateLimiter:
    async def allow(self, source: str, *, limit: int, window_seconds: int = 60) -> bool:
        return True


class OneDuplicateDedupeStore:
    def __init__(self) -> None:
        self.seen: set[str] = set()

    async def mark_new(self, idempotency_key: str, *, ttl_seconds: int = 604_800) -> bool:
        if idempotency_key in self.seen:
            return False
        self.seen.add(idempotency_key)
        return True


class StaticCollector(BaseCollector):
    source = "rss"

    def __init__(self, events: list[NormalizedEvent]) -> None:
        self.events = events
        self.max_items = len(events)

    async def collect(self) -> list[NormalizedEvent]:
        return self.events


@pytest.mark.asyncio
async def test_pipeline_emits_only_new_events() -> None:
    event = NormalizedEvent(
        source="rss",
        url="https://example.com/nike",
        title="Nike launches product",
        content="Nike launched a new product.",
        published_at=datetime(2026, 7, 10, tzinfo=UTC),
        metadata={},
    )
    redis = FakeRedis()
    pipeline = CollectionPipeline(
        redis,
        Settings(environment="test"),
        rate_limiter=AllowAllRateLimiter(),
        dedupe_store=OneDuplicateDedupeStore(),
    )

    result = await pipeline.run_collector(
        StaticCollector([event, event]),
        CollectorSourceConfig(),
        trace_id="trace-1",
    )

    assert result.collected == 2
    assert result.emitted == 1
    assert result.duplicates == 1
    assert len(redis.messages) == 1
    assert "event" in redis.messages[0]
