"""FastAPI router factory for Lead Intelligence Explorer APIs."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Query


def build_lead_explorer_router(get_service: Callable[..., Any]) -> APIRouter:
    from typing import Annotated
    from uuid import UUID

    from fastapi import Depends, HTTPException

    router = APIRouter(prefix="/explorer", tags=["lead-explorer"])
    ServiceDep = Annotated[Any, Depends(get_service)]

    @router.get("/search")
    async def search(
        service: ServiceDep,
        q: str = Query(default="", max_length=200),
        limit: int = Query(default=25, ge=1, le=100),
    ) -> dict[str, Any]:
        return await service.search(q, limit=limit)

    @router.get("/company/{company_id}")
    async def company(company_id: UUID, service: ServiceDep) -> dict[str, Any]:
        payload = await service.company(str(company_id))
        if payload.get("error") == "company_not_found":
            raise HTTPException(status_code=404, detail="Company not found")
        return payload

    @router.get("/timeline")
    async def timeline(
        service: ServiceDep,
        company_id: UUID = Query(...),
    ) -> dict[str, Any]:
        return await service.timeline(str(company_id))

    @router.get("/evidence")
    async def evidence(
        service: ServiceDep,
        company_id: UUID = Query(...),
    ) -> dict[str, Any]:
        return await service.evidence(str(company_id))

    @router.get("/providers")
    async def providers(
        service: ServiceDep,
        company_id: UUID | None = Query(default=None),
    ) -> dict[str, Any]:
        return await service.providers(str(company_id) if company_id else None)

    @router.get("/score")
    async def score(
        service: ServiceDep,
        company_id: UUID = Query(...),
    ) -> dict[str, Any]:
        return await service.score(str(company_id))

    @router.get("/history")
    async def history(
        service: ServiceDep,
        company_id: UUID = Query(...),
    ) -> dict[str, Any]:
        return await service.history(str(company_id))

    @router.get("/replay")
    async def replay(
        service: ServiceDep,
        company_id: UUID = Query(...),
    ) -> dict[str, Any]:
        return await service.replay(str(company_id))

    @router.get("/contribution")
    async def contribution(service: ServiceDep) -> dict[str, Any]:
        return await service.connector_contribution()

    @router.get("/compare")
    async def compare(
        service: ServiceDep,
        ready_id: UUID = Query(...),
        rejected_id: UUID = Query(...),
    ) -> dict[str, Any]:
        return await service.compare(str(ready_id), str(rejected_id))

    @router.post("/sync")
    async def sync(service: ServiceDep) -> dict[str, Any]:
        return await service.sync_all()

    return router
