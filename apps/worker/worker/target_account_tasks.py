import logging

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.repositories.target_account import TargetAccountRepository
from app.services.target_account import TargetAccountPlatformService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="targets.process_accounts",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_target_accounts(self: object, limit: int = 40) -> dict[str, int]:
    return run_async(_process_target_accounts(limit=limit))


async def _process_target_accounts(*, limit: int) -> dict[str, int]:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        service = TargetAccountPlatformService(TargetAccountRepository(session), settings)
        result = await service.process_pending(limit=limit)
        await session.commit()
    logger.info("Processed target account intelligence batch", extra={"extra": result})
    return result
