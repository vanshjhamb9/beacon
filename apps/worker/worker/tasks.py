import json
import logging
import time
from datetime import datetime
from typing import Any

import httpx
from redis.asyncio import Redis
from redis.exceptions import ResponseError

from app.core.config import CollectorSourceConfig, Settings, get_settings
from app.db.redis import create_redis_client
from app.db.session import AsyncSessionLocal
from app.repositories.acquisition import AcquisitionRepository
from app.repositories.raw_event import RawEventRepository
from app.repositories.source_health import SourceHealthRepository
from collectors.factory import build_collector_registry
from collectors.pipeline import CollectionPipeline
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="worker.health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _collector_config(settings: Settings, source: str) -> CollectorSourceConfig:
    match source:
        case "reddit":
            return settings.reddit_collector
        case "rss":
            return settings.rss_collector
        case "hacker_news":
            return settings.hacker_news_collector
        case "product_hunt":
            return settings.product_hunt_collector
        case "github_trending":
            return settings.github_trending_collector
        case "indie_hackers":
            return settings.indie_hackers_collector
        case "sec_edgar":
            return settings.sec_edgar_collector
        case "devto":
            return settings.devto_collector
        case "pain_signals":
            return settings.pain_signals_collector
        case _:
            raise ValueError(f"Unknown collector source '{source}'.")


