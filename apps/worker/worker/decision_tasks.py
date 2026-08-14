import logging

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.repositories.decision import DecisionDiscoveryRepository
from app.services.decision import DecisionMakerDiscoveryService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="decision.process_companies",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_decision_companies(self: object, limit: int = 50) -> dict[str, int]:
    return run_async(_process_decision_companies(limit=limit))


async def _process_decision_companies(*, limit: int) -> dict[str, int]:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        service = DecisionMakerDiscoveryService(
            DecisionDiscoveryRepository(session),
            settings=settings,
        )
        result = await service.process_pending(limit=limit)
        await session.commit()

    logger.info("Processed decision discovery batch", extra={"extra": result})
    return result
