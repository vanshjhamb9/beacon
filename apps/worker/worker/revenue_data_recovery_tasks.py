import logging

from app.db.session import AsyncSessionLocal
from app.services.revenue_data_recovery import RevenueDataRecoveryService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="revenue_data_recovery.process_pending",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_revenue_data_recovery(self: object, limit: int = 80) -> dict:
    return run_async(_process(limit=limit))


@celery_app.task(
    name="revenue_data_recovery.daily_report",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def daily_revenue_data_recovery(self: object, limit: int = 200) -> dict:
    return run_async(_process(limit=limit))


async def _process(*, limit: int) -> dict:
    async with AsyncSessionLocal() as session:
        result = await RevenueDataRecoveryService(session).process_pending(limit=limit)
        qa = await RevenueDataRecoveryService(session).qa_dashboard()
    logger.info("Processed revenue data recovery batch", extra={"extra": {**result, "qa": qa}})
    return {**result, "qa": qa}
