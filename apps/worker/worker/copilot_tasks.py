import logging

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.repositories.copilot import SalesCopilotRepository
from app.services.copilot import AISalesCopilotService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="copilot.process_packages",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_copilot_packages(self: object, limit: int = 25) -> dict[str, int]:
    return run_async(_process_copilot_packages(limit=limit))


async def _process_copilot_packages(*, limit: int) -> dict[str, int]:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        service = AISalesCopilotService(
            SalesCopilotRepository(session),
            settings=settings,
        )
        result = await service.process_pending(limit=limit)
        await session.commit()

    logger.info("Processed sales copilot batch", extra={"extra": result})
    return result
