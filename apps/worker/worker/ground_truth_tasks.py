import logging

from app.db.session import AsyncSessionLocal
from app.services.ground_truth import GroundTruthService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="ground_truth.process_pending",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_ground_truth(self: object, limit: int = 80) -> dict:
    return run_async(_process(limit=limit))


@celery_app.task(
    name="ground_truth.daily_report",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def daily_ground_truth_report(self: object) -> dict:
    return run_async(_daily())


async def _process(*, limit: int) -> dict:
    async with AsyncSessionLocal() as session:
        result = await GroundTruthService(session).process_pending(limit=limit)
    logger.info("Processed ground truth batch", extra={"extra": result})
    return result


async def _daily() -> dict:
    async with AsyncSessionLocal() as session:
        service = GroundTruthService(session)
        report = await service.daily_report()
        acceptance = await service.acceptance()
    return {"report": report, "acceptance": acceptance, "scoring_version": "alpha-plus-v1"}
