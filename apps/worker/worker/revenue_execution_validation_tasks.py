from worker.async_runtime import run_async
from worker.celery_app import celery_app


@celery_app.task(name="revenue_execution_validation.rebuild", bind=True, autoretry_for=(Exception,), max_retries=2)
def rebuild_revenue_execution(self, limit: int = 500) -> dict:
    return run_async(_rebuild(limit=limit))


@celery_app.task(name="revenue_execution_validation.daily_report", bind=True, autoretry_for=(Exception,), max_retries=2)
def daily_revenue_execution_report(self) -> dict:
    return run_async(_daily())


async def _rebuild(*, limit: int) -> dict:
    from app.db.session import AsyncSessionLocal
    from app.services.revenue_execution_validation import RevenueExecutionValidationService

    async with AsyncSessionLocal() as session:
        return await RevenueExecutionValidationService(session).rebuild(persist=True, limit=limit)


async def _daily() -> dict:
    from app.db.session import AsyncSessionLocal
    from app.services.revenue_execution_validation import RevenueExecutionValidationService

    async with AsyncSessionLocal() as session:
        return await RevenueExecutionValidationService(session).daily_report()
