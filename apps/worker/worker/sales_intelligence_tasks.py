import logging

from app.db.session import AsyncSessionLocal
from app.repositories.sales_intelligence import SalesIntelligenceRepository
from app.services.sales_intelligence import SalesIntelligencePlatformService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="sales_intelligence.refresh_from_replies",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def refresh_from_replies(self: object, limit: int = 40) -> dict:
    return run_async(_refresh_from_replies(limit=limit))


@celery_app.task(
    name="sales_intelligence.refresh_company",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_company(self: object, company_id: str) -> dict:
    return run_async(_refresh_company(company_id))


async def _refresh_from_replies(*, limit: int) -> dict:
    async with AsyncSessionLocal() as session:
        service = SalesIntelligencePlatformService(SalesIntelligenceRepository(session))
        result = await service.process_reply_updates(limit=limit)
        await session.commit()
    logger.info("Sales intelligence refreshed from replies", extra={"extra": result})
    return result


async def _refresh_company(company_id: str) -> dict:
    from uuid import UUID

    async with AsyncSessionLocal() as session:
        service = SalesIntelligencePlatformService(SalesIntelligenceRepository(session))
        pack = await service.refresh(UUID(company_id))
        await session.commit()
    return {"refreshed": bool(pack), "company_id": company_id}
