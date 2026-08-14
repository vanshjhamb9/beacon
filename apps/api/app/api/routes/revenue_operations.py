from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.dependencies import DatabaseDep
from app.repositories.revenue_operations import RevenueOperationsRepository
from app.schemas.revenue_operations import RevenueOperationsDashboardResponse
from app.services.revenue_operations import RevenueOperationsPlatformService

router = APIRouter(prefix="/revenue-operations", tags=["revenue-operations"])


def get_roc_service(database: DatabaseDep) -> RevenueOperationsPlatformService:
    return RevenueOperationsPlatformService(RevenueOperationsRepository(database))


ROCServiceDep = Annotated[RevenueOperationsPlatformService, Depends(get_roc_service)]


class AlertTransitionBody(BaseModel):
    target: str = Field(..., description="viewed|resolved|dismissed|archived")


class LearningApprovalBody(BaseModel):
    approve: bool = True
    actor: str = "founder"


@router.get("/dashboard", response_model=RevenueOperationsDashboardResponse)
async def roc_dashboard(service: ROCServiceDep, refresh: bool = Query(False)) -> RevenueOperationsDashboardResponse:
    return RevenueOperationsDashboardResponse.model_validate(await service.dashboard(refresh=refresh))


@router.post("/refresh", response_model=RevenueOperationsDashboardResponse)
async def roc_refresh(service: ROCServiceDep) -> RevenueOperationsDashboardResponse:
    return RevenueOperationsDashboardResponse.model_validate(await service.refresh())


@router.get("/forecast")
async def roc_forecast(service: ROCServiceDep, refresh: bool = Query(False)) -> dict:
    return await service.forecast(refresh=refresh)


@router.get("/alerts")
async def roc_alerts(
    service: ROCServiceDep,
    lifecycle: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    return await service.alerts(lifecycle=lifecycle, limit=limit)


@router.post("/alerts/{alert_id}/transition")
async def roc_alert_transition(alert_id: UUID, body: AlertTransitionBody, service: ROCServiceDep) -> dict:
    result = await service.transition_alert(alert_id, body.target)
    if result.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return result


@router.get("/memory")
async def roc_memory(service: ROCServiceDep, q: str = Query(""), limit: int = Query(50, ge=1, le=200)) -> dict:
    return await service.memory(query=q, limit=limit)


@router.get("/replay/{replay_id}")
async def roc_replay(replay_id: UUID, service: ROCServiceDep) -> dict:
    pack = await service.replay(replay_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Replay not found")
    return pack


@router.get("/learning")
async def roc_learning(
    service: ROCServiceDep,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    return await service.learning(status=status_filter, limit=limit)


@router.post("/learning/{recommendation_id}/approve")
async def roc_approve_learning(recommendation_id: str, body: LearningApprovalBody, service: ROCServiceDep) -> dict:
    result = await service.approve_learning(recommendation_id, actor=body.actor, approve=body.approve)
    if result.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    return result


@router.get("/metrics")
async def roc_metrics(service: ROCServiceDep, refresh: bool = Query(False)) -> dict:
    return await service.metrics(refresh=refresh)
