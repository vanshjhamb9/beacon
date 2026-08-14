from __future__ import annotations

from worker.async_runtime import run_async
from worker.celery_app import celery_app


@celery_app.task(name="company_resolution.rebuild", bind=True, autoretry_for=(Exception,), max_retries=2)
def rebuild_companies(self, limit: int = 1000, soft_delete_companies: bool = True) -> dict:
    return run_async(_rebuild(limit=limit, soft_delete_companies=soft_delete_companies))


async def _rebuild(*, limit: int, soft_delete_companies: bool) -> dict:
    from app.db.session import AsyncSessionLocal
    from app.services.company_resolution import CompanyResolutionService

    async with AsyncSessionLocal() as session:
        service = CompanyResolutionService(session)
        return await service.rebuild_from_raw_events(limit=limit, soft_delete_companies=soft_delete_companies)
