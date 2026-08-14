from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep
from app.repositories.account_journey import AccountJourneyRepository
from app.schemas.account_journey import AccountJourneyPackResponse
from app.services.account_journey import AccountJourneyPlatformService

router = APIRouter(prefix="/account-journey", tags=["account-journey"])


def get_goi_service(database: DatabaseDep) -> AccountJourneyPlatformService:
    return AccountJourneyPlatformService(AccountJourneyRepository(database))


GOIServiceDep = Annotated[AccountJourneyPlatformService, Depends(get_goi_service)]


@router.get("/company/{company_id}", response_model=AccountJourneyPackResponse)
async def company_journey(company_id: UUID, service: GOIServiceDep) -> AccountJourneyPackResponse:
    pack = await service.company_pack(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return AccountJourneyPackResponse.model_validate(pack)


@router.post("/refresh")
async def refresh_journeys(service: GOIServiceDep, limit: int = Query(30, ge=1, le=100)) -> dict:
    return await service.refresh_batch(limit=limit)


@router.post("/refresh/{company_id}", response_model=AccountJourneyPackResponse)
async def refresh_company(company_id: UUID, service: GOIServiceDep) -> AccountJourneyPackResponse:
    pack = await service.refresh(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return AccountJourneyPackResponse.model_validate(pack)


@router.get("/dashboard")
async def journey_dashboard(service: GOIServiceDep) -> dict:
    return await service.dashboard()


@router.get("/followups")
async def journey_followups(service: GOIServiceDep, limit: int = Query(50, ge=1, le=200)) -> dict:
    return await service.followups(limit=limit)


@router.get("/analytics")
async def journey_analytics(service: GOIServiceDep) -> dict:
    return await service.analytics()


@router.get("/replies")
async def journey_replies(service: GOIServiceDep, limit: int = Query(50, ge=1, le=200)) -> dict:
    return await service.replies(limit=limit)


@router.get("/health")
async def journey_health(service: GOIServiceDep, limit: int = Query(50, ge=1, le=200)) -> dict:
    return await service.health(limit=limit)
