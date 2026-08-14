"""FastAPI router factory for Beacon Operations Center APIs."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Query


def build_operations_center_router(get_service: Callable[..., Any]) -> APIRouter:
    from typing import Annotated

    from fastapi import Depends

    router = APIRouter(tags=["operations-center"])
    ServiceDep = Annotated[Any, Depends(get_service)]

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

    return router
