from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep
from app.services.sales_readiness import SalesReadinessService

router = APIRouter(prefix="/sales-readiness", tags=["sales-readiness"])


def get_sre_service(database: DatabaseDep) -> SalesReadinessService:
    return SalesReadinessService(database)


SREServiceDep = Annotated[SalesReadinessService, Depends(get_sre_service)]


@router.get("/company/{company_id}")
async def get_company(company_id: UUID, service: SREServiceDep, refresh: bool = False) -> dict:
    if refresh:
        data = await service.evaluate_company(company_id, persist=False)
    else:
        data = await service.latest(company_id)
    if not data or data.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return data


@router.post("/company/{company_id}/evaluate")
async def evaluate_company(company_id: UUID, service: SREServiceDep) -> dict:
    data = await service.evaluate_company(company_id, persist=True)
    if data.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return data


@router.get("/dashboard")
async def dashboard(service: SREServiceDep) -> dict:
    return await service.dashboard()


@router.get("/search")
async def search(
    service: SREServiceDep,
    q: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    return await service.search(q=q, status=status_filter, limit=limit)


@router.get("/trust")
async def trust(service: SREServiceDep) -> dict:
    return await service.trust_dashboard()


@router.get("/outreach-ready")
async def outreach_ready(service: SREServiceDep, limit: int = Query(50, ge=1, le=200)) -> dict:
    return await service.list_by_flag(flag="outreach-ready", limit=limit)


@router.get("/high-intent")
async def high_intent(service: SREServiceDep, limit: int = Query(50, ge=1, le=200)) -> dict:
    return await service.list_by_flag(flag="high-intent", limit=limit)


@router.get("/enterprise")
async def enterprise(service: SREServiceDep, limit: int = Query(50, ge=1, le=200)) -> dict:
    return await service.list_by_flag(flag="enterprise", limit=limit)
