import logging

from app.db.session import AsyncSessionLocal
from app.repositories.production_validation import ProductionValidationRepository
from app.services.production_validation import ProductionValidationPlatformService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="production_validation.refresh_report",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_report(self: object) -> dict:
    return run_async(_refresh_report())


async def _refresh_report() -> dict:
    async with AsyncSessionLocal() as session:
        service = ProductionValidationPlatformService(ProductionValidationRepository(session))
        pack = await service.refresh()
        await session.commit()
    logger.info(
        "Production validation refreshed",
        extra={"extra": {"score": pack.get("overall_score"), "status": pack.get("overall_status")}},
    )
    return {
        "overall_score": pack.get("overall_score"),
        "overall_status": pack.get("overall_status"),
        "alerts": len(pack.get("alerts") or []),
    }
