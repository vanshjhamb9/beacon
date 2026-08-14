from worker.async_runtime import run_async
from worker.celery_app import celery_app


@celery_app.task(name="entity_resolution.rebuild", bind=True, autoretry_for=(Exception,), max_retries=2)
def rebuild_entities(self, limit: int = 1000, fetch_official: bool = False) -> dict:
    return run_async(_rebuild(limit=limit, fetch_official=fetch_official))


async def _rebuild(*, limit: int, fetch_official: bool) -> dict:
    from app.db.session import AsyncSessionLocal
    from app.services.entity_resolution_erowd import EntityResolutionService

    async with AsyncSessionLocal() as session:
        return await EntityResolutionService(session).rebuild(limit=limit, fetch_official=fetch_official)
