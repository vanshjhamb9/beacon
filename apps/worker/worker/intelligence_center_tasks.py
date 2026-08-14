"""Beacon Intelligence Center background sync (BIC v1)."""

from __future__ import annotations

import logging
from typing import Any

from app.db.session import AsyncSessionLocal
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="intelligence_center.sync")
def sync_intelligence_center() -> dict[str, Any]:
    return run_async(_sync())


async def _sync() -> dict[str, Any]:
    from app.services.intelligence_center import IntelligenceCenterService

    async with AsyncSessionLocal() as session:
        service = IntelligenceCenterService(session)
        result = await service.sync_all()
        await session.commit()
    logger.info("BIC sync complete", extra={"extra": result})
    return result
