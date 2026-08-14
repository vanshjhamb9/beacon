from worker.async_runtime import run_async
from worker.celery_app import celery_app


@celery_app.task(name="identity_coverage.process_pending", bind=True, autoretry_for=(Exception,), max_retries=2)
def process_pending(self, limit: int = 200) -> dict:
    return run_async(_expand(limit=limit, fetch_github=True, crawl_website=False))


@celery_app.task(name="identity_coverage.retry_missing", bind=True, autoretry_for=(Exception,), max_retries=2)
def retry_missing(self, limit: int = 40) -> dict:
    return run_async(_retry(limit=limit))


@celery_app.task(name="identity_coverage.collector_metrics", bind=True, autoretry_for=(Exception,), max_retries=2)
def collector_metrics(self, limit: int = 500) -> dict:
    return run_async(_expand(limit=limit, fetch_github=False, crawl_website=False))


@celery_app.task(name="identity_coverage.daily_report", bind=True, autoretry_for=(Exception,), max_retries=2)
def daily_report(self, limit: int = 800) -> dict:
    return run_async(_expand(limit=limit, fetch_github=True, crawl_website=True))


async def _expand(*, limit: int, fetch_github: bool, crawl_website: bool) -> dict:
    from app.db.session import AsyncSessionLocal
    from app.services.identity_coverage import IdentityCoverageService

    async with AsyncSessionLocal() as session:
        return await IdentityCoverageService(session).expand(
            limit=limit, fetch_github=fetch_github, crawl_website=crawl_website
        )


async def _retry(*, limit: int) -> dict:
    from app.db.session import AsyncSessionLocal
    from app.services.identity_coverage import IdentityCoverageService

    async with AsyncSessionLocal() as session:
        return await IdentityCoverageService(session).retry_missing(limit=limit)
