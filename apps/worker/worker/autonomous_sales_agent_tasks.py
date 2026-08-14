import logging

from app.db.session import AsyncSessionLocal
from app.repositories.autonomous_sales_agent import AutonomousSalesAgentRepository
from app.services.autonomous_sales_agent import AutonomousSalesAgentPlatformService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="autonomous_sales_agent.refresh_morning_brief",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_morning_brief(self: object) -> dict:
    return run_async(_refresh_morning_brief())


@celery_app.task(
    name="autonomous_sales_agent.refresh_work_queue",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_work_queue(self: object) -> dict:
    return run_async(_refresh_work_queue())


@celery_app.task(
    name="autonomous_sales_agent.refresh_company",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_company(self: object, company_id: str) -> dict:
    return run_async(_refresh_company(company_id))


async def _refresh_morning_brief() -> dict:
    async with AsyncSessionLocal() as session:
        service = AutonomousSalesAgentPlatformService(AutonomousSalesAgentRepository(session))
        pack = await service.morning_brief(refresh=True)
        await session.commit()
    logger.info(
        "ASA morning brief refreshed",
        extra={"extra": {"priorities": len(pack.get("priorities") or []), "forecast": pack.get("revenue_forecast")}},
    )
    return {
        "priorities": len(pack.get("priorities") or []),
        "revenue_forecast": pack.get("revenue_forecast", 0),
        "follow_ups_due": len(pack.get("follow_ups_due") or []),
    }


async def _refresh_work_queue() -> dict:
    async with AsyncSessionLocal() as session:
        service = AutonomousSalesAgentPlatformService(AutonomousSalesAgentRepository(session))
        pack = await service.work_queue(limit=50, refresh=True)
        await session.commit()
    return {"total": pack.get("total", 0)}


async def _refresh_company(company_id: str) -> dict:
    from uuid import UUID

    async with AsyncSessionLocal() as session:
        service = AutonomousSalesAgentPlatformService(AutonomousSalesAgentRepository(session))
        pack = await service.refresh(UUID(company_id))
        await session.commit()
    return {"refreshed": bool(pack), "company_id": company_id}
