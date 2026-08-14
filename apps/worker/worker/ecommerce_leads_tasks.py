import logging

from app.db.session import AsyncSessionLocal
from app.repositories.ecommerce_leads import EcommerceLeadRepository
from app.services.ecommerce_leads import EcommerceLeadsService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="ecommerce.discovery_worker",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def run_ecommerce_discovery(
    self: object, limit: int = 500, country: str = "India"
) -> dict[str, int]:
    return run_async(_run_ecommerce_discovery(limit=limit, country=country))


async def _run_ecommerce_discovery(
    *, limit: int, country: str
) -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        service = EcommerceLeadsService(
            EcommerceLeadRepository(session),
        )
        result = await service.discover_leads(limit=limit, country=country)
        await session.commit()

    logger.info(
        "Ecommerce discovery completed",
        extra={"extra": result},
    )
    return result