@celery_app.task(
    name="collectors.collect_source",
    bind=True,
    autoretry_for=(httpx.HTTPError, TimeoutError, ValueError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def collect_source(self: object, source: str) -> dict[str, object]:
    return run_async(_collect_source(source))


async def _collect_source(source: str) -> dict[str, object]:
    settings = get_settings()
    redis = create_redis_client()
    started = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as http_client:
            registry = build_collector_registry(settings, lambda: http_client)
            try:
                collector = registry.create(source)
            except KeyError:
                return {
                    "source": source,
                    "collected": 0,
                    "emitted": 0,
                    "duplicates": 0,
                    "rate_limited": False,
                    "trace_id": None,
                    "warning": f"No collector registered for source '{source}' — skipping",
                }
            pipeline = CollectionPipeline(redis, settings)
            result = await pipeline.run_collector(collector, _collector_config(settings, source))

        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        success = not result.rate_limited
        if success:
            await _record_source_success(source, latency_ms)
        else:
            await _record_source_failure(source, "rate_limited")

        await _record_collector_run(
            source=source,
            collected=result.collected,
            emitted=result.emitted,
            duplicates=result.duplicates,
            rate_limited=result.rate_limited,
            success=success,
            latency_ms=latency_ms,
            error="rate_limited" if result.rate_limited else None,
            trace_id=result.trace_id,
        )
        await _record_ingestion_event(
            collector=source,
            status="collected" if success else "rate_limited",
            reason=None if success else "rate_limited",
            duration=latency_ms / 1000.0,
            payload={"count": result.emitted, "collected": result.collected, "duplicates": result.duplicates},
        )
        return {
            "source": result.source,
            "collected": result.collected,
            "emitted": result.emitted,
            "duplicates": result.duplicates,
            "rate_limited": result.rate_limited,
            "trace_id": result.trace_id,
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.exception(
            "Collector failed",
            extra={"extra": {"source": source, "error": str(exc)}},
        )
        try:
            await _record_source_failure(source, str(exc))
        except Exception:
            logger.exception(
                "Failed to persist source health failure",
                extra={"extra": {"source": source}},
            )
        try:
            await _record_ingestion_event(
                collector=source,
                status="failed",
                reason=str(exc)[:240],
                duration=latency_ms / 1000.0,
            )
        except Exception:
            logger.exception(
                "Failed to persist ingestion event",
                extra={"extra": {"source": source}},
            )
        try:
            await _record_collector_run(
                source=source,
                collected=0,
                emitted=0,
                duplicates=0,
                rate_limited=False,
                success=False,
                latency_ms=latency_ms,
                error=str(exc),
                trace_id=None,
            )
        except Exception:
            logger.exception(
                "Failed to persist collector run failure",
                extra={"extra": {"source": source}},
            )
        raise
    finally:
        await redis.aclose()


@celery_app.task(
    name="collectors.persist_raw_events",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def persist_raw_events(self: object) -> dict[str, int]:
    return run_async(_persist_raw_events())


async def _persist_raw_events() -> dict[str, int]:
    settings = get_settings()
    redis = create_redis_client()
    try:
        await _ensure_consumer_group(redis, settings)

        records = await redis.xreadgroup(
            settings.collector_consumer_group,
            settings.collector_consumer_name,
            {settings.collector_stream_name: ">"},
            count=settings.collector_persist_batch_size,
            block=1_000,
        )

        persisted = 0
        duplicates = 0
        acknowledged = 0

        async with AsyncSessionLocal() as session:
            repository = RawEventRepository(session)
            for _, messages in records or []:
                for stream_id, fields in messages:
                    payload = _decode_stream_event(fields)
                    created = await repository.create_if_new(
                        {
                            "source": payload["source"],
                            "url": payload["url"],
                            "title": payload["title"],
                            "content": payload["content"],
                            "published_at": datetime.fromisoformat(payload["published_at"]),
                            "event_metadata": payload["metadata"],
                            "idempotency_key": payload["idempotency_key"],
                            "event_hash": payload["event_hash"],
                            "trace_id": payload.get("trace_id"),
                            "stream_id": stream_id,
                        }
                    )
                    if not created:
                        duplicates += 1
                    else:
                        persisted += 1

                    await redis.xack(
                        settings.collector_stream_name,
                        settings.collector_consumer_group,
                        stream_id,
                    )
                    acknowledged += 1

            await session.commit()

        return {"persisted": persisted, "duplicates": duplicates, "acknowledged": acknowledged}
    finally:
        await redis.aclose()


async def _ensure_consumer_group(redis: Redis, settings: Settings) -> None:
    try:
        await redis.xgroup_create(
            settings.collector_stream_name,
            settings.collector_consumer_group,
            id="0",
            mkstream=True,
        )
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def _decode_stream_event(fields: dict[str, Any]) -> dict[str, Any]:
    raw_event = fields.get("event")
    if not isinstance(raw_event, str):
        raise ValueError("Stream message is missing an event payload.")
    payload = json.loads(raw_event)
    if not isinstance(payload, dict):
        raise ValueError("Stream event payload must be an object.")
    return payload


async def _record_source_success(source: str, latency_ms: float) -> None:
    settings = get_settings()
    if not settings.feature_flags.source_health_monitoring_enabled:
        return

    async with AsyncSessionLocal() as session:
        repository = SourceHealthRepository(session)
        await repository.record_success(source, latency_ms)
        await session.commit()


async def _record_source_failure(source: str, error: str) -> None:
    settings = get_settings()
    if not settings.feature_flags.source_health_monitoring_enabled:
        return

    async with AsyncSessionLocal() as session:
        repository = SourceHealthRepository(session)
        await repository.record_failure(source, error)
        await session.commit()


async def _record_ingestion_event(
    *,
    collector: str,
    status: str,
    company: str | None = None,
    reason: str | None = None,
    duration: float | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    from app.services.operations_center import OperationsCenterService

    async with AsyncSessionLocal() as session:
        service = OperationsCenterService(session)
        await service.emit_ingestion_event(
            collector=collector,
            status=status,
            company=company,
            reason=reason,
            duration=duration,
            payload=payload,
        )
        await session.commit()


async def _record_collector_run(
    *,
    source: str,
    collected: int,
    emitted: int,
    duplicates: int,
    rate_limited: bool,
    success: bool,
    latency_ms: float,
    error: str | None,
    trace_id: str | None,
) -> None:
    async with AsyncSessionLocal() as session:
        repository = AcquisitionRepository(session)
        await repository.record_run(
            source=source,
            collected=collected,
            emitted=emitted,
            duplicates=duplicates,
            rate_limited=rate_limited,
            success=success,
            latency_ms=latency_ms,
            error=error,
            trace_id=trace_id,
        )
        await session.commit()
