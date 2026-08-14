import logging

from app.db.session import AsyncSessionLocal
from app.services.beacon_alpha import BeaconAlphaService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="beacon_alpha.process_pending",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_beacon_alpha(self: object, limit: int = 80) -> dict:
    return run_async(_process(limit=limit))


async def _process(*, limit: int) -> dict:
    async with AsyncSessionLocal() as session:
        service = BeaconAlphaService(session)
        result = await service.process_pending(limit=limit)
        acceptance = await service.acceptance()
    logger.info("Processed beacon alpha batch", extra={"extra": {**result, "acceptance": acceptance}})
    return {**result, "acceptance": acceptance}
