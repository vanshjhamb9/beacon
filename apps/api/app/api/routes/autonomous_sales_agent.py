from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep
from app.repositories.autonomous_sales_agent import AutonomousSalesAgentRepository
from app.schemas.autonomous_sales_agent import (
    AutonomousSalesAgentPackResponse,
    FounderWorkQueueResponse,
    MorningBriefResponse,
)
from app.services.autonomous_sales_agent import AutonomousSalesAgentPlatformService

router = APIRouter(prefix="/autonomous-sales-agent", tags=["autonomous-sales-agent"])


def get_asa_service(database: DatabaseDep) -> AutonomousSalesAgentPlatformService:
    return AutonomousSalesAgentPlatformService(AutonomousSalesAgentRepository(database))


ASAServiceDep = Annotated[AutonomousSalesAgentPlatformService, Depends(get_asa_service)]


@router.get("/company/{company_id}", response_model=AutonomousSalesAgentPackResponse)
async def company_asa_pack(company_id: UUID, service: ASAServiceDep) -> AutonomousSalesAgentPackResponse:
    pack = await service.company_pack(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return AutonomousSalesAgentPackResponse.model_validate(pack)


@router.post("/refresh/{company_id}", response_model=AutonomousSalesAgentPackResponse)
async def refresh_company_asa(company_id: UUID, service: ASAServiceDep) -> AutonomousSalesAgentPackResponse:
    pack = await service.refresh(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return AutonomousSalesAgentPackResponse.model_validate(pack)


@router.get("/work-queue", response_model=FounderWorkQueueResponse)
async def founder_work_queue(
    service: ASAServiceDep,
    limit: int = Query(50, ge=1, le=200),
    refresh: bool = Query(False),
) -> FounderWorkQueueResponse:
    return FounderWorkQueueResponse.model_validate(await service.work_queue(limit=limit, refresh=refresh))


@router.get("/morning-brief", response_model=MorningBriefResponse)
async def morning_brief(
    service: ASAServiceDep,
    refresh: bool = Query(False),
) -> MorningBriefResponse:
    return MorningBriefResponse.model_validate(await service.morning_brief(refresh=refresh))


@router.post("/morning-brief/refresh", response_model=MorningBriefResponse)
async def refresh_morning_brief(service: ASAServiceDep) -> MorningBriefResponse:
    return MorningBriefResponse.model_validate(await service.morning_brief(refresh=True))


@router.get("/timeline/{company_id}")
async def company_timeline(company_id: UUID, service: ASAServiceDep, limit: int = Query(100, ge=1, le=500)) -> dict:
    return await service.timeline(company_id, limit=limit)


@router.get("/dashboard")
async def asa_dashboard(service: ASAServiceDep) -> dict:
    return await service.dashboard()


@router.post("/refresh-batch")
async def refresh_batch(service: ASAServiceDep, limit: int = Query(25, ge=1, le=100)) -> dict:
    return await service.refresh_batch(limit=limit)
