from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import DatabaseDep
from app.repositories.outcomes import OutcomeRepository
from app.schemas.outcomes import (
    CompanyOutcomeResponse,
    OutcomeAnalyticsResponse,
    OutcomeDashboardResponse,
    OutcomeUpdateRequest,
    OutcomeUpdateResponse,
)
from app.services.outcomes import OutcomePlatformService
from outcome_intelligence.metrics.lifecycle import normalize_stage
from outcome_intelligence.models.types import OutcomeUpdateInput

router = APIRouter(prefix="/outcomes", tags=["outcome-intelligence"])


def get_outcome_service(database: DatabaseDep) -> OutcomePlatformService:
    return OutcomePlatformService(OutcomeRepository(database))


OutcomeServiceDep = Annotated[OutcomePlatformService, Depends(get_outcome_service)]


@router.get("/dashboard", response_model=OutcomeDashboardResponse)
async def get_outcomes_dashboard(service: OutcomeServiceDep) -> OutcomeDashboardResponse:
    dashboard = await service.dashboard()
    return OutcomeDashboardResponse.model_validate(dashboard.model_dump())


@router.get("/company/{company_id}", response_model=CompanyOutcomeResponse)
async def get_company_outcomes(company_id: UUID, service: OutcomeServiceDep) -> CompanyOutcomeResponse:
    try:
        report = await service.company_report(company_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CompanyOutcomeResponse.model_validate(report.model_dump())


@router.post("/update", response_model=OutcomeUpdateResponse)
async def update_outcome(body: OutcomeUpdateRequest, service: OutcomeServiceDep) -> OutcomeUpdateResponse:
    try:
        stage = normalize_stage(body.lifecycle_stage)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid lifecycle_stage '{body.lifecycle_stage}'",
        ) from exc

    payload = OutcomeUpdateInput(
        opportunity_id=body.opportunity_id,
        company_id=body.company_id,
        lifecycle_stage=stage,
        notes=body.notes,
        reason=body.reason,
        owner=body.owner,
        revenue=body.revenue,
        close_date=body.close_date,
        contacted_at=body.contacted_at,
        replied_at=body.replied_at,
        meeting_at=body.meeting_at,
        proposal_at=body.proposal_at,
        channel=body.channel,
        meeting_type=body.meeting_type,
        proposal_value=body.proposal_value,
        deal_value=body.deal_value,
        feedback_score=body.feedback_score,
        feedback_text=body.feedback_text,
        metadata=body.metadata,
        actor=body.actor,
    )
    try:
        result = await service.update(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return OutcomeUpdateResponse.model_validate(result)


@router.get("/analytics", response_model=OutcomeAnalyticsResponse)
async def get_outcomes_analytics(service: OutcomeServiceDep) -> OutcomeAnalyticsResponse:
    analytics = await service.analytics()
    return OutcomeAnalyticsResponse.model_validate(analytics.model_dump())
