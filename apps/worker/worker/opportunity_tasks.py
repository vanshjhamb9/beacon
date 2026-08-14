import logging

from app.db.session import AsyncSessionLocal
from app.repositories.opportunity import OpportunityRepository
from app.services.opportunity import OpportunityService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="opportunity.process_companies",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_opportunity_companies(self: object, limit: int = 100) -> dict[str, int]:
    return run_async(_process_opportunity_companies(limit=limit))


async def _process_opportunity_companies(*, limit: int) -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        service = OpportunityService(OpportunityRepository(session))
        result = await service.process_pending(limit=limit)
        await session.commit()

    logger.info("Processed opportunity company batch", extra={"extra": result})
    return result
