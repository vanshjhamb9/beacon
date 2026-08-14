"""Celery tasks for buyer-first lead discovery pipeline.

Only companies with verified buying events enter the sales pipeline.
Zero is acceptable — no fabrication.
"""

import logging

from app.db.session import AsyncSessionLocal
from app.services.lead_discovery import LeadDiscoveryService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="lead_discovery.get_stats",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def get_pipeline_stats(self: object) -> dict:
    """Get pipeline statistics by department."""
    return run_async(_get_stats())


async def _get_stats() -> dict:
    async with AsyncSessionLocal() as session:
        service = LeadDiscoveryService(session)
        return await service.get_pipeline_stats()
