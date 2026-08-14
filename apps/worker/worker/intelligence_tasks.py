import logging
from datetime import UTC, datetime

from sqlalchemy import exists, or_, select

from app.db.session import AsyncSessionLocal
from app.models.quality import QualityReport
from app.models.raw_event import RawEvent, RawEventStatus
from app.repositories.intelligence import IntelligenceRepository
from app.services.intelligence import IntelligenceService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)

MAX_UNRESOLVED_ATTEMPTS = 3


@celery_app.task(
    name="intelligence.process_raw_events",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_raw_events(self: object, limit: int = 100) -> dict[str, int]:
    return run_async(_process_raw_events(limit=limit))


async def _process_raw_events(*, limit: int) -> dict[str, int]:
    processed = 0
    unresolved = 0
    exhausted = 0

    async with AsyncSessionLocal() as session:
        accepted_quality_report = exists().where(
            QualityReport.raw_event_id == RawEvent.id,
            or_(QualityReport.decision == "accept", QualityReport.decision == "review"),
        )
        result = await session.execute(
            select(RawEvent)
            .where(RawEvent.status == RawEventStatus.RECEIVED, accepted_quality_report)
            .order_by(RawEvent.published_at)
            .limit(limit)
        )
        raw_events = result.scalars().all()
        service = IntelligenceService(IntelligenceRepository(session))

        for raw_event in raw_events:
            try:
                outcome = await service.process_raw_event(raw_event)
            except Exception:
                logger.exception(
                    "Intelligence processing failed for raw event",
                    extra={
                        "extra": {
                            "raw_event_id": str(raw_event.id),
                            "source": raw_event.source,
                        }
                    },
                )
                raise

            if outcome["status"] in {"cre_rejected", "erowd_rejected"}:
                metadata = dict(raw_event.event_metadata or {})
                metadata[outcome["status"]] = True
                metadata["identity_reject_reason"] = outcome.get("reason")
                metadata["identity_score"] = outcome.get("identity_score")
                metadata["identity_rejected_at"] = datetime.now(UTC).isoformat()
                raw_event.event_metadata = metadata
                raw_event.status = RawEventStatus.PROCESSED
                processed += 1
                continue

            if outcome["status"] == "unresolved":
                metadata = dict(raw_event.event_metadata or {})
                attempts = int(metadata.get("intelligence_attempts") or 0) + 1
                metadata["intelligence_attempts"] = attempts
                metadata["last_unresolved_at"] = datetime.now(UTC).isoformat()
                metadata["unresolved_reason"] = "company_entity_not_found"
                raw_event.event_metadata = metadata
                unresolved += 1

                if attempts >= MAX_UNRESOLVED_ATTEMPTS:
                    raw_event.status = RawEventStatus.PROCESSED
                    exhausted += 1
                    logger.warning(
                        "Raw event unresolved after max attempts — marking processed",
                        extra={
                            "extra": {
                                "raw_event_id": str(raw_event.id),
                                "source": raw_event.source,
                                "attempts": attempts,
                                "title": raw_event.title[:160],
                            }
                        },
                    )
                else:
                    logger.warning(
                        "Raw event unresolved — company entity not found",
                        extra={
                            "extra": {
                                "raw_event_id": str(raw_event.id),
                                "source": raw_event.source,
                                "attempts": attempts,
                                "title": raw_event.title[:160],
                            }
                        },
                    )
                continue

            raw_event.status = RawEventStatus.PROCESSED
            processed += 1

        await session.commit()

    logger.info(
        "Processed raw events into intelligence layer",
        extra={
            "extra": {
                "processed": processed,
                "unresolved": unresolved,
                "exhausted": exhausted,
            }
        },
    )
    return {"processed": processed, "unresolved": unresolved, "exhausted": exhausted}
