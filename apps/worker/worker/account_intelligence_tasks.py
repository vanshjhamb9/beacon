import logging

from app.db.session import AsyncSessionLocal
from app.repositories.account_intelligence import AccountIntelligenceRepository
from app.services.account_intelligence import AccountIntelligencePlatformService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="account.refresh_profiles", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_profiles(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="account.refresh_contacts", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_contacts(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="account.refresh_technology", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_technology(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="account.refresh_websites", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_websites(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="account.refresh_ai_scores", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_ai_scores(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="account.refresh_sales_scores", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_sales_scores(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="account.refresh_relationship_graph", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_relationship_graph(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="account.daily_validation", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def daily_validation(self: object) -> dict:
    return run_async(_refresh())


async def _refresh() -> dict:
    async with AsyncSessionLocal() as session:
        service = AccountIntelligencePlatformService(AccountIntelligenceRepository(session))
        result = await service.refresh_batch(limit=30)
        await session.commit()
    logger.info("AIP refresh complete", extra={"extra": result})
    return result
