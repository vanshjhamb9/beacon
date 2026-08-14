from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.dependencies import DatabaseDep
from app.services.beacon_alpha import BeaconAlphaService

router = APIRouter(prefix="/beacon-alpha", tags=["beacon-alpha"])


def get_alpha_service(database: DatabaseDep) -> BeaconAlphaService:
    return BeaconAlphaService(database)


AlphaServiceDep = Annotated[BeaconAlphaService, Depends(get_alpha_service)]


class QaDecisionBody(BaseModel):
    rating: str
    notes: str | None = None
    reviewer: str | None = Field(default="founder")


@router.get("/company/{company_id}")
async def get_company(company_id: UUID, service: AlphaServiceDep, refresh: bool = False) -> dict:
    if refresh:
        data = await service.evaluate_company(company_id, persist=False)
    else:
        data = await service.latest(company_id)
    if not data or data.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return data


@router.post("/company/{company_id}/evaluate")
async def evaluate_company(company_id: UUID, service: AlphaServiceDep) -> dict:
    data = await service.evaluate_company(company_id, persist=True)
    if data.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return data


@router.get("/founder-queue")
async def founder_queue(service: AlphaServiceDep) -> dict:
    return await service.top10()


@router.get("/qa/pending")
async def qa_pending(service: AlphaServiceDep, limit: int = Query(40, ge=1, le=100)) -> dict:
    return await service.qa_pending(limit=limit)


@router.post("/qa/{company_id}")
async def qa_decide(company_id: UUID, body: QaDecisionBody, service: AlphaServiceDep) -> dict:
    data = await service.record_qa(company_id, rating=body.rating, notes=body.notes, reviewer=body.reviewer)
    if data.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=data)
    return data


@router.get("/qa/analytics")
async def qa_analytics(service: AlphaServiceDep) -> dict:
    return await service.qa_analytics()


@router.get("/acceptance")
async def acceptance(service: AlphaServiceDep) -> dict:
    return await service.acceptance()


@router.get("/dashboard")
async def dashboard(service: AlphaServiceDep) -> dict:
    return await service.dashboard()


@router.post("/process-pending")
async def process_pending(service: AlphaServiceDep, limit: int = Query(80, ge=1, le=500)) -> dict:
    return await service.process_pending(limit=limit)
