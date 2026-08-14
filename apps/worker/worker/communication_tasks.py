import logging

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.communication import CommunicationPlatformService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="communication.process_queue",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_communication_queue(self: object, limit: int = 50) -> dict[str, int | bool | list]:
    return run_async(_process_communication_queue(limit=limit))


@celery_app.task(
    name="communication.snapshot_health",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def snapshot_system_health(self: object) -> dict[str, float | str]:
    return run_async(_snapshot_system_health())


@celery_app.task(
    name="communication.sync_gmail_replies",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def sync_gmail_replies(self: object, max_messages: int = 25) -> dict[str, object]:
    return run_async(_sync_gmail_replies(max_messages=max_messages))


@celery_app.task(
    name="communication.refresh_oauth",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_oauth(self: object) -> dict[str, object]:
    return run_async(_refresh_oauth())


async def _process_communication_queue(*, limit: int) -> dict[str, int | bool | list]:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        service = CommunicationPlatformService(session, settings)
        result = await service.process_queue(limit=limit)
        await session.commit()
    logger.info(
        "Processed communication queue",
        extra={"extra": {"processed": result.get("processed"), "sandbox": result.get("sandbox")}},
    )
    return result


async def _snapshot_system_health() -> dict[str, float | str]:
    from app.db.redis import create_redis_client

    settings = get_settings()
    redis = create_redis_client()
    try:
        async with AsyncSessionLocal() as session:
            service = CommunicationPlatformService(session, settings)
            report = await service.system_health(redis)
            await session.commit()
    finally:
        await redis.aclose()
    return {
        "overall_score": float(report["overall_score"]),
        "status": str(report["status"]),
        "mode": str(report["mode"]),
    }


async def _sync_gmail_replies(*, max_messages: int) -> dict[str, object]:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        service = CommunicationPlatformService(session, settings)
        result = await service.sync_gmail_replies(max_messages=max_messages)
        await session.commit()
    # After Communication Gateway sync, refresh Sales Intelligence for touched companies.
    try:
        from worker.sales_intelligence_tasks import refresh_from_replies

        refresh_from_replies.delay(limit=40)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to enqueue sales intelligence refresh after Gmail sync")
    logger.info("Synced Gmail replies", extra={"extra": result})
    return result


async def _refresh_oauth() -> dict[str, object]:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        service = CommunicationPlatformService(session, settings)
        result = await service.refresh_oauth_tokens()
        await session.commit()
    logger.info("Refreshed OAuth tokens", extra={"extra": result})
    return result
