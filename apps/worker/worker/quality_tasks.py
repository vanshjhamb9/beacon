import logging

from sqlalchemy import exists, select

from app.db.session import AsyncSessionLocal
from app.models.quality import QualityReport
from app.models.raw_event import RawEvent, RawEventStatus
from app.repositories.quality import QualityRepository
from app.services.quality import QualityService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="quality.process_raw_events",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_quality_events(self: object, limit: int = 250) -> dict[str, int]:
    return run_async(_process_quality_events(limit=limit))


async def _process_quality_events(*, limit: int) -> dict[str, int]:
    processed = 0
    accepted = 0
    rejected = 0

    async with AsyncSessionLocal() as session:
        already_reported = exists().where(QualityReport.raw_event_id == RawEvent.id)
        result = await session.execute(
            select(RawEvent)
            .where(RawEvent.status == RawEventStatus.RECEIVED, ~already_reported)
            .order_by(RawEvent.created_at)
            .limit(limit)
        )
        service = QualityService(QualityRepository(session))
        await service.ensure_rules_seeded()

        for raw_event in result.scalars().all():
            report = await service.process_raw_event(raw_event)
            processed += 1
            accepted += int(report.decision == "accept")
            rejected += int(report.decision == "reject")

        await session.commit()

    logger.info(
        "Quality processed raw event batch",
        extra={"extra": {"processed": processed, "accepted": accepted, "rejected": rejected}},
    )
    return {"processed": processed, "accepted": accepted, "rejected": rejected}
