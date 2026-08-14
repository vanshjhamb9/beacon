from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep
from app.services.revenue_quality_recovery import RevenueQualityRecoveryService

router = APIRouter(prefix="/revenue-quality", tags=["revenue-quality"])


def get_rqp_service(database: DatabaseDep) -> RevenueQualityRecoveryService:
    return RevenueQualityRecoveryService(database)


RQPServiceDep = Annotated[RevenueQualityRecoveryService, Depends(get_rqp_service)]


@router.get("/company/{company_id}")
async def get_company(company_id: UUID, service: RQPServiceDep, refresh: bool = False) -> dict:
    if refresh:
        data = await service.evaluate_company(company_id, persist=False)
    else:
        data = await service.latest(company_id)
    if not data or data.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return data


@router.post("/company/{company_id}/evaluate")
async def evaluate_company(company_id: UUID, service: RQPServiceDep) -> dict:
    data = await service.evaluate_company(company_id, persist=True)
    if data.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return data


@router.get("/founder-queue")
async def founder_queue(service: RQPServiceDep, limit: int = Query(60, ge=1, le=100)) -> dict:
    return await service.founder_queue(limit=limit)


@router.get("/kpi")
async def daily_kpi(service: RQPServiceDep) -> dict:
    return await service.daily_kpi()


@router.get("/acceptance")
async def acceptance(
    service: RQPServiceDep,
    manual_review_sample: int = Query(0, ge=0, le=1000),
    manual_review_accuracy: float = Query(0.0, ge=0.0, le=100.0),
) -> dict:
    return await service.acceptance(
        manual_review_sample=manual_review_sample,
        manual_review_accuracy=manual_review_accuracy,
    )


@router.post("/golden-dataset/seed")
async def seed_golden(service: RQPServiceDep) -> dict:
    return await service.ensure_golden_dataset()


@router.get("/dashboard")
async def dashboard(service: RQPServiceDep) -> dict:
    return await service.dashboard()


@router.post("/process-pending")
async def process_pending(service: RQPServiceDep, limit: int = Query(80, ge=1, le=500)) -> dict:
    return await service.process_pending(limit=limit)
