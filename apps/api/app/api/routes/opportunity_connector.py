from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseDep
from app.services.opportunity_connector import OpportunityConnectorService


def get_opportunity_connector_service(database: DatabaseDep) -> OpportunityConnectorService:
    return OpportunityConnectorService(database)


ServiceDep = Annotated[OpportunityConnectorService, Depends(get_opportunity_connector_service)]

router = APIRouter(prefix="/connectors", tags=["opportunity-connector-platform"])


@router.get("")
async def list_connectors(service: ServiceDep) -> dict[str, Any]:
    return await service.list_connectors()


@router.get("/health")
async def connectors_health(service: ServiceDep) -> dict[str, Any]:
    return await service.connectors_health()


@router.get("/statistics")
async def connector_statistics(
    service: ServiceDep,
    period: str = Query(default="today"),
) -> dict[str, Any]:
    return await service.connector_statistics(period=period)


@router.get("/yield")
async def connector_yield(service: ServiceDep) -> dict[str, Any]:
    return await service.connector_yield()


@router.get("/failures")
async def connector_failures(service: ServiceDep) -> dict[str, Any]:
    return await service.connector_failures()


@router.get("/feed")
async def connector_feed(
    service: ServiceDep,
    limit: int = Query(default=40, ge=1, le=200),
) -> dict[str, Any]:
    return await service.connector_feed(limit=limit)


@router.get("/events")
async def connector_events(
    service: ServiceDep,
    connector_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    accepted: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    return await service.connector_events(
        connector_id=connector_id,
        event_type=event_type,
        accepted=accepted,
        limit=limit,
    )


@router.get("/{connector_id}")
async def get_connector(
    connector_id: str,
    service: ServiceDep,
) -> dict[str, Any]:
    return await service.get_connector(connector_id)
