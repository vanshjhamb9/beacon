from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep
from app.repositories.account_intelligence import AccountIntelligenceRepository
from app.services.account_intelligence import AccountIntelligencePlatformService

router = APIRouter(prefix="/account-intelligence", tags=["account-intelligence"])


def get_aip_service(database: DatabaseDep) -> AccountIntelligencePlatformService:
    return AccountIntelligencePlatformService(AccountIntelligenceRepository(database))


AIPServiceDep = Annotated[AccountIntelligencePlatformService, Depends(get_aip_service)]


@router.get("/dashboard")
async def dashboard(service: AIPServiceDep) -> dict:
    return await service.dashboard()


@router.get("/search")
async def search(
    service: AIPServiceDep,
    q: str = Query(""),
    industry: str | None = None,
    country: str | None = None,
    sales_readiness: str | None = None,
    technology: str | None = None,
) -> dict:
    return await service.search(
        q=q,
        industry=industry,
        country=country,
        sales_readiness=sales_readiness,
        technology=technology,
    )


@router.get("/company/{company_id}")
async def company(company_id: UUID, service: AIPServiceDep) -> dict:
    pack = await service.company(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return pack


@router.get("/company/{company_id}/contacts")
async def contacts(company_id: UUID, service: AIPServiceDep) -> dict:
    pack = await service.company(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return {
        "buying_committee": pack.get("buying_committee", []),
        "verified_contacts": pack.get("verified_contacts", []),
    }


@router.get("/company/{company_id}/technology")
async def technology(company_id: UUID, service: AIPServiceDep) -> dict:
    pack = await service.company(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return pack.get("technology", {})


@router.get("/company/{company_id}/website")
async def website(company_id: UUID, service: AIPServiceDep) -> dict:
    pack = await service.company(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return pack.get("website", {})


@router.get("/company/{company_id}/business")
async def business(company_id: UUID, service: AIPServiceDep) -> dict:
    pack = await service.company(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return {"business": pack.get("business", {}), "financial": pack.get("financial", {}), "growth": pack.get("growth", {})}


@router.get("/company/{company_id}/readiness")
async def readiness(company_id: UUID, service: AIPServiceDep) -> dict:
    pack = await service.company(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return {"ai_readiness": pack.get("ai_readiness", {}), "sales_readiness": pack.get("sales_readiness", {})}


@router.get("/company/{company_id}/relationship")
async def relationship(company_id: UUID, service: AIPServiceDep) -> dict:
    pack = await service.company(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return pack.get("relationship_graph", {})


@router.get("/company/{company_id}/timeline")
async def timeline(company_id: UUID, service: AIPServiceDep) -> dict:
    pack = await service.company(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return {"timeline": pack.get("timeline", [])}


@router.get("/company/{company_id}/verification")
async def verification(company_id: UUID, service: AIPServiceDep) -> dict:
    pack = await service.company(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return {"verification_history": pack.get("verification_history", []), "confidence": pack.get("confidence", {})}


@router.post("/refresh")
async def refresh(service: AIPServiceDep, limit: int = Query(30, ge=1, le=100)) -> dict:
    return await service.refresh_batch(limit=limit)


@router.post("/refresh/{company_id}")
async def refresh_one(company_id: UUID, service: AIPServiceDep) -> dict:
    pack = await service.refresh(company_id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return pack
