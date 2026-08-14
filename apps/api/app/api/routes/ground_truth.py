from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep
from app.services.ground_truth import GroundTruthService

router = APIRouter(prefix="/ground-truth", tags=["ground-truth"])


def get_gt_service(database: DatabaseDep) -> GroundTruthService:
    return GroundTruthService(database)


GTServiceDep = Annotated[GroundTruthService, Depends(get_gt_service)]


@router.get("/company/{company_id}")
async def get_company(company_id: UUID, service: GTServiceDep, refresh: bool = False) -> dict:
    data = await service.evaluate_company(company_id, persist=False) if refresh else await service.latest(company_id)
    if not data or data.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return data


@router.post("/company/{company_id}/evaluate")
async def evaluate_company(company_id: UUID, service: GTServiceDep) -> dict:
    data = await service.evaluate_company(company_id, persist=True)
    if data.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return data


@router.get("/founder-queue")
async def founder_queue(service: GTServiceDep) -> dict:
    return await service.founder_queue()


@router.get("/funnel")
async def quality_funnel(service: GTServiceDep) -> dict:
    return await service.quality_funnel()


@router.get("/daily-report")
async def daily_report(service: GTServiceDep) -> dict:
    return await service.daily_report()


@router.get("/acceptance")
async def acceptance(service: GTServiceDep) -> dict:
    return await service.acceptance()


@router.get("/dashboard")
async def dashboard(service: GTServiceDep) -> dict:
    return await service.dashboard()


@router.post("/process-pending")
async def process_pending(service: GTServiceDep, limit: int = Query(80, ge=1, le=500)) -> dict:
    return await service.process_pending(limit=limit)
