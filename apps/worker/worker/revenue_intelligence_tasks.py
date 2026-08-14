import logging

from app.db.session import AsyncSessionLocal
from app.repositories.ecommerce_leads import EcommerceLeadRepository
from app.repositories.revenue_intelligence import RevenueIntelligenceRepository
from app.services.revenue_intelligence import RevenueIntelligenceService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="revenue_intelligence.analyze_leads",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def analyze_revenue_intelligence(self: object, limit: int = 500, country: str = "India") -> dict[str, int]:
    return run_async(_analyze_revenue_intelligence(limit=limit, country=country))


async def _analyze_revenue_intelligence(*, limit: int, country: str) -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        service = RevenueIntelligenceService(
            RevenueIntelligenceRepository(session),
            EcommerceLeadRepository(session),
        )
        result = await service.analyze_leads(limit=limit, country=country)
        await session.commit()

    logger.info("Revenue intelligence analysis completed", extra={"extra": result})
    return result
