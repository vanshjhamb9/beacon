import logging

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.repositories.revenue_hunter import RevenueHunterRepository
from app.services.revenue_hunter import RevenueHunterPlatformService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="revenue_hunter.process_accounts",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_revenue_hunter(self: object, limit: int = 40) -> dict[str, int]:
    return run_async(_process_revenue_hunter(limit=limit))


async def _process_revenue_hunter(*, limit: int) -> dict[str, int]:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        service = RevenueHunterPlatformService(RevenueHunterRepository(session), settings)
        result = await service.process_pending(limit=limit)
        await session.commit()
    logger.info("Processed revenue hunter batch", extra={"extra": result})
    return result
