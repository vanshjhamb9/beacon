from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep
from app.services.revenue_data_recovery import RevenueDataRecoveryService

router = APIRouter(prefix="/revenue-data-recovery", tags=["revenue-data-recovery"])


def get_rdi_service(database: DatabaseDep) -> RevenueDataRecoveryService:
    return RevenueDataRecoveryService(database)


RDIServiceDep = Annotated[RevenueDataRecoveryService, Depends(get_rdi_service)]


@router.get("/company/{company_id}")
async def get_company(company_id: UUID, service: RDIServiceDep, refresh: bool = False) -> dict:
    if refresh:
        data = await service.evaluate_company(company_id, persist=False)
    else:
        data = await service.latest(company_id)
    if not data or data.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return data


@router.post("/company/{company_id}/evaluate")
async def evaluate_company(company_id: UUID, service: RDIServiceDep) -> dict:
    data = await service.evaluate_company(company_id, persist=True)
    if data.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return data


@router.get("/company/{company_id}/dossier")
async def get_dossier(company_id: UUID, service: RDIServiceDep) -> dict:
    data = await service.dossier(company_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return data


@router.get("/queue")
async def recovery_queue(
    service: RDIServiceDep,
    stage: str | None = None,
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    return await service.recovery_queue(stage=stage, limit=limit)


@router.get("/founder-queue")
async def founder_queue(service: RDIServiceDep, limit: int = Query(60, ge=1, le=100)) -> dict:
    return await service.founder_queue(limit=limit)


@router.get("/dashboard")
async def dashboard(service: RDIServiceDep) -> dict:
    return await service.dashboard()


@router.get("/qa")
async def qa_dashboard(service: RDIServiceDep) -> dict:
    return await service.qa_dashboard()


@router.post("/process-pending")
async def process_pending(service: RDIServiceDep, limit: int = Query(80, ge=1, le=500)) -> dict:
    return await service.process_pending(limit=limit)
