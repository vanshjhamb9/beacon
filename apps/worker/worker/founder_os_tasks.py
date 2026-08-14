import logging

from app.db.session import AsyncSessionLocal
from app.repositories.founder_os import FounderOsRepository
from app.services.founder_os import FounderOsPlatformService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="founder_os.refresh_brief",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def refresh_founder_brief(self: object) -> dict[str, object]:
    return run_async(_refresh())


async def _refresh() -> dict[str, object]:
    async with AsyncSessionLocal() as session:
        service = FounderOsPlatformService(FounderOsRepository(session))
        pack = await service.refresh()
        await session.commit()
    brief = pack.get("brief") or {}
    result = {
        "brief_id": pack.get("brief_id"),
        "a_plus": brief.get("a_plus_opportunities", 0),
        "tasks": len(pack.get("tasks") or []),
        "expected_revenue": brief.get("expected_revenue", 0),
    }
    logger.info("Refreshed founder OS daily brief", extra={"extra": result})
    return result
