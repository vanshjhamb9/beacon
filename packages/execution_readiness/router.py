"""FastAPI router factory for execution readiness APIs."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Depends


def build_execution_router(get_service: Callable[..., Any]) -> APIRouter:
    """Bind routes to an app-provided service dependency.

    Dependencies are declared as runtime `Depends` defaults rather than a
    function-local `Annotated` alias: postponed annotations (PEP 563) stringify
    parameter annotations, and a local alias can never be resolved from module
    globals, which breaks OpenAPI schema generation.
    """
    router = APIRouter(prefix="/execution", tags=["execution-readiness"])

    @router.get("/status")
    async def status(service: Any = Depends(get_service)) -> dict[str, Any]:
        return await service.get_status()

    @router.get("/readiness")
    async def readiness(service: Any = Depends(get_service)) -> dict[str, Any]:
        return await service.get_readiness()

    @router.post("/validate")
    async def validate(service: Any = Depends(get_service)) -> dict[str, Any]:
        return await service.validate()

    @router.get("/dashboard-card")
    async def dashboard_card(service: Any = Depends(get_service)) -> dict[str, Any]:
        return await service.dashboard_card()

    return router
