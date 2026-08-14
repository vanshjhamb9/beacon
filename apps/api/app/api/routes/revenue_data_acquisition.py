from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseDep
from app.services.revenue_data_acquisition import RevenueDataAcquisitionService

router = APIRouter(prefix="/revenue-data-acquisition", tags=["revenue-data-acquisition"])


def get_rdap_service(database: DatabaseDep) -> RevenueDataAcquisitionService:
    return RevenueDataAcquisitionService(database)


RdapServiceDep = Annotated[RevenueDataAcquisitionService, Depends(get_rdap_service)]


@router.get("/dashboard")
async def dashboard(service: RdapServiceDep) -> dict[str, Any]:
    return await service.dashboard()


@router.get("/connectors")
async def connectors(service: RdapServiceDep) -> dict[str, Any]:
    return await service.connectors()


@router.get("/company/{company_id}")
async def company_dossier(company_id: UUID, service: RdapServiceDep) -> dict[str, Any]:
    data = await service.company_dossier(company_id)
    return data or {"status": "not_found"}


@router.get("/recovery")
async def recovery(service: RdapServiceDep, limit: int = Query(default=50, ge=1, le=200)) -> dict[str, Any]:
    return await service.recovery_queue(limit=limit)


@router.get("/reports")
async def reports(service: RdapServiceDep) -> dict[str, Any]:
    return await service.reports()


@router.get("/revenue-yield")
async def revenue_yield(service: RdapServiceDep) -> dict[str, Any]:
    return await service.revenue_yield()


@router.post("/expand")
async def expand(
    service: RdapServiceDep,
    limit: int = Query(default=800, ge=1, le=3000),
    fetch_github: bool = Query(default=True),
    recover_contacts: bool = Query(default=True),
    recover_dms: bool = Query(default=True),
) -> dict[str, Any]:
    return await service.expand(
        limit=limit,
        fetch_github=fetch_github,
        recover_contacts=recover_contacts,
        recover_dms=recover_dms,
        crawl_companies=True,
    )


@router.post("/recovery/retry")
async def retry_recovery(service: RdapServiceDep, limit: int = Query(default=40, ge=1, le=200)) -> dict[str, Any]:
    return await service.retry_recovery(limit=limit)


@router.post("/evaluate")
async def evaluate(payload: dict[str, Any], service: RdapServiceDep) -> dict[str, Any]:
    return service.evaluate(payload)
