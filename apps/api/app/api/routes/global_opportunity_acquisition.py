from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep
from app.repositories.global_opportunity_acquisition import GlobalOpportunityAcquisitionRepository
from app.services.global_opportunity_acquisition import GlobalOpportunityAcquisitionPlatformService

router = APIRouter(prefix="/opportunity-acquisition", tags=["opportunity-acquisition"])


def get_goap_service(database: DatabaseDep) -> GlobalOpportunityAcquisitionPlatformService:
    return GlobalOpportunityAcquisitionPlatformService(GlobalOpportunityAcquisitionRepository(database))


GOAPServiceDep = Annotated[GlobalOpportunityAcquisitionPlatformService, Depends(get_goap_service)]


@router.get("/dashboard")
async def dashboard(service: GOAPServiceDep) -> dict:
    return await service.dashboard()


@router.get("/connectors")
async def connectors(service: GOAPServiceDep) -> dict:
    return await service.connectors()


@router.get("/connectors/{connector_id}")
async def connector(connector_id: str, service: GOAPServiceDep) -> dict:
    row = await service.connector(connector_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    return row


@router.get("/companies/{company_id}/graph")
async def company_graph(company_id: UUID, service: GOAPServiceDep) -> dict:
    graph = await service.company_graph(company_id)
    if graph is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not found")
    return graph


@router.get("/website")
async def websites(service: GOAPServiceDep) -> dict:
    return await service.websites()


@router.get("/website/{company_key}")
async def website(company_key: str, service: GOAPServiceDep) -> dict:
    row = await service.website(company_key)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website profile not found")
    return row


@router.get("/technology")
async def technologies(service: GOAPServiceDep) -> dict:
    return await service.technologies()


@router.get("/technology/{company_key}")
async def technology(company_key: str, service: GOAPServiceDep) -> dict:
    return await service.technology(company_key)


@router.get("/funding")
async def funding(service: GOAPServiceDep) -> dict:
    return await service.funding()


@router.get("/hiring")
async def hiring(service: GOAPServiceDep) -> dict:
    return await service.hiring()


@router.get("/reviews")
async def reviews(service: GOAPServiceDep) -> dict:
    return await service.reviews()


@router.get("/community")
async def community(service: GOAPServiceDep) -> dict:
    return await service.community()


@router.get("/benchmarks")
async def benchmarks(service: GOAPServiceDep) -> dict:
    return await service.benchmarks()


@router.get("/freshness")
async def freshness(service: GOAPServiceDep) -> dict:
    return await service.freshness()


@router.get("/analytics")
async def analytics(service: GOAPServiceDep) -> dict:
    return await service.analytics()


@router.get("/daily-report")
async def daily_report(service: GOAPServiceDep) -> dict:
    return await service.daily_report()


@router.post("/refresh")
async def refresh(service: GOAPServiceDep, limit: int = Query(40, ge=1, le=100)) -> dict:
    return await service.refresh(limit=limit)
