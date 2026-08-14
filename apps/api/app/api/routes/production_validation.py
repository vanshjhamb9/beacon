from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import DatabaseDep, RedisDep, SettingsDep
from app.repositories.production_validation import ProductionValidationRepository
from app.schemas.production_validation import ProductionValidationPackResponse
from app.services.production_validation import ProductionValidationPlatformService

router = APIRouter(prefix="/production-validation", tags=["production-validation"])


def get_prv_service(
    database: DatabaseDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> ProductionValidationPlatformService:
    return ProductionValidationPlatformService(
        ProductionValidationRepository(database),
        session=database,
        redis=redis,
        settings=settings,
    )


PRVServiceDep = Annotated[ProductionValidationPlatformService, Depends(get_prv_service)]


@router.get("/report", response_model=ProductionValidationPackResponse)
async def production_readiness_report(service: PRVServiceDep) -> ProductionValidationPackResponse:
    return ProductionValidationPackResponse.model_validate(await service.report())


@router.post("/refresh", response_model=ProductionValidationPackResponse)
async def refresh_production_validation(service: PRVServiceDep) -> ProductionValidationPackResponse:
    return ProductionValidationPackResponse.model_validate(await service.refresh())


@router.get("/health")
async def production_health(service: PRVServiceDep) -> dict:
    return await service.production_health()


@router.get("/revenue")
async def revenue_dashboard(service: PRVServiceDep) -> dict:
    return await service.revenue_dashboard()


@router.get("/alerts")
async def production_alerts(service: PRVServiceDep) -> dict:
    return await service.alerts()


@router.get("/playbooks")
async def playbooks(service: PRVServiceDep) -> dict:
    return await service.playbooks()


@router.get("/campaigns/monitoring")
async def campaign_monitoring(service: PRVServiceDep) -> dict:
    return await service.campaign_monitoring()


@router.get("/lead-readiness/{company_id}")
async def lead_readiness(company_id: UUID, service: PRVServiceDep) -> dict:
    pack = await service.company_readiness(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return pack
