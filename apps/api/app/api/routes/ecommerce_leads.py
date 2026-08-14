from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.api.dependencies import DatabaseDep, SettingsDep
from app.repositories.ecommerce_leads import EcommerceLeadRepository
from app.schemas.ecommerce_leads import (
    EcommerceDiscoverRequest,
    EcommerceDiscoverResponse,
    EcommerceExportResponse,
    EcommerceLeadListResponse,
    EcommerceLeadResponse,
    EcommerceStatsResponse,
)
from app.services.ecommerce_leads import EcommerceLeadsService

router = APIRouter(prefix="/ecommerce", tags=["ecommerce-leads"])


def get_ecommerce_service(database: DatabaseDep, settings: SettingsDep) -> EcommerceLeadsService:
    return EcommerceLeadsService(EcommerceLeadRepository(database), settings=settings)


EcommerceServiceDep = Annotated[EcommerceLeadsService, Depends(get_ecommerce_service)]


@router.get("/leads", response_model=EcommerceLeadListResponse)
async def list_leads(
    service: EcommerceServiceDep,
    country: str | None = Query(None, description="Filter by country"),
    state: str | None = Query(None, description="Filter by state"),
    category: str | None = Query(None, description="Filter by category"),
    platform: str | None = Query(None, description="Filter by platform"),
    score: float | None = Query(None, description="Minimum COMAI score"),
    priority: str | None = Query(None, description="Filter by priority (HOT/WARM/LOW)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> EcommerceLeadListResponse:
    result = await service.list_leads(
        country=country,
        state=state,
        category=category,
        platform=platform,
        min_score=score,
        priority=priority,
        limit=limit,
        offset=offset,
    )
    return EcommerceLeadListResponse(
        leads=[EcommerceLeadResponse.model_validate(l) for l in result["leads"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/leads/{lead_id}", response_model=EcommerceLeadResponse)
async def get_lead(
    lead_id: UUID,
    service: EcommerceServiceDep,
) -> EcommerceLeadResponse:
    lead = await service.get_lead(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Ecommerce lead not found")
    return EcommerceLeadResponse.model_validate(lead)


@router.post("/discover", response_model=EcommerceDiscoverResponse)
async def discover_leads(
    request: EcommerceDiscoverRequest,
    service: EcommerceServiceDep,
) -> EcommerceDiscoverResponse:
    try:
        from worker.ecommerce_leads_tasks import run_ecommerce_discovery
        run_ecommerce_discovery.delay(limit=request.limit, country=request.country)
    except ImportError:
        import logging
        logging.getLogger(__name__).warning("Celery worker not available, running discovery inline")
        import asyncio
        asyncio.create_task(service.discover_leads(limit=request.limit, country=request.country))
    return EcommerceDiscoverResponse(
        status="started",
        message=f"Discovery started (limit={request.limit}, country={request.country}). Check back in a few minutes.",
    )


@router.get("/export")
async def export_leads(
    service: EcommerceServiceDep,
    country: str | None = Query(None),
    state: str | None = Query(None),
    category: str | None = Query(None),
    platform: str | None = Query(None),
    score: float | None = Query(None),
    priority: str | None = Query(None),
) -> Response:
    excel_bytes = await service.export_leads(
        country=country,
        state=state,
        category=category,
        platform=platform,
        min_score=score,
        priority=priority,
    )
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=india_ecommerce_leads.xlsx"
        },
    )


@router.get("/stats", response_model=EcommerceStatsResponse)
async def get_stats(
    service: EcommerceServiceDep,
) -> EcommerceStatsResponse:
    stats = await service.get_stats()
    return EcommerceStatsResponse(**stats)
