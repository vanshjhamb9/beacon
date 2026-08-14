import logging

from app.db.session import AsyncSessionLocal
from app.repositories.revenue import RevenueRepository
from app.services.revenue import RevenueService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="revenue.process_opportunities",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_revenue_opportunities(self: object, limit: int = 100) -> dict[str, int]:
    return run_async(_process_revenue_opportunities(limit=limit))


async def _process_revenue_opportunities(*, limit: int) -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        service = RevenueService(RevenueRepository(session))
        await service.ensure_catalog_seeded()
        result = await service.process_pending(limit=limit)
        await session.commit()

    logger.info("Processed revenue opportunity batch", extra={"extra": result})
    return result
