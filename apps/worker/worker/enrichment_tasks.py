import logging

from app.db.session import AsyncSessionLocal
from app.repositories.enrichment import EnrichmentRepository
from app.services.enrichment import LeadEnrichmentService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="enrichment.process_opportunities",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_enrichment_opportunities(self: object, limit: int = 50) -> dict[str, int]:
    return run_async(_process_enrichment_opportunities(limit=limit))


async def _process_enrichment_opportunities(*, limit: int) -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        service = LeadEnrichmentService(EnrichmentRepository(session))
        result = await service.process_pending(limit=limit)
        await session.commit()

    logger.info("Processed lead enrichment batch", extra={"extra": result})
    return result
