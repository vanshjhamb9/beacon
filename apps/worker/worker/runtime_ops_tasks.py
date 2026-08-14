"""Periodic Beat heartbeat for operations dashboard."""

from __future__ import annotations

import logging

from app.db.redis import create_redis_client
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)

HEARTBEAT_KEY = "beacon:celery:beat:heartbeat"
HEARTBEAT_TTL_SECONDS = 120


@celery_app.task(name="runtime_ops.beat_heartbeat")
def beat_heartbeat() -> dict[str, object]:
    return run_async(_beat_heartbeat())


async def _beat_heartbeat() -> dict[str, object]:
    redis = create_redis_client()
    try:
        await redis.set(HEARTBEAT_KEY, "1", ex=HEARTBEAT_TTL_SECONDS)
        logger.info("Beat heartbeat written", extra={"extra": {"key": HEARTBEAT_KEY}})
        return {"ok": True, "key": HEARTBEAT_KEY, "ttl": HEARTBEAT_TTL_SECONDS}
    finally:
        await redis.aclose()
