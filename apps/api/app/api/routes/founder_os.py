from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep
from app.repositories.founder_os import FounderOsRepository
from app.schemas.founder_os import AnalyticsTrackBody, FounderOsPackResponse
from app.services.founder_os import FounderOsPlatformService

router = APIRouter(prefix="/founder-os", tags=["founder-os"])


def get_founder_os_service(database: DatabaseDep) -> FounderOsPlatformService:
    return FounderOsPlatformService(FounderOsRepository(database))


FounderOsDep = Annotated[FounderOsPlatformService, Depends(get_founder_os_service)]


@router.get("/command-center", response_model=FounderOsPackResponse)
async def command_center(service: FounderOsDep) -> FounderOsPackResponse:
    return FounderOsPackResponse(**await service.command_center())


@router.post("/refresh", response_model=FounderOsPackResponse)
async def refresh(service: FounderOsDep) -> FounderOsPackResponse:
    return FounderOsPackResponse(**await service.refresh())


@router.get("/brief")
async def daily_brief(service: FounderOsDep) -> dict[str, Any]:
    return await service.daily_brief()


@router.get("/assistant")
async def assistant(service: FounderOsDep) -> dict[str, Any]:
    return await service.assistant()


@router.get("/tasks")
async def tasks(
    service: FounderOsDep,
    status_filter: str | None = Query(default="open", alias="status"),
) -> dict[str, Any]:
    rows = await service.tasks(status=status_filter)
    return {"tasks": rows, "total": len(rows)}


@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: UUID, service: FounderOsDep) -> dict[str, Any]:
    row = await service.complete_task(task_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return row


@router.get("/kpis")
async def kpis(service: FounderOsDep) -> dict[str, Any]:
    return await service.kpis()


@router.get("/recommendations")
async def recommendations(service: FounderOsDep) -> dict[str, Any]:
    rows = await service.recommendations()
    return {"recommendations": rows, "total": len(rows)}


@router.get("/proposals")
async def proposals(service: FounderOsDep) -> dict[str, Any]:
    rows = await service.proposals()
    return {"proposals": rows, "total": len(rows)}


@router.get("/meetings")
async def meetings(service: FounderOsDep) -> dict[str, Any]:
    rows = await service.meetings()
    return {"meetings": rows, "total": len(rows)}


@router.get("/timeline/{company_id}")
async def timeline(company_id: UUID, service: FounderOsDep) -> dict[str, Any]:
    rows = await service.timeline(company_id)
    return {"events": rows, "total": len(rows)}


@router.post("/analytics/track")
async def track_analytics(body: AnalyticsTrackBody, service: FounderOsDep) -> dict[str, str]:
    try:
        return await service.track(
            event_type=body.event_type,
            action=body.action,
            actor=body.actor,
            company_id=body.company_id,
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            payload=body.payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
