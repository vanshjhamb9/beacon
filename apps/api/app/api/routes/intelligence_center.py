from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import DatabaseDep
from app.services.intelligence_center import IntelligenceCenterService

router = APIRouter(tags=["intelligence-center"])


def get_bic(database: DatabaseDep) -> IntelligenceCenterService:
    return IntelligenceCenterService(database)


BicDep = Annotated[IntelligenceCenterService, Depends(get_bic)]

discoveries_router = APIRouter(prefix="/discoveries", tags=["discoveries"])
connectors_router = APIRouter(prefix="/connectors", tags=["connectors"])
dataset_router = APIRouter(prefix="/dataset", tags=["dataset"])
company_router = APIRouter(prefix="/company", tags=["company-journey"])
pipeline_router = APIRouter(prefix="/pipeline", tags=["pipeline-replay"])
analytics_router = APIRouter(prefix="/analytics", tags=["analytics-v2"])
search_router = APIRouter(prefix="/intelligence", tags=["intelligence-search"])


@discoveries_router.get("/live")
async def discoveries_live(
    service: BicDep,
    limit: int = Query(default=80, ge=1, le=300),
    collector: str | None = None,
    industry: str | None = None,
    status: str | None = None,
    connector: str | None = None,
    company: str | None = None,
    revenue_ready_only: bool = False,
    errors_only: bool = False,
) -> dict[str, Any]:
    return await service.discoveries_live(
        limit=limit,
        collector=collector,
        industry=industry,
        status=status,
        connector=connector,
        company=company,
        revenue_ready_only=revenue_ready_only,
        errors_only=errors_only,
    )


@discoveries_router.get("/company/{company_id}")
async def discoveries_company(company_id: UUID, service: BicDep) -> dict[str, Any]:
    return await service.discoveries_for_company(str(company_id))


@connectors_router.get("/roi")
async def connectors_roi(service: BicDep) -> dict[str, Any]:
    return await service.connectors_roi()


@dataset_router.get("/statistics")
async def dataset_statistics(
    service: BicDep,
    days: int = Query(default=30, ge=1, le=90),
) -> dict[str, Any]:
    return await service.dataset_statistics(days=days)


@company_router.get("/{company_id}/journey")
async def company_journey(company_id: UUID, service: BicDep) -> dict[str, Any]:
    payload = await service.company_journey(str(company_id))
    if payload.get("error") == "company_not_found":
        raise HTTPException(status_code=404, detail="Company not found")
    return payload


@pipeline_router.get("/replay")
async def pipeline_replay(service: BicDep) -> dict[str, Any]:
    return await service.pipeline_replay()


@analytics_router.get("/v2")
async def analytics_v2(service: BicDep) -> dict[str, Any]:
    return await service.analytics_v2()


@search_router.get("/search")
async def intelligence_search(
    service: BicDep,
    q: str = Query(default="", min_length=0, max_length=200),
    limit: int = Query(default=40, ge=1, le=100),
) -> dict[str, Any]:
    return await service.operations_search(q, limit=limit)


@search_router.post("/sync")
async def intelligence_sync(service: BicDep) -> dict[str, Any]:
    return await service.sync_all()


def build_routers() -> list[APIRouter]:
    return [
        discoveries_router,
        connectors_router,
        dataset_router,
        company_router,
        pipeline_router,
        analytics_router,
        search_router,
    ]
