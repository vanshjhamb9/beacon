import logging

from app.db.session import AsyncSessionLocal
from app.repositories.context import ContextRepository
from app.services.context import ContextService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="context.process_signals",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_context_signals(self: object, limit: int = 100) -> dict[str, int]:
    return run_async(_process_context_signals(limit=limit))


async def _process_context_signals(*, limit: int) -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        service = ContextService(ContextRepository(session))
        result = await service.process_pending(limit=limit)
        await session.commit()

    logger.info("Processed context signal batch", extra={"extra": result})
    return result
