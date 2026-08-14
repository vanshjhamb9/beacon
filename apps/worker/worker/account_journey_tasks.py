import logging

from app.db.session import AsyncSessionLocal
from app.repositories.account_journey import AccountJourneyRepository
from app.services.account_journey import AccountJourneyPlatformService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="journey.refresh_accounts",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_accounts(self: object) -> dict:
    return run_async(_refresh_accounts())


@celery_app.task(
    name="journey.calculate_engagement",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def calculate_engagement(self: object) -> dict:
    return run_async(_calculate_engagement())


@celery_app.task(
    name="journey.plan_followups",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def plan_followups(self: object) -> dict:
    return run_async(_plan_followups())


@celery_app.task(
    name="journey.analytics_daily",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def analytics_daily(self: object) -> dict:
    return run_async(_analytics_daily())


async def _refresh_accounts() -> dict:
    async with AsyncSessionLocal() as session:
        service = AccountJourneyPlatformService(AccountJourneyRepository(session))
        result = await service.refresh_batch(limit=40)
        await session.commit()
    logger.info("GOI accounts refreshed", extra={"extra": result})
    return result


async def _calculate_engagement() -> dict:
    async with AsyncSessionLocal() as session:
        service = AccountJourneyPlatformService(AccountJourneyRepository(session))
        result = await service.refresh_batch(limit=25)
        dash = await service.dashboard()
        await session.commit()
    return {"refreshed": result.get("refreshed", 0), "total_journeys": dash.get("total_journeys", 0)}


async def _plan_followups() -> dict:
    async with AsyncSessionLocal() as session:
        service = AccountJourneyPlatformService(AccountJourneyRepository(session))
        await service.refresh_batch(limit=25)
        plans = await service.followups(limit=50)
        await session.commit()
    return {"plans": plans.get("total", 0)}


async def _analytics_daily() -> dict:
    async with AsyncSessionLocal() as session:
        service = AccountJourneyPlatformService(AccountJourneyRepository(session))
        await service.refresh_batch(limit=40)
        analytics = await service.analytics()
        await session.commit()
    return {"has_payload": bool(analytics.get("payload")), "scoring_version": analytics.get("scoring_version")}
