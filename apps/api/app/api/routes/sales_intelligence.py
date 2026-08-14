from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import DatabaseDep
from app.repositories.sales_intelligence import SalesIntelligenceRepository
from app.schemas.sales_intelligence import (
    SalesIntelligenceDashboardResponse,
    SalesIntelligencePackResponse,
    SalesIntelligenceRefreshResponse,
)
from app.services.sales_intelligence import SalesIntelligencePlatformService

router = APIRouter(prefix="/sales-intelligence", tags=["sales-intelligence"])


def get_sales_intelligence_service(database: DatabaseDep) -> SalesIntelligencePlatformService:
    return SalesIntelligencePlatformService(SalesIntelligenceRepository(database))


SIServiceDep = Annotated[SalesIntelligencePlatformService, Depends(get_sales_intelligence_service)]


@router.get("/company/{company_id}", response_model=SalesIntelligencePackResponse)
async def get_company_sales_intelligence(
    company_id: UUID,
    service: SIServiceDep,
) -> SalesIntelligencePackResponse:
    pack = await service.company_pack(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return SalesIntelligencePackResponse.model_validate(pack)


@router.get("/opportunity/{opportunity_id}", response_model=SalesIntelligencePackResponse)
async def get_opportunity_sales_intelligence(
    opportunity_id: UUID,
    service: SIServiceDep,
) -> SalesIntelligencePackResponse:
    pack = await service.opportunity_pack(opportunity_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity sales intelligence not found")
    return SalesIntelligencePackResponse.model_validate(pack)


@router.post("/refresh/{company_id}", response_model=SalesIntelligenceRefreshResponse)
async def refresh_sales_intelligence(
    company_id: UUID,
    service: SIServiceDep,
) -> SalesIntelligenceRefreshResponse:
    pack = await service.refresh(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return SalesIntelligenceRefreshResponse(refreshed=True, pack=SalesIntelligencePackResponse.model_validate(pack))


@router.get("/dashboard", response_model=SalesIntelligenceDashboardResponse)
async def sales_intelligence_dashboard(service: SIServiceDep) -> SalesIntelligenceDashboardResponse:
    return SalesIntelligenceDashboardResponse(**await service.dashboard())
