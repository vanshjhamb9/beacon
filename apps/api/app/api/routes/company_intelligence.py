from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseDep
from app.services.company_intelligence import CompanyIntelligenceService

router = APIRouter(prefix="/company-intelligence", tags=["company-intelligence"])


def get_cir_service(database: DatabaseDep) -> CompanyIntelligenceService:
    return CompanyIntelligenceService(database)


CirServiceDep = Annotated[CompanyIntelligenceService, Depends(get_cir_service)]


@router.get("/company/{company_id}")
async def company_card(company_id: UUID, service: CirServiceDep) -> dict[str, Any]:
    data = await service.company_card(company_id)
    return data or {"status": "not_found"}


@router.get("/dashboard")
async def dashboard(service: CirServiceDep) -> dict[str, Any]:
    return await service.dashboard()


@router.post("/rebuild")
async def rebuild(
    service: CirServiceDep,
    limit: int = Query(default=500, ge=1, le=5000),
    fetch_website: bool = Query(default=False),
) -> dict[str, Any]:
    return await service.rebuild(limit=limit, fetch_website=fetch_website)


@router.get("/search")
async def search(service: CirServiceDep, q: str = Query(min_length=1), limit: int = Query(default=40, ge=1, le=100)) -> dict[str, Any]:
    return await service.search(q, limit=limit)


@router.get("/opportunities")
async def opportunities(service: CirServiceDep) -> dict[str, Any]:
    return await service.opportunities()


@router.get("/summary")
async def summary(service: CirServiceDep) -> dict[str, Any]:
    return await service.summary()


@router.post("/evaluate")
async def evaluate(payload: dict[str, Any], service: CirServiceDep) -> dict[str, Any]:
    return service.evaluate(payload)
