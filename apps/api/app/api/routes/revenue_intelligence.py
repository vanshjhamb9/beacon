from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.api.dependencies import DatabaseDep, SettingsDep
from app.repositories.ecommerce_leads import EcommerceLeadRepository
from app.repositories.revenue_intelligence import RevenueIntelligenceRepository
from app.schemas.revenue_intelligence import (
    RevenueAnalyzeRequest,
    RevenueAnalyzeResponse,
    RevenueDashboardResponse,
    RevenueIntelligenceListResponse,
    RevenueIntelligenceResponse,
)
from app.services.revenue_intelligence import RevenueIntelligenceService

router = APIRouter(prefix="/revenue-intelligence", tags=["revenue-intelligence"])


def get_ri_service(database: DatabaseDep, settings: SettingsDep) -> RevenueIntelligenceService:
    return RevenueIntelligenceService(
        RevenueIntelligenceRepository(database),
        EcommerceLeadRepository(database),
        settings=settings,
    )


RIServiceDep = Annotated[RevenueIntelligenceService, Depends(get_ri_service)]


@router.get("/leads", response_model=RevenueIntelligenceListResponse)
async def list_leads(
    service: RIServiceDep,
    priority: str | None = Query(None),
    icp_match: bool | None = Query(None),
    score: float | None = Query(None, description="Minimum probability to buy"),
    platform: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> RevenueIntelligenceListResponse:
    result = await service.list_leads(
        priority=priority, icp_match=icp_match, min_probability=score,
        platform=platform, category=category, limit=limit, offset=offset,
    )
    return RevenueIntelligenceListResponse(
        leads=[RevenueIntelligenceResponse.model_validate(l) for l in result["leads"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/leads/{lead_id}", response_model=RevenueIntelligenceResponse)
async def get_lead(lead_id: UUID, service: RIServiceDep) -> RevenueIntelligenceResponse:
    lead = await service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Revenue intelligence lead not found")
    return RevenueIntelligenceResponse.model_validate(lead)


@router.get("/dashboard", response_model=RevenueDashboardResponse)
async def get_dashboard(service: RIServiceDep) -> RevenueDashboardResponse:
    stats = await service.get_dashboard()
    top_buyers = await service.get_top_buyers()
    top_pain = await service.get_highest_pain()
    fastest_growing = await service.get_highest_growth()
    stats["top_buyers"] = top_buyers
    stats["top_pain"] = top_pain
    stats["fastest_growing"] = fastest_growing
    return RevenueDashboardResponse(**stats)


@router.get("/top-buyers")
async def get_top_buyers(service: RIServiceDep, limit: int = Query(10)) -> list[dict]:
    return await service.get_top_buyers(limit=limit)


@router.get("/highest-pain")
async def get_highest_pain(service: RIServiceDep, limit: int = Query(10)) -> list[dict]:
    return await service.get_highest_pain(limit=limit)


@router.get("/highest-growth")
async def get_highest_growth(service: RIServiceDep, limit: int = Query(10)) -> list[dict]:
    return await service.get_highest_growth(limit=limit)


@router.get("/highest-probability")
async def get_highest_probability(service: RIServiceDep, limit: int = Query(10)) -> list[dict]:
    return await service.get_highest_probability(limit=limit)


@router.post("/analyze", response_model=RevenueAnalyzeResponse)
async def analyze_leads(
    request: RevenueAnalyzeRequest, service: RIServiceDep
) -> RevenueAnalyzeResponse:
    result = await service.analyze_leads(limit=request.limit, country=request.country)
    return RevenueAnalyzeResponse(
        status=result["status"],
        message=f"Analyzed {result['processed']} of {result['total_leads']} leads",
        processed=result["processed"],
    )


@router.get("/export")
async def export_leads(
    service: RIServiceDep,
    priority: str | None = Query(None),
) -> Response:
    result = await service.list_leads(priority=priority, limit=10000, offset=0)
    leads = result["leads"]
    rows = []
    for l in leads:
        rows.append({
            "company_name": l.company_name,
            "website": l.website,
            "domain": l.domain,
            "priority": l.priority,
            "pain_score": l.pain_score,
            "growth_score": l.growth_score,
            "buying_intent": l.buying_intent,
            "probability_to_buy": l.probability_to_buy,
            "revenue_potential": l.revenue_potential,
            "why_comai": l.why_comai,
            "recommended_pitch": l.recommended_pitch,
        })
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Revenue Intelligence"
    if rows:
        ws.append(list(rows[0].keys()))
        for row in rows:
            ws.append(list(row.values()))
    import io
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=revenue_intelligence.xlsx"},
    )
