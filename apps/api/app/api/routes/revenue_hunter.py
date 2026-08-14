from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep, SettingsDep
from app.repositories.revenue_hunter import RevenueHunterRepository
from app.schemas.revenue_hunter import (
    FilterTaxonomyResponse,
    FounderDashboardResponse,
    RevenueHunterDossierListResponse,
    RevenueHunterDossierResponse,
    WorkQueueActionBody,
    WorkQueueItemResponse,
    WorkQueueListResponse,
)
from app.services.revenue_hunter import RevenueHunterPlatformService

router = APIRouter(prefix="/revenue-hunter", tags=["revenue-hunter"])


def get_revenue_hunter_service(database: DatabaseDep, settings: SettingsDep) -> RevenueHunterPlatformService:
    return RevenueHunterPlatformService(RevenueHunterRepository(database), settings)


HunterServiceDep = Annotated[RevenueHunterPlatformService, Depends(get_revenue_hunter_service)]


@router.get("/taxonomy", response_model=FilterTaxonomyResponse)
async def get_taxonomy(service: HunterServiceDep) -> FilterTaxonomyResponse:
    return FilterTaxonomyResponse(**service.taxonomy())


@router.get("/dossiers", response_model=RevenueHunterDossierListResponse)
async def list_dossiers(
    service: HunterServiceDep,
    grade: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> RevenueHunterDossierListResponse:
    rows = await service.list_dossiers(grade=grade, limit=limit, offset=offset)
    return RevenueHunterDossierListResponse(
        dossiers=[RevenueHunterDossierResponse.model_validate(row) for row in rows],
        total=len(rows),
    )


@router.get("/dossiers/{dossier_id}", response_model=RevenueHunterDossierResponse)
async def get_dossier(dossier_id: UUID, service: HunterServiceDep) -> RevenueHunterDossierResponse:
    row = await service.get_dossier(dossier_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier not found")
    return RevenueHunterDossierResponse.model_validate(row)


@router.get("/dashboard", response_model=FounderDashboardResponse)
async def founder_dashboard(service: HunterServiceDep) -> FounderDashboardResponse:
    return FounderDashboardResponse(**await service.founder_dashboard())


@router.get("/work-queue", response_model=WorkQueueListResponse)
async def work_queue(
    service: HunterServiceDep,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
) -> WorkQueueListResponse:
    rows = await service.work_queue(status=status_filter, limit=limit)
    return WorkQueueListResponse(
        items=[WorkQueueItemResponse.model_validate(row) for row in rows],
        total=len(rows),
    )


@router.post("/work-queue/{item_id}/action", response_model=WorkQueueItemResponse)
async def work_queue_action(
    item_id: UUID,
    body: WorkQueueActionBody,
    service: HunterServiceDep,
) -> WorkQueueItemResponse:
    try:
        row = await service.apply_action(item_id, action=body.action, actor=body.actor)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work queue item not found")
    return WorkQueueItemResponse.model_validate(row)


@router.post("/process")
async def process_pending(
    service: HunterServiceDep,
    limit: int = Query(default=40, ge=1, le=200),
) -> dict[str, Any]:
    return await service.process_pending(limit=limit)
