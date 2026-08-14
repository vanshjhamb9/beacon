from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import DatabaseDep, SettingsDep
from app.repositories.enrichment import EnrichmentRepository
from app.schemas.enrichment import (
    ContactEntryResponse,
    EnrichedCompanyProfileResponse,
    EnrichmentRefreshResponse,
    EnrichmentScoresResponse,
    EvidenceChainItemResponse,
    JobEntryResponse,
    PersonEntryResponse,
    SalesReadyLeadProfileResponse,
    SocialProfileResponse,
    SourceAttributionResponse,
    TeamInsightsResponse,
    TechnologyEntryResponse,
)
from app.services.enrichment import LeadEnrichmentService

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


def get_enrichment_service(database: DatabaseDep, settings: SettingsDep) -> LeadEnrichmentService:
    return LeadEnrichmentService(EnrichmentRepository(database), settings=settings)


EnrichmentServiceDep = Annotated[LeadEnrichmentService, Depends(get_enrichment_service)]


@router.get("/company/{company_id}", response_model=SalesReadyLeadProfileResponse)
async def get_company_enrichment(
    company_id: UUID,
    service: EnrichmentServiceDep,
) -> SalesReadyLeadProfileResponse:
    payload = await service.company_lead_profile(company_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Sales-ready lead profile not found for company.")
    return _profile_response(payload)


@router.get("/opportunity/{opportunity_id}", response_model=SalesReadyLeadProfileResponse)
async def get_opportunity_enrichment(
    opportunity_id: UUID,
    service: EnrichmentServiceDep,
) -> SalesReadyLeadProfileResponse:
    payload = await service.opportunity_lead_profile(opportunity_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Sales-ready lead profile not found for opportunity.")
    return _profile_response(payload)


@router.post("/refresh/{entity_id}", response_model=EnrichmentRefreshResponse)
async def refresh_enrichment(
    entity_id: UUID,
    service: EnrichmentServiceDep,
) -> EnrichmentRefreshResponse:
    payload = await service.refresh(entity_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Unable to refresh enrichment for the given id.")
    return EnrichmentRefreshResponse(refreshed=True, profile=_profile_response(payload))


def _profile_response(payload: dict[str, Any]) -> SalesReadyLeadProfileResponse:
    company_profile = payload.get("company_profile") or {}
    scores = payload.get("enrichment_confidence") or {}
    team = payload.get("team_insights") or {}
    report_id = payload.get("enrichment_report_id")
    created_at = payload.get("created_at")

    return SalesReadyLeadProfileResponse(
        company_id=UUID(str(payload["company_id"])),
        opportunity_id=UUID(str(payload["opportunity_id"])),
        company_name=str(payload["company_name"]),
        opportunity_score=float(payload["opportunity_score"]),
        business_pain=str(payload["business_pain"]),
        recommended_service=str(payload["recommended_service"]),
        buyer_persona=str(payload["buyer_persona"]),
        company_profile=EnrichedCompanyProfileResponse(
            company_name=str(company_profile.get("company_name") or payload["company_name"]),
            website=company_profile.get("website"),
            domain=company_profile.get("domain"),
            industry=company_profile.get("industry"),
            sub_industry=company_profile.get("sub_industry"),
            description=company_profile.get("description"),
            location=company_profile.get("location"),
            country=company_profile.get("country"),
            founded_year=company_profile.get("founded_year"),
            employee_count_estimate=company_profile.get("employee_count_estimate"),
            company_size_range=company_profile.get("company_size_range"),
            revenue_estimate=company_profile.get("revenue_estimate"),
            attributions=list(company_profile.get("attributions") or []),
        ),
        technology_stack=[
            TechnologyEntryResponse(
                name=str(item.get("name")),
                category=str(item.get("category")),
                confidence=float(item.get("confidence") or 0.0),
                source=str(item.get("source")),
                source_url=item.get("source_url"),
                signal=item.get("signal"),
            )
            for item in payload.get("technology_stack") or []
        ],
        decision_makers=[
            PersonEntryResponse(
                name=str(item.get("name")),
                role=str(item.get("role")),
                department=item.get("department"),
                linkedin_url=item.get("linkedin_url"),
                work_email=item.get("work_email"),
                business_phone=item.get("business_phone"),
                confidence=float(item.get("confidence") or 0.0),
                source=str(item.get("source")),
                source_url=item.get("source_url"),
            )
            for item in payload.get("decision_makers") or []
        ],
        public_contact_information=[
            ContactEntryResponse(
                kind=str(item.get("kind")),
                value=str(item.get("value")),
                label=item.get("label"),
                confidence=float(item.get("confidence") or 0.0),
                source=str(item.get("source")),
                source_url=item.get("source_url"),
                is_public=bool(item.get("is_public", True)),
            )
            for item in payload.get("public_contact_information") or []
        ],
        team_insights=TeamInsightsResponse(
            leadership_team_size=team.get("leadership_team_size"),
            engineering_team_estimate=team.get("engineering_team_estimate"),
            support_team_estimate=team.get("support_team_estimate"),
            operations_team_estimate=team.get("operations_team_estimate"),
            recent_hires=list(team.get("recent_hires") or []),
            open_positions=list(team.get("open_positions") or []),
            hiring_trends=team.get("hiring_trends"),
        ),
        social_profiles=[
            SocialProfileResponse(
                platform=str(item.get("platform")),
                url=str(item.get("url")),
                handle=item.get("handle"),
                confidence=float(item.get("confidence") or 0.0),
                source=str(item.get("source")),
            )
            for item in payload.get("social_profiles") or []
        ],
        open_jobs=[
            JobEntryResponse(
                title=str(item.get("title")),
                department=item.get("department"),
                location=item.get("location"),
                url=item.get("url"),
                confidence=float(item.get("confidence") or 0.0),
                source=str(item.get("source")),
                source_url=item.get("source_url"),
            )
            for item in payload.get("open_jobs") or []
        ],
        estimated_budget=payload.get("estimated_budget"),
        priority=payload.get("priority"),
        why_now=str(payload["why_now"]),
        best_outreach_angle=str(payload["best_outreach_angle"]),
        evidence_chain=[
            EvidenceChainItemResponse(
                category=str(item.get("category")),
                summary=str(item.get("summary")),
                source=str(item.get("source")),
                source_url=item.get("source_url"),
                confidence=float(item.get("confidence") or 0.0),
                reference_id=item.get("reference_id"),
            )
            for item in payload.get("evidence_chain") or []
        ],
        source_attribution=[
            SourceAttributionResponse(
                source=str(item.get("source")),
                source_url=item.get("source_url"),
                fields=list(item.get("fields") or []),
                confidence=float(item.get("confidence") or 0.0),
                licensed=bool(item.get("licensed", False)),
                notes=str(item.get("notes") or ""),
            )
            for item in payload.get("source_attribution") or []
        ],
        enrichment_confidence=EnrichmentScoresResponse(
            profile_completeness=float(scores.get("profile_completeness") or 0.0),
            contact_availability=float(scores.get("contact_availability") or 0.0),
            technology_confidence=float(scores.get("technology_confidence") or 0.0),
            decision_maker_confidence=float(scores.get("decision_maker_confidence") or 0.0),
            overall_enrichment_confidence=float(
                scores.get("overall_enrichment_confidence")
                or payload.get("overall_enrichment_confidence")
                or 0.0
            ),
        ),
        enrichment_report_id=UUID(str(report_id)) if report_id else None,
        created_at=created_at,
        processing_latency_ms=float(payload.get("processing_latency_ms") or 0.0),
    )
