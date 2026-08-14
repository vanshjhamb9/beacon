from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseDep
from app.repositories.revenue_optimization import RevenueOptimizationRepository
from app.services.revenue_optimization import RevenueOptimizationPlatformService

router = APIRouter(prefix="/revenue-optimization", tags=["revenue-optimization"])


def get_roip_service(database: DatabaseDep) -> RevenueOptimizationPlatformService:
    return RevenueOptimizationPlatformService(RevenueOptimizationRepository(database))


ROIPServiceDep = Annotated[RevenueOptimizationPlatformService, Depends(get_roip_service)]


@router.get("/dashboard")
async def dashboard(service: ROIPServiceDep) -> dict:
    return await service.dashboard()


@router.get("/company/{company_id}")
async def company(company_id: UUID, service: ROIPServiceDep) -> dict:
    return await service.company(company_id)


@router.get("/campaign/{campaign_id}")
async def campaign(campaign_id: str, service: ROIPServiceDep) -> dict:
    return await service.campaign(campaign_id)


@router.get("/founder")
async def founder(service: ROIPServiceDep) -> dict:
    return await service.founder()


@router.get("/industry")
async def industry(service: ROIPServiceDep) -> dict:
    return await service.industry()


@router.get("/offers")
async def offers(service: ROIPServiceDep) -> dict:
    return await service.offers()


@router.get("/recommendations")
async def recommendations(service: ROIPServiceDep) -> dict:
    return await service.recommendations()


@router.get("/benchmarks")
async def benchmarks(service: ROIPServiceDep) -> dict:
    return await service.benchmarks()


@router.get("/learning")
async def learning(service: ROIPServiceDep) -> dict:
    return await service.learning()


@router.get("/replies")
async def replies(service: ROIPServiceDep) -> dict:
    return await service.replies()


@router.get("/search")
async def search(
    service: ROIPServiceDep,
    q: str = Query(""),
    industry: str | None = None,
    offer: str | None = None,
    reply_type: str | None = None,
) -> dict:
    return await service.search(q=q, industry=industry, offer=offer, reply_type=reply_type)


@router.post("/refresh")
async def refresh(service: ROIPServiceDep, limit: int = Query(100, ge=1, le=500)) -> dict:
    return await service.refresh(limit=limit)
