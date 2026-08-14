import logging

from app.db.session import AsyncSessionLocal
from app.repositories.live_revenue import LiveRevenueRepository
from app.services.live_revenue import LiveRevenuePlatformService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="live_revenue.refresh_command_center",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_command_center(self: object) -> dict:
    return run_async(_refresh_command_center())


@celery_app.task(
    name="live_revenue.refresh_company",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_company(self: object, company_id: str) -> dict:
    return run_async(_refresh_company(company_id))


async def _refresh_command_center() -> dict:
    async with AsyncSessionLocal() as session:
        service = LiveRevenuePlatformService(LiveRevenueRepository(session))
        pack = await service.command_center()
        await session.commit()
    logger.info("LRE command center refreshed", extra={"extra": {"awaiting": pack.get("awaiting_approval")}})
    return {"awaiting_approval": pack.get("awaiting_approval", 0), "total_runs": pack.get("total_runs", 0)}


async def _refresh_company(company_id: str) -> dict:
    from uuid import UUID

    async with AsyncSessionLocal() as session:
        service = LiveRevenuePlatformService(LiveRevenueRepository(session))
        pack = await service.refresh(UUID(company_id))
        await session.commit()
    return {"refreshed": bool(pack), "company_id": company_id}
