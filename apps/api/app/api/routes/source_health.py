from fastapi import APIRouter
from sqlalchemy import select

from app.api.dependencies import DatabaseDep
from app.models.source_health import SourceHealth
from app.schemas.source_health import SourceHealthItem, SourceHealthResponse

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/health", response_model=SourceHealthResponse)
async def source_health(database: DatabaseDep) -> SourceHealthResponse:
    result = await database.execute(select(SourceHealth).order_by(SourceHealth.source))
    sources = [
        SourceHealthItem(
            source=item.source,
            status=item.status.value,
            last_success_at=item.last_success_at,
            last_failure_at=item.last_failure_at,
            last_checked_at=item.last_checked_at,
            last_error=item.last_error,
            consecutive_failures=item.consecutive_failures,
            average_latency_ms=item.average_latency_ms,
        )
        for item in result.scalars().all()
    ]
    return SourceHealthResponse(sources=sources)
