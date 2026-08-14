import time

from fastapi import APIRouter
from sqlalchemy import text

from app.api.dependencies import DatabaseDep, RedisDep, SettingsDep
from app.schemas.health import DependencyStatus, HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: SettingsDep,
    database: DatabaseDep,
    redis: RedisDep,
) -> HealthResponse:
    dependencies: dict[str, DependencyStatus] = {}

    database_started = time.perf_counter()
    await database.execute(text("SELECT 1"))
    dependencies["postgres"] = DependencyStatus(
        status="ok",
        latency_ms=round((time.perf_counter() - database_started) * 1000, 2),
    )

    redis_started = time.perf_counter()
    await redis.ping()
    dependencies["redis"] = DependencyStatus(
        status="ok",
        latency_ms=round((time.perf_counter() - redis_started) * 1000, 2),
    )

    return HealthResponse(
        status="ok",
        environment=settings.environment,
        dependencies=dependencies,
    )
