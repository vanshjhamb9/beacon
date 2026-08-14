from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.dependencies import DatabaseDep
from app.repositories.client_execution import ClientExecutionRepository
from app.schemas.client_execution import ClientExecutionPackResponse
from app.services.client_execution import ClientExecutionPlatformService

router = APIRouter(prefix="/client-execution", tags=["client-execution"])


def get_aep_service(database: DatabaseDep) -> ClientExecutionPlatformService:
    return ClientExecutionPlatformService(ClientExecutionRepository(database))


AEPServiceDep = Annotated[ClientExecutionPlatformService, Depends(get_aep_service)]


class UpsellApprovalBody(BaseModel):
    approve: bool = True
    actor: str = "founder"


@router.get("/dashboard")
async def client_dashboard(service: AEPServiceDep) -> dict:
    return await service.dashboard()


@router.get("/client/{company_id}", response_model=ClientExecutionPackResponse)
async def client_pack(company_id: UUID, service: AEPServiceDep) -> ClientExecutionPackResponse:
    pack = await service.client_pack(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return ClientExecutionPackResponse.model_validate(pack)


@router.get("/health")
async def client_health(service: AEPServiceDep, limit: int = Query(50, ge=1, le=200)) -> dict:
    return await service.health(limit=limit)


@router.get("/handoff")
async def client_handoffs(service: AEPServiceDep, limit: int = Query(50, ge=1, le=200)) -> dict:
    return await service.handoffs(limit=limit)


@router.get("/upsells")
async def client_upsells(service: AEPServiceDep, limit: int = Query(50, ge=1, le=200)) -> dict:
    return await service.upsells(limit=limit)


@router.post("/upsells/{recommendation_id}/approve")
async def approve_upsell(recommendation_id: str, body: UpsellApprovalBody, service: AEPServiceDep) -> dict:
    result = await service.approve_upsell(recommendation_id, actor=body.actor, approve=body.approve)
    if result.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upsell not found")
    return result


@router.get("/projects")
async def client_projects(service: AEPServiceDep, limit: int = Query(50, ge=1, le=200)) -> dict:
    return await service.projects(limit=limit)


@router.post("/refresh")
async def refresh_clients(service: AEPServiceDep, limit: int = Query(30, ge=1, le=100)) -> dict:
    return await service.refresh_batch(limit=limit)


@router.post("/refresh/{company_id}", response_model=ClientExecutionPackResponse)
async def refresh_client(company_id: UUID, service: AEPServiceDep) -> ClientExecutionPackResponse:
    pack = await service.refresh(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return ClientExecutionPackResponse.model_validate(pack)
