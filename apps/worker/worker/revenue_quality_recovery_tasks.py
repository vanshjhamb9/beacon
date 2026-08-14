import logging

from app.db.session import AsyncSessionLocal
from app.services.revenue_quality_recovery import RevenueQualityRecoveryService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="revenue_quality.process_pending",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_revenue_quality(self: object, limit: int = 80) -> dict:
    return run_async(_process(limit=limit))


@celery_app.task(
    name="revenue_quality.daily_kpi",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def daily_revenue_quality_kpi(self: object) -> dict:
    return run_async(_kpi())


async def _process(*, limit: int) -> dict:
    async with AsyncSessionLocal() as session:
        service = RevenueQualityRecoveryService(session)
        result = await service.process_pending(limit=limit)
        await service.ensure_golden_dataset()
        kpi = await service.daily_kpi()
    logger.info("Processed revenue quality batch", extra={"extra": {**result, "kpi": kpi}})
    return {**result, "kpi": kpi}


async def _kpi() -> dict:
    async with AsyncSessionLocal() as session:
        service = RevenueQualityRecoveryService(session)
        kpi = await service.daily_kpi()
        acceptance = await service.acceptance()
    return {"kpi": kpi, "acceptance": acceptance, "scoring_version": "rqp-v1"}
