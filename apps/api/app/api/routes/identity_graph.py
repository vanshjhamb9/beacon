from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseDep
from app.services.identity_graph import IdentityGraphService

router = APIRouter(prefix="/identity-graph", tags=["identity-graph"])


def get_igf_service(database: DatabaseDep) -> IdentityGraphService:
    return IdentityGraphService(database)


IgfServiceDep = Annotated[IdentityGraphService, Depends(get_igf_service)]


@router.get("/company/{company_id}")
async def company_card(company_id: UUID, service: IgfServiceDep) -> dict[str, Any]:
    data = await service.company_card(company_id)
    return data or {"status": "not_found"}


@router.get("/search")
async def search(
    service: IgfServiceDep, q: str = Query(min_length=1), limit: int = Query(default=40, ge=1, le=100)
) -> dict[str, Any]:
    return await service.search(q, limit=limit)


@router.post("/evaluate")
async def evaluate(payload: dict[str, Any], service: IgfServiceDep) -> dict[str, Any]:
    return service.evaluate_signal(payload)


@router.post("/rebuild")
async def rebuild(
    service: IgfServiceDep,
    limit: int = Query(default=1000, ge=1, le=5000),
    fetch_official: bool = Query(default=False),
) -> dict[str, Any]:
    return await service.rebuild(limit=limit, fetch_official=fetch_official)


@router.get("/report")
async def report(service: IgfServiceDep) -> dict[str, Any]:
    return await service.report()


@router.get("/dashboard")
async def dashboard(service: IgfServiceDep) -> dict[str, Any]:
    return await service.dashboard()


@router.get("/funnel")
async def funnel(service: IgfServiceDep) -> dict[str, Any]:
    dash = await service.dashboard()
    return {"funnel": dash.get("funnel") or dash}
