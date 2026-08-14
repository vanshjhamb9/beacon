import logging

from app.db.session import AsyncSessionLocal
from app.services.sales_readiness import SalesReadinessService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="sales_readiness.process_pending",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_sales_readiness(self: object, limit: int = 40) -> dict:
    return run_async(_process(limit=limit))


async def _process(*, limit: int) -> dict:
    async with AsyncSessionLocal() as session:
        result = await SalesReadinessService(session).process_pending(limit=limit)
    logger.info("Processed sales readiness batch", extra={"extra": result})
    return result
