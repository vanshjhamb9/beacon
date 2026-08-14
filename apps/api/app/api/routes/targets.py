from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep, SettingsDep
from app.repositories.target_account import TargetAccountRepository
from app.schemas.target_account import (
    HunterStartBody,
    HunterStatusResponse,
    ICPProfileBody,
    ICPProfileResponse,
    ICPProfileUpdateBody,
    TargetAccountListResponse,
    TargetAccountResponse,
)
from app.services.target_account import TargetAccountPlatformService

router = APIRouter(tags=["target-account-intelligence"])


def get_target_service(database: DatabaseDep, settings: SettingsDep) -> TargetAccountPlatformService:
    return TargetAccountPlatformService(TargetAccountRepository(database), settings)


TargetServiceDep = Annotated[TargetAccountPlatformService, Depends(get_target_service)]


@router.get("/targets", response_model=TargetAccountListResponse)
async def list_targets(
    service: TargetServiceDep,
    tier: str | None = None,
    icp_key: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> TargetAccountListResponse:
    rows = await service.list_targets(tier=tier, icp_key=icp_key, limit=limit, offset=offset)
    return TargetAccountListResponse(
        targets=[TargetAccountResponse.model_validate(row) for row in rows],
        total=len(rows),
    )


@router.get("/targets/dashboard")
async def targets_dashboard(service: TargetServiceDep) -> dict[str, Any]:
    return await service.dashboard()


@router.get("/targets/{target_id}", response_model=TargetAccountResponse)
async def get_target(target_id: UUID, service: TargetServiceDep) -> TargetAccountResponse:
    row = await service.get_target(target_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target account not found")
    return TargetAccountResponse.model_validate(row)


@router.get("/icp", response_model=list[ICPProfileResponse])
async def list_icps(service: TargetServiceDep) -> list[ICPProfileResponse]:
    rows = await service.list_icps()
    return [ICPProfileResponse.model_validate(row) for row in rows]


@router.post("/icp", response_model=ICPProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_icp(body: ICPProfileBody, service: TargetServiceDep) -> ICPProfileResponse:
    row = await service.create_icp(body.model_dump())
    return ICPProfileResponse.model_validate(row)


@router.put("/icp/{icp_id}", response_model=ICPProfileResponse)
async def update_icp(icp_id: UUID, body: ICPProfileUpdateBody, service: TargetServiceDep) -> ICPProfileResponse:
    row = await service.update_icp(icp_id, body.model_dump(exclude_unset=True))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ICP not found")
    return ICPProfileResponse.model_validate(row)


@router.delete("/icp/{icp_id}")
async def delete_icp(icp_id: UUID, service: TargetServiceDep) -> dict[str, bool]:
    ok = await service.delete_icp(icp_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ICP not found")
    return {"deleted": True}


@router.post("/hunter/start")
async def hunter_start(body: HunterStartBody, service: TargetServiceDep) -> dict[str, Any]:
    try:
        company_id = UUID(body.company_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid company_id") from exc
    return await service.start_hunter(company_id=company_id)


@router.get("/hunter/status", response_model=HunterStatusResponse)
async def hunter_status(
    service: TargetServiceDep,
    company_id: UUID | None = None,
) -> HunterStatusResponse:
    row = await service.hunter_status(company_id=company_id)
    return HunterStatusResponse.model_validate(row)
