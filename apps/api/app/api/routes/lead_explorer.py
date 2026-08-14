from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import DatabaseDep
from app.services.lead_intelligence import LeadIntelligenceService


def get_lix(database: DatabaseDep) -> LeadIntelligenceService:
    return LeadIntelligenceService(database)


ServiceDep = Annotated[LeadIntelligenceService, Depends(get_lix)]
router = APIRouter(prefix="/explorer", tags=["lead-explorer"])


@router.get("/search")
async def search(
    service: ServiceDep,
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=25, ge=1, le=100),
) -> dict[str, Any]:
    return await service.search(q, limit=limit)


@router.get("/company/{company_id}")
async def company(company_id: UUID, service: ServiceDep) -> dict[str, Any]:
    payload = await service.company(str(company_id))
    if payload.get("error") == "company_not_found":
        raise HTTPException(status_code=404, detail="Company not found")
    return payload


@router.get("/timeline")
async def timeline(
    service: ServiceDep,
    company_id: UUID = Query(...),
) -> dict[str, Any]:
    return await service.timeline(str(company_id))


@router.get("/evidence")
async def evidence(
    service: ServiceDep,
    company_id: UUID = Query(...),
) -> dict[str, Any]:
    return await service.evidence(str(company_id))


@router.get("/providers")
async def providers(
    service: ServiceDep,
    company_id: UUID | None = Query(default=None),
) -> dict[str, Any]:
    return await service.providers(str(company_id) if company_id else None)


@router.get("/score")
async def score(
    service: ServiceDep,
    company_id: UUID = Query(...),
) -> dict[str, Any]:
    return await service.score(str(company_id))


@router.get("/history")
async def history(
    service: ServiceDep,
    company_id: UUID = Query(...),
) -> dict[str, Any]:
    return await service.history(str(company_id))


@router.get("/replay")
async def replay(
    service: ServiceDep,
    company_id: UUID = Query(...),
) -> dict[str, Any]:
    return await service.replay(str(company_id))


@router.get("/contribution")
async def contribution(service: ServiceDep) -> dict[str, Any]:
    return await service.connector_contribution()


@router.get("/compare")
async def compare(
    service: ServiceDep,
    ready_id: UUID = Query(...),
    rejected_id: UUID = Query(...),
) -> dict[str, Any]:
    return await service.compare(str(ready_id), str(rejected_id))


@router.post("/sync")
async def sync(service: ServiceDep) -> dict[str, Any]:
    return await service.sync_all()


@router.get("/industries/{industry}")
async def companies_by_industry(
    industry: str,
    service: ServiceDep,
    limit: int = Query(default=40, ge=1, le=100),
) -> dict[str, Any]:
    """Analytics → industry → companies → Lead Explorer helper."""
    from sqlalchemy import select

    from app.models.intelligence import Company

    rows = (
        await service.session.execute(
            select(Company)
            .where(
                Company.deleted_at.is_(None),
                Company.industry.ilike(industry),
            )
            .order_by(Company.updated_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    items = []
    for company in rows:
        profile = await service._rrp_for(company.id)
        items.append(await service._search_row(company, profile))
    return {
        "industry": industry,
        "items": items,
        "count": len(items),
        "explorer_path": "/lead-explorer",
    }
