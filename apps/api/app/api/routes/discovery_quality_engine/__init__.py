"""Discovery Quality Engine API router — read-only endpoints."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Query


def build_dqe_router(get_service: Callable[..., Any]) -> APIRouter:
    from typing import Annotated

    from fastapi import Depends

    router = APIRouter(prefix="/quality", tags=["discovery-quality-engine"])
    ServiceDep = Annotated[Any, Depends(get_service)]

    @router.get("/dashboard")
    async def dashboard(service: ServiceDep) -> dict[str, Any]:
        return await service.dashboard()

    @router.get("/rejections")
    async def rejections(
        service: ServiceDep,
        reason: str | None = None,
        limit: int = Query(default=100, ge=1, le=500),
    ) -> dict[str, Any]:
        return await service.rejections(reason=reason, limit=limit)

    @router.get("/connectors")
    async def connectors(service: ServiceDep) -> dict[str, Any]:
        return await service.connector_quality()

    @router.get("/companies")
    async def companies(
        service: ServiceDep,
        limit: int = Query(default=100, ge=1, le=500),
    ) -> dict[str, Any]:
        return await service.company_quality(limit=limit)

    @router.get("/signals")
    async def signals(service: ServiceDep) -> dict[str, Any]:
        return await service.signal_quality()

    @router.get("/reports/daily")
    async def daily_report(service: ServiceDep) -> dict[str, Any]:
        return await service.daily_report()

    @router.get("/reports/weekly")
    async def weekly_report(service: ServiceDep) -> dict[str, Any]:
        return await service.weekly_report()

    @router.get("/failures")
    async def failures(
        service: ServiceDep,
        gate: str | None = None,
        limit: int = Query(default=100, ge=1, le=500),
    ) -> dict[str, Any]:
        return await service.failures(gate=gate, limit=limit)

    @router.get("/freshness")
    async def freshness(service: ServiceDep) -> dict[str, Any]:
        return await service.freshness_stats()

    return router
