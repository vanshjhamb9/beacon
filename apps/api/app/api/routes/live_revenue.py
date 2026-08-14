from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep
from app.repositories.live_revenue import LiveRevenueRepository
from app.schemas.live_revenue import (
    LREApprovalCenterResponse,
    LREDashboardResponse,
    LREPackResponse,
    LRETrackBody,
)
from app.services.live_revenue import LiveRevenuePlatformService

router = APIRouter(prefix="/live-revenue", tags=["live-revenue-execution"])


def get_live_revenue_service(database: DatabaseDep) -> LiveRevenuePlatformService:
    return LiveRevenuePlatformService(LiveRevenueRepository(database))


LREServiceDep = Annotated[LiveRevenuePlatformService, Depends(get_live_revenue_service)]


@router.get("/company/{company_id}", response_model=LREPackResponse)
async def get_company_lre(company_id: UUID, service: LREServiceDep) -> LREPackResponse:
    pack = await service.company_pack(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return LREPackResponse.model_validate(pack)


@router.post("/refresh/{company_id}", response_model=LREPackResponse)
async def refresh_company_lre(company_id: UUID, service: LREServiceDep) -> LREPackResponse:
    pack = await service.refresh(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return LREPackResponse.model_validate(pack)


@router.get("/approval-center", response_model=LREApprovalCenterResponse)
async def approval_center(
    service: LREServiceDep,
    limit: int = Query(default=50, ge=1, le=200),
) -> LREApprovalCenterResponse:
    return LREApprovalCenterResponse(**await service.approval_center(limit=limit))


@router.get("/proposals")
async def list_proposals(
    service: LREServiceDep,
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    return await service.proposals(limit=limit)


@router.get("/dashboard", response_model=LREDashboardResponse)
async def lre_dashboard(service: LREServiceDep) -> LREDashboardResponse:
    return LREDashboardResponse(**await service.dashboard())


@router.get("/command-center")
async def lre_command_center(service: LREServiceDep) -> dict:
    return await service.command_center()


@router.post("/track")
async def track_event(body: LRETrackBody, service: LREServiceDep) -> dict:
    return await service.track(
        tracking_id=body.tracking_id,
        event_type=body.event_type,
        company_id=body.company_id,
        campaign_id=body.campaign_id,
        target_url=body.target_url,
    )
