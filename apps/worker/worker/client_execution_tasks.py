import logging

from app.db.session import AsyncSessionLocal
from app.repositories.client_execution import ClientExecutionRepository
from app.services.client_execution import ClientExecutionPlatformService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="client_execution.refresh_health",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_health(self: object) -> dict:
    return run_async(_refresh_health())


@celery_app.task(
    name="client_execution.detect_upsells",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def detect_upsells(self: object) -> dict:
    return run_async(_detect_upsells())


@celery_app.task(
    name="client_execution.refresh_dashboard",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_dashboard(self: object) -> dict:
    return run_async(_refresh_dashboard())


async def _refresh_health() -> dict:
    async with AsyncSessionLocal() as session:
        service = ClientExecutionPlatformService(ClientExecutionRepository(session))
        result = await service.refresh_batch(limit=30)
        health = await service.health(limit=50)
        await session.commit()
    logger.info("AEP health refreshed", extra={"extra": result})
    return {"refreshed": result.get("refreshed", 0), "health_snapshots": health.get("total", 0)}


async def _detect_upsells() -> dict:
    async with AsyncSessionLocal() as session:
        service = ClientExecutionPlatformService(ClientExecutionRepository(session))
        await service.refresh_batch(limit=40)
        upsells = await service.upsells(limit=100)
        await session.commit()
    return {"upsells": upsells.get("total", 0)}


async def _refresh_dashboard() -> dict:
    async with AsyncSessionLocal() as session:
        service = ClientExecutionPlatformService(ClientExecutionRepository(session))
        await service.refresh_batch(limit=25)
        dash = await service.dashboard()
        await session.commit()
    return {"total_clients": dash.get("total_clients", 0), "scoring_version": dash.get("scoring_version")}
