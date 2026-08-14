"""Beacon Operations Center background tasks (BOC v1)."""

from __future__ import annotations

import logging
from typing import Any

from app.db.session import AsyncSessionLocal
from worker.async_runtime import run_async
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def _celery_inspect_payload() -> dict[str, Any]:
    try:
        inspector = celery_app.control.inspect(timeout=1.0)
        if inspector is None:
            return {}
        return {
            "ping": inspector.ping() or {},
            "stats": inspector.stats() or {},
            "active": inspector.active() or {},
            "reserved": inspector.reserved() or {},
            "scheduled": inspector.scheduled() or {},
        }
    except Exception:  # noqa: BLE001 — ops probe must not crash worker
        return {}


@celery_app.task(name="operations_center.refresh_metrics")
def refresh_metrics() -> dict[str, Any]:
    return run_async(_refresh_metrics())


async def _refresh_metrics() -> dict[str, Any]:
    from app.services.operations_center import OperationsCenterService

    async with AsyncSessionLocal() as session:
        service = OperationsCenterService(session, inspect_payload=_celery_inspect_payload())
        result = await service.refresh_metrics()
        await session.commit()
    logger.info("BOC metrics refreshed", extra={"extra": {"stages": result.get("stages", {})}})
    return result


@celery_app.task(name="operations_center.hourly_snapshot")
def hourly_snapshot() -> dict[str, Any]:
    return run_async(_hourly_snapshot())


async def _hourly_snapshot() -> dict[str, Any]:
    from app.services.operations_center import OperationsCenterService

    async with AsyncSessionLocal() as session:
        service = OperationsCenterService(session)
        result = await service.take_hourly_snapshot()
        await session.commit()
    logger.info("BOC hourly snapshot taken", extra={"extra": result})
    return result


@celery_app.task(name="operations_center.emit_event")
def emit_event(
    collector: str,
    status: str,
    company: str | None = None,
    reason: str | None = None,
    duration: float | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return run_async(
        _emit_event(
            collector=collector,
            status=status,
            company=company,
            reason=reason,
            duration=duration,
            payload=payload,
        )
    )


async def _emit_event(
    *,
    collector: str,
    status: str,
    company: str | None,
    reason: str | None,
    duration: float | None,
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    from app.services.operations_center import OperationsCenterService

    async with AsyncSessionLocal() as session:
        service = OperationsCenterService(session)
        result = await service.emit_ingestion_event(
            collector=collector,
            status=status,
            company=company,
            reason=reason,
            duration=duration,
            payload=payload,
        )
        await session.commit()
    return result
