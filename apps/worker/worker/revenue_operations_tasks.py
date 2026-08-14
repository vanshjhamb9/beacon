import logging

from app.db.session import AsyncSessionLocal
from app.repositories.revenue_operations import RevenueOperationsRepository
from app.services.revenue_operations import RevenueOperationsPlatformService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="revenue_operations.refresh_dashboard",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_dashboard(self: object) -> dict:
    return run_async(_refresh_dashboard())


@celery_app.task(
    name="revenue_operations.refresh_forecast",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_forecast(self: object) -> dict:
    return run_async(_refresh_forecast())


@celery_app.task(
    name="revenue_operations.refresh_alerts",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_alerts(self: object) -> dict:
    return run_async(_refresh_alerts())


@celery_app.task(
    name="revenue_operations.daily_learning",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def daily_learning(self: object) -> dict:
    return run_async(_daily_learning())


async def _refresh_dashboard() -> dict:
    async with AsyncSessionLocal() as session:
        service = RevenueOperationsPlatformService(RevenueOperationsRepository(session))
        pack = await service.refresh()
        await session.commit()
    logger.info("ROC dashboard refreshed", extra={"extra": {"score": pack.get("revenue_score")}})
    return {
        "revenue_score": pack.get("revenue_score"),
        "pipeline_value": pack.get("pipeline_value"),
        "alerts": len((pack.get("alerts") or [])),
    }


async def _refresh_forecast() -> dict:
    async with AsyncSessionLocal() as session:
        service = RevenueOperationsPlatformService(RevenueOperationsRepository(session))
        pack = await service.forecast(refresh=True)
        await session.commit()
    return {
        "this_week": pack.get("this_week"),
        "this_month": pack.get("this_month"),
        "confidence_score": pack.get("confidence_score"),
    }


async def _refresh_alerts() -> dict:
    async with AsyncSessionLocal() as session:
        service = RevenueOperationsPlatformService(RevenueOperationsRepository(session))
        await service.refresh()
        alerts = await service.alerts(lifecycle="new", limit=100)
        await session.commit()
    return {"new_alerts": alerts.get("total", 0)}


async def _daily_learning() -> dict:
    async with AsyncSessionLocal() as session:
        service = RevenueOperationsPlatformService(RevenueOperationsRepository(session))
        pack = await service.refresh()
        learning = await service.learning(status="pending_approval", limit=100)
        await session.commit()
    return {
        "recommendations": learning.get("total", 0),
        "scoring_version": pack.get("scoring_version"),
    }
