from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseDep
from app.services.company_resolution import CompanyResolutionService

router = APIRouter(prefix="/company-resolution", tags=["company-resolution"])


def get_cre_service(database: DatabaseDep) -> CompanyResolutionService:
    return CompanyResolutionService(database)


CreServiceDep = Annotated[CompanyResolutionService, Depends(get_cre_service)]


@router.get("/dashboard")
async def dashboard(service: CreServiceDep) -> dict[str, Any]:
    return await service.dashboard()


@router.post("/evaluate")
async def evaluate(payload: dict[str, Any], service: CreServiceDep) -> dict[str, Any]:
    return service.evaluate_signal(payload)


@router.post("/rebuild")
async def rebuild(
    service: CreServiceDep,
    limit: int = Query(default=1000, ge=1, le=5000),
    soft_delete_companies: bool = Query(default=True),
) -> dict[str, Any]:
    return await service.rebuild_from_raw_events(limit=limit, soft_delete_companies=soft_delete_companies)


@router.get("/rebuild/latest")
async def latest_rebuild(service: CreServiceDep) -> dict[str, Any]:
    data = await service.latest_rebuild_report()
    return data or {"status": "empty"}
