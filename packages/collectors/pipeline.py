import logging
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.core.config import CollectorSourceConfig, Settings
from collectors.base import BaseCollector
from collectors.dedupe import RedisDedupeStore
from collectors.events import NormalizedEvent
from collectors.rate_limit import RedisRateLimiter

logger = logging.getLogger(__name__)


class StreamPublisher(Protocol):
    async def xadd(
        self,
        name: str,
        fields: dict[str, str],
        *,
        maxlen: int,
        approximate: bool,
    ) -> str:
        ...


class RateLimiter(Protocol):
    async def allow(self, source: str, *, limit: int, window_seconds: int = 60) -> bool:
        ...


class DedupeStore(Protocol):
    async def mark_new(self, idempotency_key: str, *, ttl_seconds: int = 604_800) -> bool:
        ...


@dataclass(frozen=True)
class PipelineResult:
    source: str
    collected: int
    emitted: int
    duplicates: int
    rate_limited: bool
    trace_id: str


class CollectionPipeline:
    def __init__(
        self,
        redis: StreamPublisher,
        settings: Settings,
        *,
        rate_limiter: RateLimiter | None = None,
        dedupe_store: DedupeStore | None = None,
    ) -> None:
        self.redis = redis
        self.settings = settings
        self.rate_limiter = rate_limiter or RedisRateLimiter(redis)
        self.dedupe_store = dedupe_store or RedisDedupeStore(redis)

    async def run_collector(
        self,
        collector: BaseCollector,
        config: CollectorSourceConfig,
        *,
        trace_id: str | None = None,
    ) -> PipelineResult:
        trace_id = trace_id or uuid.uuid4().hex
        source = collector.source

        if not self.settings.feature_flags.collectors_enabled or not config.enabled:
            logger.info("Collector disabled", extra={"extra": {"source": source, "trace_id": trace_id}})
            return PipelineResult(source, 0, 0, 0, False, trace_id)

        allowed = await self.rate_limiter.allow(source, limit=config.rate_limit_per_minute)
        if not allowed:
            logger.warning("Collector rate limited", extra={"extra": {"source": source, "trace_id": trace_id}})
            return PipelineResult(source, 0, 0, 0, True, trace_id)

        events = await collector.collect()
        from collectors.freshness import FRESH_HOURS, filter_fresh_events

        events = filter_fresh_events(list(events), max_age_hours=FRESH_HOURS)
        emitted, duplicates = await self.emit_events(events, trace_id=trace_id)

        return PipelineResult(
            source=source,
            collected=len(events),
            emitted=emitted,
            duplicates=duplicates,
            rate_limited=False,
            trace_id=trace_id,
        )

    async def emit_events(
        self,
        events: Sequence[NormalizedEvent],
        *,
        trace_id: str,
    ) -> tuple[int, int]:
        emitted = 0
        duplicates = 0

        for event in events:
            is_new = await self.dedupe_store.mark_new(event.idempotency_key)
            if not is_new:
                duplicates += 1
                continue

            await self.redis.xadd(
                self.settings.collector_stream_name,
                event.stream_payload(trace_id),
                maxlen=self.settings.collector_stream_max_length,
                approximate=True,
            )
            emitted += 1

        return emitted, duplicates
