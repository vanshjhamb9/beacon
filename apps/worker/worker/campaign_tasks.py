import logging

from app.db.session import AsyncSessionLocal
from app.repositories.campaign import CampaignRepository
from app.services.campaign import CampaignService
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="campaigns.process_pending",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_pending_campaigns(self: object, limit: int = 25) -> dict[str, int]:
    return run_async(_process_pending_campaigns(limit=limit))


async def _process_pending_campaigns(*, limit: int) -> dict[str, int]:
    """Create campaign plans for top-tier target accounts with approved sales packages."""
    from sqlalchemy import select

    from app.core.config import get_settings
    from app.models.campaign import Campaign
    from app.models.copilot import SalesPackage
    from app.repositories.target_account import TargetAccountRepository

    created = 0
    skipped = 0
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        service = CampaignService(CampaignRepository(session))
        from uuid import UUID

        top_tier: set[UUID] | None = None
        if settings.target_account_gate_enabled:
            top_tier = await TargetAccountRepository(session).top_tier_company_ids()
        result = await session.execute(
            select(SalesPackage.company_id)
            .where(SalesPackage.review_status == "approved")
            .order_by(SalesPackage.created_at.desc())
            .limit(limit * 4)
        )
        company_ids = list(dict.fromkeys(result.scalars().all()))
        for company_id in company_ids:
            if top_tier is not None and company_id not in top_tier:
                skipped += 1
                continue
            existing = await session.scalar(
                select(Campaign.id)
                .where(Campaign.company_id == company_id, Campaign.status.notin_(["cancelled", "completed"]))
                .limit(1)
            )
            if existing is not None:
                continue
            outcome = await service.create_for_company(company_id)
            if outcome.get("created"):
                created += 1
            if created >= limit:
                break
        await session.commit()
    logger.info(
        "Processed campaign intelligence batch",
        extra={"extra": {"created": created, "skipped_non_top_tier": skipped}},
    )
    return {"created": created, "skipped_non_top_tier": skipped}
