from worker.async_runtime import run_async
from worker.celery_app import celery_app


@celery_app.task(name="company_intelligence.process_verified", bind=True, autoretry_for=(Exception,), max_retries=2)
def process_verified(self, limit: int = 40) -> dict:
    return run_async(_process(limit=limit))


@celery_app.task(name="company_intelligence.rebuild", bind=True, autoretry_for=(Exception,), max_retries=2)
def rebuild_intelligence(self, limit: int = 500, fetch_website: bool = False) -> dict:
    return run_async(_rebuild(limit=limit, fetch_website=fetch_website))


async def _process(*, limit: int) -> dict:
    from app.db.session import AsyncSessionLocal
    from app.services.company_intelligence import CompanyIntelligenceService

    async with AsyncSessionLocal() as session:
        return await CompanyIntelligenceService(session).process_verified(limit=limit)


async def _rebuild(*, limit: int, fetch_website: bool) -> dict:
    from app.db.session import AsyncSessionLocal
    from app.services.company_intelligence import CompanyIntelligenceService

    async with AsyncSessionLocal() as session:
        return await CompanyIntelligenceService(session).rebuild(limit=limit, fetch_website=fetch_website)
