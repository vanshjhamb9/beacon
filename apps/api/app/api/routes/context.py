from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import DatabaseDep
from app.models.context import BusinessContext, BusinessGoal, BusinessPain, CompanyProfile, ContextEvidence
from app.repositories.context import ContextRepository
from app.schemas.context import (
    BusinessContextResponse,
    CompanyContextResponse,
    CompanyDNAResponse,
    ContextEvidenceListResponse,
    ContextEvidenceResponse,
    ContextFeedbackRequest,
    ContextFeedbackResponse,
    ContextInferenceListResponse,
    ContextInferenceResponse,
    ContextStatisticsResponse,
)
from app.services.context import ContextService

router = APIRouter(prefix="/context", tags=["context"])


def get_context_service(database: DatabaseDep) -> ContextService:
    return ContextService(ContextRepository(database))


ContextServiceDep = Annotated[ContextService, Depends(get_context_service)]


@router.get("/company/{company_id}", response_model=CompanyContextResponse)
async def company_context(
    company_id: UUID,
    service: ContextServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
) -> CompanyContextResponse:
    contexts = await service.company_context(company_id, limit=limit)
    return CompanyContextResponse(contexts=[_context_response(item) for item in contexts])


@router.get("/company/{company_id}/dna", response_model=CompanyDNAResponse)
async def company_dna(company_id: UUID, service: ContextServiceDep) -> CompanyDNAResponse:
    profile = await service.company_dna(company_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Company DNA not found.")
    return _dna_response(profile)


@router.get("/company/{company_id}/pains", response_model=ContextInferenceListResponse)
async def company_pains(
    company_id: UUID,
    service: ContextServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
) -> ContextInferenceListResponse:
    pains = await service.company_pains(company_id, limit=limit)
    return ContextInferenceListResponse(items=[_inference_response(item) for item in pains])


@router.get("/company/{company_id}/goals", response_model=ContextInferenceListResponse)
async def company_goals(
    company_id: UUID,
    service: ContextServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
) -> ContextInferenceListResponse:
    goals = await service.company_goals(company_id, limit=limit)
    return ContextInferenceListResponse(items=[_inference_response(item) for item in goals])


@router.get("/company/{company_id}/timeline", response_model=CompanyContextResponse)
async def company_context_timeline(
    company_id: UUID,
    service: ContextServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
) -> CompanyContextResponse:
    contexts = await service.company_timeline_context(company_id, limit=limit)
    return CompanyContextResponse(contexts=[_context_response(item) for item in contexts])


@router.get("/company/{company_id}/evidence", response_model=ContextEvidenceListResponse)
async def company_context_evidence(
    company_id: UUID,
    service: ContextServiceDep,
    limit: int = Query(default=200, ge=1, le=1000),
) -> ContextEvidenceListResponse:
    evidence = await service.company_evidence(company_id, limit=limit)
    return ContextEvidenceListResponse(evidence=[_evidence_response(item) for item in evidence])


@router.get("/statistics", response_model=ContextStatisticsResponse)
async def context_statistics(service: ContextServiceDep) -> ContextStatisticsResponse:
    return ContextStatisticsResponse(statistics=await service.statistics())


@router.post("/feedback", response_model=ContextFeedbackResponse)
async def context_feedback(
    payload: ContextFeedbackRequest,
    service: ContextServiceDep,
) -> ContextFeedbackResponse:
    try:
        feedback = await service.feedback(
            business_context_id=payload.business_context_id,
            reviewer=payload.reviewer,
            review_outcome=payload.review_outcome,
            corrected_fields=payload.corrected_fields,
            ground_truth=payload.ground_truth,
            notes=payload.notes,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ContextFeedbackResponse(
        id=feedback.id,
        business_context_id=feedback.business_context_id,
        reviewer=feedback.reviewer,
        review_outcome=feedback.review_outcome,
        corrected_fields=feedback.corrected_fields,
        ground_truth=feedback.ground_truth,
        notes=feedback.notes,
        created_at=feedback.created_at,
    )


def _context_response(context: BusinessContext) -> BusinessContextResponse:
    return BusinessContextResponse(
        id=context.id,
        company_id=context.company_id,
        classified_signal_id=context.classified_signal_id,
        raw_event_id=context.raw_event_id,
        quality_report_id=context.quality_report_id,
        business_urgency=context.business_urgency,
        buying_stage=context.buying_stage,
        decision_stage=context.decision_stage,
        growth_stage=context.growth_stage,
        digital_maturity=context.digital_maturity,
        ai_readiness=context.ai_readiness,
        automation_readiness=context.automation_readiness,
        budget_probability=context.budget_probability,
        technology_maturity=context.technology_maturity,
        expansion_probability=context.expansion_probability,
        operational_pressure=context.operational_pressure,
        customer_experience_pressure=context.customer_experience_pressure,
        support_pressure=context.support_pressure,
        engineering_pressure=context.engineering_pressure,
        marketing_pressure=context.marketing_pressure,
        sales_pressure=context.sales_pressure,
        confidence=context.confidence,
        evidence=context.evidence,
        created_at=context.created_at,
    )


def _dna_response(profile: CompanyProfile) -> CompanyDNAResponse:
    return CompanyDNAResponse(
        id=profile.id,
        company_id=profile.company_id,
        industry=profile.industry,
        business_model=profile.business_model,
        company_stage=profile.company_stage,
        growth_pattern=profile.growth_pattern,
        technology_stack=profile.technology_stack,
        digital_maturity=profile.digital_maturity,
        ai_adoption=profile.ai_adoption,
        automation_adoption=profile.automation_adoption,
        hiring_pattern=profile.hiring_pattern,
        expansion_pattern=profile.expansion_pattern,
        innovation_score=profile.innovation_score,
        support_maturity=profile.support_maturity,
        operational_maturity=profile.operational_maturity,
        technology_maturity=profile.technology_maturity,
        customer_maturity=profile.customer_maturity,
        completeness_score=profile.completeness_score,
        evidence=profile.evidence,
        created_at=profile.created_at,
    )


def _inference_response(item: BusinessPain | BusinessGoal) -> ContextInferenceResponse:
    return ContextInferenceResponse(
        id=item.id,
        company_id=item.company_id,
        business_context_id=item.business_context_id,
        category=item.category,
        value=item.value,
        confidence=item.confidence,
        evidence=item.evidence,
        created_at=item.created_at,
    )


def _evidence_response(item: ContextEvidence) -> ContextEvidenceResponse:
    return ContextEvidenceResponse(
        id=item.id,
        business_context_id=item.business_context_id,
        evidence_type=item.evidence_type,
        reference_id=item.reference_id,
        reference_key=item.reference_key,
        confidence=item.confidence,
        details=item.details,
        created_at=item.created_at,
    )
