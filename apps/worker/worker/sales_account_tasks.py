import logging

from app.db.session import AsyncSessionLocal
from app.repositories.ecommerce_leads import EcommerceLeadRepository
from app.repositories.sales_account import SalesAccountRepository
from app.services.sales_account import SalesAccountService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="sales_intelligence.refresh_accounts",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def refresh_sales_accounts(self: object, limit: int = 500) -> dict[str, int]:
    return run_async(_refresh_sales_accounts(limit=limit))


async def _refresh_sales_accounts(*, limit: int) -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        service = SalesAccountService(
            SalesAccountRepository(session),
            EcommerceLeadRepository(session),
        )
        result = await service.bulk_refresh(limit=limit)
        await session.commit()

    logger.info("Sales account refresh completed", extra={"extra": result})
    return result
