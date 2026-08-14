from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import DatabaseDep
from app.models.opportunity import (
    Opportunity,
    OpportunityEvidence,
    OpportunityHistory,
    OpportunityRecommendation,
    OpportunityTimeline,
)
from app.repositories.opportunity import OpportunityRepository
from app.schemas.opportunity import (
    OpportunitiesResponse,
    OpportunityEvidenceListResponse,
    OpportunityEvidenceResponse,
    OpportunityFeedbackRequest,
    OpportunityFeedbackResponse,
    OpportunityHistoryListResponse,
    OpportunityHistoryResponse,
    OpportunityRecommendationResponse,
    OpportunityResponse,
    OpportunityStatisticsResponse,
    OpportunityTimelineListResponse,
    OpportunityTimelineResponse,
)
from app.services.opportunity import OpportunityService

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


def get_opportunity_service(database: DatabaseDep) -> OpportunityService:
    return OpportunityService(OpportunityRepository(database))


OpportunityServiceDep = Annotated[OpportunityService, Depends(get_opportunity_service)]


@router.get("", response_model=OpportunitiesResponse)
async def list_opportunities(
    service: OpportunityServiceDep,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> OpportunitiesResponse:
    opportunities = await service.list_opportunities(status=status, limit=limit, offset=offset)
    return OpportunitiesResponse(opportunities=[_opportunity_response(item) for item in opportunities])


@router.get("/statistics", response_model=OpportunityStatisticsResponse)
async def opportunity_statistics(service: OpportunityServiceDep) -> OpportunityStatisticsResponse:
    return OpportunityStatisticsResponse(statistics=await service.statistics())


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(opportunity_id: UUID, service: OpportunityServiceDep) -> OpportunityResponse:
    opportunity = await service.get_opportunity(opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    return _opportunity_response(opportunity)


@router.get("/{opportunity_id}/history", response_model=OpportunityHistoryListResponse)
async def opportunity_history(opportunity_id: UUID, service: OpportunityServiceDep) -> OpportunityHistoryListResponse:
    return OpportunityHistoryListResponse(
        history=[_history_response(item) for item in await service.history(opportunity_id)]
    )


@router.get("/{opportunity_id}/evidence", response_model=OpportunityEvidenceListResponse)
async def opportunity_evidence(opportunity_id: UUID, service: OpportunityServiceDep) -> OpportunityEvidenceListResponse:
    return OpportunityEvidenceListResponse(
        evidence=[_evidence_response(item) for item in await service.evidence(opportunity_id)]
    )


@router.get("/{opportunity_id}/timeline", response_model=OpportunityTimelineListResponse)
async def opportunity_timeline(opportunity_id: UUID, service: OpportunityServiceDep) -> OpportunityTimelineListResponse:
    return OpportunityTimelineListResponse(
        timeline=[_timeline_response(item) for item in await service.timeline(opportunity_id)]
    )


@router.get("/{opportunity_id}/recommendation", response_model=OpportunityRecommendationResponse)
async def opportunity_recommendation(
    opportunity_id: UUID,
    service: OpportunityServiceDep,
) -> OpportunityRecommendationResponse:
    recommendation = await service.recommendation(opportunity_id)
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Opportunity recommendation not found.")
    return _recommendation_response(recommendation)


@router.post("/feedback", response_model=OpportunityFeedbackResponse)
async def opportunity_feedback(
    payload: OpportunityFeedbackRequest,
    service: OpportunityServiceDep,
) -> OpportunityFeedbackResponse:
    try:
        feedback = await service.feedback(
            opportunity_id=payload.opportunity_id,
            reviewer=payload.reviewer,
            review_outcome=payload.review_outcome,
            corrected_fields=payload.corrected_fields,
            outcome_label=payload.outcome_label,
            notes=payload.notes,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OpportunityFeedbackResponse(
        id=feedback.id,
        opportunity_id=feedback.opportunity_id,
        reviewer=feedback.reviewer,
        review_outcome=feedback.review_outcome,
        corrected_fields=feedback.corrected_fields,
        outcome_label=feedback.outcome_label,
        notes=feedback.notes,
        created_at=feedback.created_at,
    )


def _opportunity_response(item: Opportunity) -> OpportunityResponse:
    return OpportunityResponse(
        id=item.id,
        company_id=item.company_id,
        company_name=item.company_name,
        status=item.status,
        recommendation=item.recommendation,
        opportunity_score=item.opportunity_score,
        confidence_score=item.confidence_score,
        timing_score=item.timing_score,
        urgency_score=item.urgency_score,
        narrative=item.narrative,
        created_from_context_ids=item.created_from_context_ids,
        score_breakdown=item.score_breakdown,
        delta=item.delta,
        created_at=item.created_at,
    )


def _history_response(item: OpportunityHistory) -> OpportunityHistoryResponse:
    return OpportunityHistoryResponse(
        id=item.id,
        opportunity_id=item.opportunity_id,
        company_id=item.company_id,
        action=item.action,
        actor=item.actor,
        details=item.details,
        created_at=item.created_at,
    )


def _evidence_response(item: OpportunityEvidence) -> OpportunityEvidenceResponse:
    return OpportunityEvidenceResponse(
        id=item.id,
        opportunity_id=item.opportunity_id,
        company_id=item.company_id,
        source_type=item.source_type,
        reference_id=item.reference_id,
        category=item.category,
        summary=item.summary,
        confidence=item.confidence,
        polarity=item.polarity,
        weight=item.weight,
        details=item.details,
        created_at=item.created_at,
    )


def _timeline_response(item: OpportunityTimeline) -> OpportunityTimelineResponse:
    return OpportunityTimelineResponse(
        id=item.id,
        opportunity_id=item.opportunity_id,
        company_id=item.company_id,
        event_type=item.event_type,
        summary=item.summary,
        reference_id=item.reference_id,
        details=item.details,
        created_at=item.created_at,
    )


def _recommendation_response(item: OpportunityRecommendation) -> OpportunityRecommendationResponse:
    return OpportunityRecommendationResponse(
        id=item.id,
        opportunity_id=item.opportunity_id,
        company_id=item.company_id,
        action=item.action,
        confidence=item.confidence,
        reasons=item.reasons,
        next_step=item.next_step,
        created_at=item.created_at,
    )
