import logging

from app.db.session import AsyncSessionLocal
from app.repositories.improvement import ImprovementRepository
from app.services.improvement import ImprovementService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="improvement.evaluate",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def evaluate_improvement(self: object, limit: int = 1000) -> dict[str, int]:
    return run_async(_evaluate_improvement(limit=limit))


async def _evaluate_improvement(*, limit: int) -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        service = ImprovementService(ImprovementRepository(session))
        result = await service.run_evaluation(limit=limit)
        await session.commit()

    logger.info("Evaluated intelligence improvement signals", extra={"extra": result})
    return result
