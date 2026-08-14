from worker.async_runtime import run_async
from worker.celery_app import celery_app


@celery_app.task(name="operations.monitor_connectors", bind=True, autoretry_for=(Exception,), max_retries=2)
def monitor_connectors(self) -> dict:
    return run_async(_health())


@celery_app.task(name="operations.recover_websites", bind=True, autoretry_for=(Exception,), max_retries=2)
def recover_websites(self) -> dict:
    return run_async(_unlock(collect_new=True, recover_contacts=False, recover_dms=False))


@celery_app.task(name="operations.recover_contacts", bind=True, autoretry_for=(Exception,), max_retries=2)
def recover_contacts(self) -> dict:
    return run_async(_unlock(collect_new=False, recover_contacts=True, recover_dms=True))


@celery_app.task(name="operations.daily_audit", bind=True, autoretry_for=(Exception,), max_retries=2)
def daily_audit(self) -> dict:
    return run_async(_unlock(collect_new=True, recover_contacts=True, recover_dms=True))


async def _health() -> dict:
    from app.db.session import AsyncSessionLocal
    from app.services.dataset_unlock import DatasetUnlockService

    async with AsyncSessionLocal() as session:
        return await DatasetUnlockService(session).health()


async def _unlock(*, collect_new: bool, recover_contacts: bool, recover_dms: bool) -> dict:
    from app.db.session import AsyncSessionLocal
    from app.services.dataset_unlock import DatasetUnlockService

    async with AsyncSessionLocal() as session:
        return await DatasetUnlockService(session).unlock(
            collect_new=collect_new,
            recover_contacts=recover_contacts,
            recover_dms=recover_dms,
        )
