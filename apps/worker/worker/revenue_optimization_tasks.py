import logging

from app.db.session import AsyncSessionLocal
from app.repositories.revenue_optimization import RevenueOptimizationRepository
from app.services.revenue_optimization import RevenueOptimizationPlatformService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="optimization.collect_metrics", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def collect_metrics(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="optimization.calculate_scores", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def calculate_scores(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="optimization.generate_benchmarks", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def generate_benchmarks(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="optimization.generate_recommendations", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def generate_recommendations(self: object) -> dict:
    return run_async(_refresh())


@celery_app.task(name="optimization.daily_report", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def daily_report(self: object) -> dict:
    return run_async(_report("daily"))


@celery_app.task(name="optimization.weekly_report", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def weekly_report(self: object) -> dict:
    return run_async(_report("weekly"))


async def _refresh() -> dict:
    async with AsyncSessionLocal() as session:
        service = RevenueOptimizationPlatformService(RevenueOptimizationRepository(session))
        result = await service.refresh(limit=100)
        await session.commit()
    logger.info("ROIP refresh complete")
    return {"scoring_version": result.get("scoring_version"), "recommendations": len(result.get("recommendations", []))}


async def _report(kind: str) -> dict:
    async with AsyncSessionLocal() as session:
        service = RevenueOptimizationPlatformService(RevenueOptimizationRepository(session))
        dash = await service.dashboard()
        await session.commit()
    return {"kind": kind, "learning_summary": dash.get("learning_summary"), "scoring_version": dash.get("scoring_version")}
