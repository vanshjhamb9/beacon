from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import DatabaseDep
from app.repositories.revenue import RevenueRepository
from app.schemas.revenue import (
    RevenueBuyerPersonaResponse,
    RevenueCompanyResponse,
    RevenueCompanySummary,
    RevenueOpportunitiesResponse,
    RevenueOpportunityItemResponse,
    RevenuePlaybookDetailResponse,
    RevenuePlaybookResponse,
    RevenueStatisticsResponse,
)
from app.services.revenue import RevenueService

router = APIRouter(prefix="/revenue", tags=["revenue"])


def get_revenue_service(database: DatabaseDep) -> RevenueService:
    return RevenueService(RevenueRepository(database))


RevenueServiceDep = Annotated[RevenueService, Depends(get_revenue_service)]


@router.get("/opportunities", response_model=RevenueOpportunitiesResponse)
async def list_revenue_opportunities(
    service: RevenueServiceDep,
    priority: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> RevenueOpportunitiesResponse:
    opportunities = await service.list_opportunities(priority=priority, limit=limit, offset=offset)
    return RevenueOpportunitiesResponse(
        opportunities=[_opportunity_response(item) for item in opportunities]
    )


@router.get("/statistics", response_model=RevenueStatisticsResponse)
async def revenue_statistics(service: RevenueServiceDep) -> RevenueStatisticsResponse:
    return RevenueStatisticsResponse(statistics=await service.statistics())


@router.get("/company/{company_id}", response_model=RevenueCompanyResponse)
async def get_company_revenue(company_id: UUID, service: RevenueServiceDep) -> RevenueCompanyResponse:
    payload = await service.company_revenue(company_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Revenue recommendation not found for company.")
    return _company_response(payload)


@router.get("/company/{company_id}/playbook", response_model=RevenuePlaybookDetailResponse)
async def get_company_playbook(
    company_id: UUID,
    service: RevenueServiceDep,
) -> RevenuePlaybookDetailResponse:
    playbook = await service.company_playbook(company_id)
    if playbook is None:
        raise HTTPException(status_code=404, detail="Sales playbook not found for company.")
    return RevenuePlaybookDetailResponse(
        company_id=playbook.company_id,
        opportunity_id=playbook.opportunity_id,
        solution_match_id=playbook.solution_match_id,
        business_pain=playbook.business_pain,
        recommended_service=playbook.recommended_service,
        why=playbook.why,
        conversation_angle=playbook.conversation_angle,
        decision_maker=playbook.decision_maker,
        expected_outcome=playbook.expected_outcome,
        risk=playbook.risk,
        created_at=playbook.created_at,
    )


def _opportunity_response(item: dict[str, Any]) -> RevenueOpportunityItemResponse:
    return RevenueOpportunityItemResponse(
        company=RevenueCompanySummary(**item["company"]),
        opportunity_id=item["opportunity_id"],
        solution_match_id=item["solution_match_id"],
        opportunity_score=item["opportunity_score"],
        business_pain=item["business_pain"],
        recommended_service=item["recommended_service"],
        secondary_service=item["secondary_service"],
        buyer_persona=(
            RevenueBuyerPersonaResponse(**item["buyer_persona"]) if item["buyer_persona"] else None
        ),
        buyer_personas=[RevenueBuyerPersonaResponse(**persona) for persona in item["buyer_personas"]],
        estimated_budget_range=item["estimated_budget_range"],
        project_size=item["project_size"],
        implementation_complexity=item["implementation_complexity"],
        priority=item["priority"],
        confidence=item["confidence"],
        evidence=item["evidence"],
        reason=item["reason"],
        playbook=RevenuePlaybookResponse(**item["playbook"]) if item["playbook"] else None,
        created_at=item["created_at"],
    )


def _company_response(item: dict[str, Any]) -> RevenueCompanyResponse:
    return RevenueCompanyResponse(
        company=RevenueCompanySummary(**item["company"]),
        opportunity_id=item["opportunity_id"],
        solution_match_id=item["solution_match_id"],
        opportunity_score=item["opportunity_score"],
        business_pain=item["business_pain"],
        recommended_service=item["recommended_service"],
        secondary_service=item["secondary_service"],
        buyer_persona=(
            RevenueBuyerPersonaResponse(**item["buyer_persona"]) if item["buyer_persona"] else None
        ),
        buyer_personas=[RevenueBuyerPersonaResponse(**persona) for persona in item["buyer_personas"]],
        estimated_budget_range=item["estimated_budget_range"],
        project_size=item["project_size"],
        implementation_complexity=item["implementation_complexity"],
        priority=item["priority"],
        confidence=item["confidence"],
        evidence=item["evidence"],
        reason=item["reason"],
        playbook=RevenuePlaybookResponse(**item["playbook"]) if item["playbook"] else None,
        created_at=item["created_at"],
    )
