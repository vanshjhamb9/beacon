from worker.async_runtime import run_async
from worker.celery_app import celery_app


@celery_app.task(name="revenue_data_acquisition.process_pending", bind=True, autoretry_for=(Exception,), max_retries=2)
def process_pending(self, limit: int = 200) -> dict:
    return run_async(_expand(limit=limit, fetch_github=True, recover_contacts=False, recover_dms=False))


@celery_app.task(name="revenue_data_acquisition.recover_contacts", bind=True, autoretry_for=(Exception,), max_retries=2)
def recover_contacts(self, limit: int = 80) -> dict:
    return run_async(_contacts(limit=limit))


@celery_app.task(
    name="revenue_data_acquisition.recover_decision_makers", bind=True, autoretry_for=(Exception,), max_retries=2
)
def recover_decision_makers(self, limit: int = 80) -> dict:
    return run_async(_dms(limit=limit))


@celery_app.task(name="revenue_data_acquisition.daily_report", bind=True, autoretry_for=(Exception,), max_retries=2)
def daily_report(self, limit: int = 800) -> dict:
    return run_async(_expand(limit=limit, fetch_github=True, recover_contacts=True, recover_dms=True))


async def _expand(*, limit: int, fetch_github: bool, recover_contacts: bool, recover_dms: bool) -> dict:
    from app.db.session import AsyncSessionLocal
    from app.services.revenue_data_acquisition import RevenueDataAcquisitionService

    async with AsyncSessionLocal() as session:
        return await RevenueDataAcquisitionService(session).expand(
            limit=limit,
            fetch_github=fetch_github,
            recover_contacts=recover_contacts,
            recover_dms=recover_dms,
            crawl_companies=True,
        )


async def _contacts(*, limit: int) -> dict:
    from app.db.session import AsyncSessionLocal
    from app.services.revenue_data_acquisition import RevenueDataAcquisitionService

    async with AsyncSessionLocal() as session:
        return await RevenueDataAcquisitionService(session).recover_contacts(limit=limit)


async def _dms(*, limit: int) -> dict:
    from app.db.session import AsyncSessionLocal
    from app.services.revenue_data_acquisition import RevenueDataAcquisitionService

    async with AsyncSessionLocal() as session:
        return await RevenueDataAcquisitionService(session).recover_decision_makers(limit=limit)
