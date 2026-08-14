import logging

from app.db.session import AsyncSessionLocal
from app.repositories.enrichment import EnrichmentRepository
from app.repositories.verification import VerificationRepository
from app.services.enrichment import LeadEnrichmentService
from app.services.verification import DataVerificationService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="verification.process_enrichments",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_verification_enrichments(self: object, limit: int = 50) -> dict[str, int]:
    return run_async(_process_verification_enrichments(limit=limit))


async def _process_verification_enrichments(*, limit: int) -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        enrichment_service = LeadEnrichmentService(EnrichmentRepository(session))
        service = DataVerificationService(
            VerificationRepository(session),
            enrichment_service=enrichment_service,
        )
        result = await service.process_pending(limit=limit)
        await session.commit()

    logger.info("Processed data verification batch", extra={"extra": result})
    return result
