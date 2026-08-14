import logging

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.repositories.acquisition import AcquisitionRepository
from app.services.acquisition import AcquisitionService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="acquisition.monitor_connectors",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def monitor_connectors(self: object) -> dict[str, int]:
    return run_async(_monitor_connectors())


@celery_app.task(
    name="acquisition.generate_daily_report",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def generate_daily_report(self: object) -> dict[str, object]:
    return run_async(_generate_daily_report())


async def _monitor_connectors() -> dict[str, int]:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        service = AcquisitionService(AcquisitionRepository(session, settings), settings=settings)
        result = await service.monitor_and_alert()
        await session.commit()
    logger.info("Acquisition connector monitor complete", extra={"extra": result})
    return result


async def _generate_daily_report() -> dict[str, object]:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        service = AcquisitionService(AcquisitionRepository(session, settings), settings=settings)
        report = await service.generate_daily_report()
        await session.commit()
    payload = {
        "report_date": report.report_date,
        "new_companies": report.new_companies,
        "new_opportunities": report.new_opportunities,
        "high_value_opportunities": report.high_value_opportunities,
        "summary": report.summary,
    }
    logger.info("Acquisition daily report generated", extra={"extra": payload})
    return payload
