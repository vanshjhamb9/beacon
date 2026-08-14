import logging

from app.db.session import AsyncSessionLocal
from app.repositories.global_opportunity_acquisition import GlobalOpportunityAcquisitionRepository
from app.services.global_opportunity_acquisition import GlobalOpportunityAcquisitionPlatformService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def _svc():
    return GlobalOpportunityAcquisitionPlatformService


@celery_app.task(name="collector.refresh_sources", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_sources(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="collector.score_sources", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def score_sources(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="collector.build_graph", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def build_graph(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="collector.update_benchmarks", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def update_benchmarks(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="collector.detect_new_intent", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def detect_new_intent(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="collector.refresh_websites", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_websites(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="collector.refresh_jobs", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_jobs(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="collector.refresh_reviews", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_reviews(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="collector.refresh_funding", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_funding(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="collector.daily_report", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def daily_report(self: object) -> dict:
    return run_async(_daily())


async def _refresh() -> dict:
    async with AsyncSessionLocal() as session:
        service = GlobalOpportunityAcquisitionPlatformService(GlobalOpportunityAcquisitionRepository(session))
        result = await service.refresh(limit=40)
        await session.commit()
    logger.info("GOAP refresh complete", extra={"extra": {"companies": len(result.get("companies", []))}})
    return {"companies": len(result.get("companies", [])), "scoring_version": result.get("scoring_version")}


async def _daily() -> dict:
    async with AsyncSessionLocal() as session:
        service = GlobalOpportunityAcquisitionPlatformService(GlobalOpportunityAcquisitionRepository(session))
        await service.refresh(limit=40)
        report = await service.daily_report()
        await session.commit()
    return {"summary": report.get("summary"), "alerts": len(report.get("alerts", []))}
