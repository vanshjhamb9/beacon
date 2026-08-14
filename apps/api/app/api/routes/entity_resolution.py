from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseDep
from app.services.entity_resolution_erowd import EntityResolutionService

router = APIRouter(prefix="/entity-resolution", tags=["entity-resolution"])


def get_erowd_service(database: DatabaseDep) -> EntityResolutionService:
    return EntityResolutionService(database)


ErowdServiceDep = Annotated[EntityResolutionService, Depends(get_erowd_service)]


@router.get("/company/{company_id}")
async def company_card(company_id: UUID, service: ErowdServiceDep) -> dict[str, Any]:
    data = await service.company_card(company_id)
    return data or {"status": "not_found"}


@router.get("/search")
async def search(service: ErowdServiceDep, q: str = Query(min_length=1), limit: int = Query(default=40, ge=1, le=100)) -> dict[str, Any]:
    return await service.search(q, limit=limit)


@router.post("/evaluate")
async def evaluate(payload: dict[str, Any], service: ErowdServiceDep) -> dict[str, Any]:
    return service.evaluate_signal(payload)


@router.post("/rebuild")
async def rebuild(
    service: ErowdServiceDep,
    limit: int = Query(default=1000, ge=1, le=5000),
    fetch_official: bool = Query(default=False),
) -> dict[str, Any]:
    return await service.rebuild(limit=limit, fetch_official=fetch_official)


@router.get("/report")
async def report(service: ErowdServiceDep) -> dict[str, Any]:
    return await service.report()


@router.get("/dashboard")
async def dashboard(service: ErowdServiceDep) -> dict[str, Any]:
    return await service.dashboard()
