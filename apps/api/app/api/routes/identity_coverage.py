from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseDep
from app.services.identity_coverage import IdentityCoverageService

router = APIRouter(prefix="/identity-coverage", tags=["identity-coverage"])


def get_ice_service(database: DatabaseDep) -> IdentityCoverageService:
    return IdentityCoverageService(database)


IceServiceDep = Annotated[IdentityCoverageService, Depends(get_ice_service)]


@router.get("/dashboard")
async def dashboard(service: IceServiceDep) -> dict[str, Any]:
    return await service.dashboard()


@router.get("/company/{company_id}")
async def company_card(company_id: UUID, service: IceServiceDep) -> dict[str, Any]:
    data = await service.company_card(company_id)
    return data or {"status": "not_found"}


@router.get("/recovery")
async def recovery(service: IceServiceDep, limit: int = Query(default=50, ge=1, le=200)) -> dict[str, Any]:
    return await service.recovery_queue(limit=limit)


@router.get("/providers")
async def providers(service: IceServiceDep) -> dict[str, Any]:
    return await service.providers()


@router.get("/collectors")
async def collectors(service: IceServiceDep) -> dict[str, Any]:
    return await service.collectors()


@router.get("/reports")
async def reports(service: IceServiceDep) -> dict[str, Any]:
    return await service.reports()


@router.post("/retry")
async def retry(service: IceServiceDep, limit: int = Query(default=40, ge=1, le=200)) -> dict[str, Any]:
    return await service.retry_missing(limit=limit)


@router.post("/expand")
async def expand(
    service: IceServiceDep,
    limit: int = Query(default=800, ge=1, le=3000),
    fetch_github: bool = Query(default=True),
    crawl_website: bool = Query(default=True),
) -> dict[str, Any]:
    return await service.expand(limit=limit, fetch_github=fetch_github, crawl_website=crawl_website)


@router.post("/evaluate")
async def evaluate(payload: dict[str, Any], service: IceServiceDep) -> dict[str, Any]:
    return service.evaluate(payload)
