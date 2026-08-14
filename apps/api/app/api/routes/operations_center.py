from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseDep, SettingsDep
from app.services.operations_center import OperationsCenterService


def _celery_inspect_payload() -> dict:
    """Fast worker probe for Operations hot paths.

    Never call Celery ``inspect`` here — on Windows solo pools a busy worker
    blocks control replies for many seconds and freezes ``/operations/live``,
    which makes the dashboard look empty. Redis evidence is enough for UI health.
    """
    return _celery_activity_fallback()


def _celery_activity_fallback() -> dict:
    """Treat recent Redis task activity / beat heartbeat as workers online."""
    try:
        import redis as redis_sync

        from app.core.config import get_settings

        settings = get_settings()
        client = redis_sync.Redis.from_url(
            settings.redis_dsn,
            decode_responses=True,
            socket_connect_timeout=1.0,
            socket_timeout=1.5,
        )
        try:
            beat = client.get("beacon:celery:beat:heartbeat")
            fresh = bool(client.llen("celery") or client.llen("unacked"))
            if not fresh:
                cursor = 0
                scanned = 0
                while scanned < 30:
                    cursor, keys = client.scan(cursor=cursor, match="celery-task-meta-*", count=20)
                    scanned += len(keys)
                    for key in keys[:10]:
                        raw = client.get(key)
                        if raw and (
                            "date_done" in raw
                            or '"status": "SUCCESS"' in raw
                            or '"status":"SUCCESS"' in raw
                        ):
                            fresh = True
                            break
                    if fresh or cursor == 0:
                        break
            if not (beat or fresh):
                return {}
            return {
                "ping": {"celery@beacon-solo": {"ok": "pong"}},
                "stats": {},
                "active": {},
                "reserved": {},
                "scheduled": {},
                "fallback": True,
            }
        finally:
            client.close()
    except Exception:  # noqa: BLE001
        return {}


def get_operations_center_service(
    database: DatabaseDep,
    settings: SettingsDep,
) -> OperationsCenterService:
    return OperationsCenterService(
        database,
        settings=settings,
        inspect_payload=_celery_inspect_payload(),
    )


ServiceDep = Annotated[OperationsCenterService, Depends(get_operations_center_service)]

router = APIRouter(prefix="/operations", tags=["operations-center"])


@router.get("/live")
async def live(service: ServiceDep) -> dict[str, Any]:
    return await service.live()


@router.get("/connectors")
async def connectors(service: ServiceDep) -> dict[str, Any]:
    return await service.connectors()


@router.get("/workers")
async def workers(service: ServiceDep) -> dict[str, Any]:
    return await service.workers()


@router.get("/pipeline")
async def pipeline(service: ServiceDep) -> dict[str, Any]:
    return await service.pipeline()


@router.get("/feed")
async def feed(
    service: ServiceDep,
    limit: int = Query(default=40, ge=1, le=200),
) -> dict[str, Any]:
    return await service.feed(limit=limit)


@router.get("/queues")
async def queues(service: ServiceDep) -> dict[str, Any]:
    return await service.queues()


@router.get("/health")
async def health(service: ServiceDep) -> dict[str, Any]:
    return await service.health()


@router.get("/daily")
async def daily(service: ServiceDep) -> dict[str, Any]:
    return await service.daily()
