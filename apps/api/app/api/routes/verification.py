from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import DatabaseDep
from app.repositories.enrichment import EnrichmentRepository
from app.repositories.verification import VerificationRepository
from app.schemas.verification import (
    CompletenessScoresResponse,
    ConnectorStatisticResponse,
    CoverageBreakdownResponse,
    FieldVerificationResponse,
    LeadReadinessChecklistResponse,
    VerificationCompanyResponse,
    VerificationConnectorsResponse,
    VerificationDashboardResponse,
    VerificationRefreshResponse,
)
from app.services.enrichment import LeadEnrichmentService
from app.services.verification import DataVerificationService

router = APIRouter(prefix="/verification", tags=["verification"])


def get_verification_service(database: DatabaseDep) -> DataVerificationService:
    enrichment_service = LeadEnrichmentService(EnrichmentRepository(database))
    return DataVerificationService(
        VerificationRepository(database),
        enrichment_service=enrichment_service,
    )


VerificationServiceDep = Annotated[DataVerificationService, Depends(get_verification_service)]


@router.get("/company/{company_id}", response_model=VerificationCompanyResponse)
async def get_company_verification(
    company_id: UUID,
    service: VerificationServiceDep,
) -> VerificationCompanyResponse:
    payload = await service.company_verification(company_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Verification report not found for company.")
    return _company_response(payload)


@router.get("/dashboard", response_model=VerificationDashboardResponse)
async def get_verification_dashboard(service: VerificationServiceDep) -> VerificationDashboardResponse:
    metrics = await service.dashboard()
    return VerificationDashboardResponse(
        overall_data_quality=metrics.overall_data_quality,
        coverage_percent=metrics.coverage_percent,
        verification_percent=metrics.verification_percent,
        freshness_percent=metrics.freshness_percent,
        average_profile_completeness=metrics.average_profile_completeness,
        connector_leaderboard=[
            ConnectorStatisticResponse(**item.model_dump()) for item in metrics.connector_leaderboard
        ],
        missing_field_distribution=metrics.missing_field_distribution,
        top_missing_fields=metrics.top_missing_fields,
        profiles_needing_refresh=metrics.profiles_needing_refresh,
        flagged_for_review=metrics.flagged_for_review,
        total_verified_profiles=metrics.total_verified_profiles,
    )


@router.get("/connectors", response_model=VerificationConnectorsResponse)
async def get_verification_connectors(service: VerificationServiceDep) -> VerificationConnectorsResponse:
    connectors = await service.connectors()
    return VerificationConnectorsResponse(
        connectors=[ConnectorStatisticResponse(**item.model_dump()) for item in connectors]
    )


@router.get("/profile/{verification_report_id}", response_model=VerificationCompanyResponse)
async def get_verification_profile(
    verification_report_id: UUID,
    service: VerificationServiceDep,
) -> VerificationCompanyResponse:
    payload = await service.profile_verification(verification_report_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Verification profile not found.")
    return _company_response(payload)


@router.post("/refresh/{entity_id}", response_model=VerificationRefreshResponse)
async def refresh_verification(
    entity_id: UUID,
    service: VerificationServiceDep,
) -> VerificationRefreshResponse:
    payload = await service.refresh(entity_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Unable to refresh verification for the given id.")
    return VerificationRefreshResponse(refreshed=True, profile=_company_response(payload))


def _company_response(payload: dict[str, Any]) -> VerificationCompanyResponse:
    completeness = payload.get("completeness") or {}
    checklist = payload.get("readiness_checklist") or {}
    report_id = payload.get("verification_report_id")
    return VerificationCompanyResponse(
        company_id=UUID(str(payload["company_id"])),
        opportunity_id=UUID(str(payload["opportunity_id"])),
        enrichment_report_id=UUID(str(payload["enrichment_report_id"])),
        company_name=str(payload["company_name"]),
        completeness=CompletenessScoresResponse(
            overall_completeness=float(completeness.get("overall_completeness") or 0.0),
            company_profile_completeness=float(completeness.get("company_profile_completeness") or 0.0),
            contact_completeness=float(completeness.get("contact_completeness") or 0.0),
            leadership_completeness=float(completeness.get("leadership_completeness") or 0.0),
            technology_completeness=float(completeness.get("technology_completeness") or 0.0),
            revenue_completeness=float(completeness.get("revenue_completeness") or 0.0),
            hiring_completeness=float(completeness.get("hiring_completeness") or 0.0),
            social_profile_completeness=float(completeness.get("social_profile_completeness") or 0.0),
            evidence_completeness=float(completeness.get("evidence_completeness") or 0.0),
            timeline_completeness=float(completeness.get("timeline_completeness") or 0.0),
        ),
        coverage=[
            CoverageBreakdownResponse(
                category=str(item.get("category")),
                present_fields=int(item.get("present_fields") or 0),
                expected_fields=int(item.get("expected_fields") or 0),
                score=float(item.get("score") or 0.0),
                missing_fields=list(item.get("missing_fields") or []),
            )
            for item in payload.get("coverage") or []
        ],
        field_verifications=[
            FieldVerificationResponse(
                field_name=str(item.get("field_name")),
                value=item.get("value"),
                source=str(item.get("source")),
                source_url=item.get("source_url"),
                connector=str(item.get("connector")),
                verified_at=item.get("verified_at"),
                confidence=float(item.get("confidence") or 0.0),
                freshness_score=float(item.get("freshness_score") or 0.0),
                freshness_status=str(item.get("freshness_status")),
                trust_score=float(item.get("trust_score") or 0.0),
                verification_status=str(item.get("verification_status")),
                confirmed_by=list(item.get("confirmed_by") or []),
                conflicting_sources=list(item.get("conflicting_sources") or []),
                is_canonical=bool(item.get("is_canonical", False)),
                conflict_explanation=item.get("conflict_explanation"),
                category=str(item.get("category") or "general"),
            )
            for item in payload.get("field_verifications") or []
            if item.get("is_canonical", True)
        ],
        freshness_score=float(payload.get("freshness_score") or 0.0),
        freshness_status=str(payload.get("freshness_status")),
        trust_score=float(payload.get("trust_score") or 0.0),
        verification_percent=float(payload.get("verification_percent") or 0.0),
        coverage_percent=float(payload.get("coverage_percent") or 0.0),
        overall_data_quality=float(payload.get("overall_data_quality") or 0.0),
        overall_readiness=float(payload.get("overall_readiness") or 0.0),
        readiness_checklist=LeadReadinessChecklistResponse(
            company_profile=bool(checklist.get("company_profile")),
            technology=bool(checklist.get("technology")),
            leadership=bool(checklist.get("leadership")),
            public_business_email=bool(checklist.get("public_business_email")),
            public_phone=bool(checklist.get("public_phone")),
            hiring=bool(checklist.get("hiring")),
            funding=bool(checklist.get("funding")),
            timeline=bool(checklist.get("timeline")),
        ),
        decision=str(payload.get("decision")),
        automatic_actions=[str(item) for item in payload.get("automatic_actions") or []],
        reason_codes=[str(item) for item in payload.get("reason_codes") or []],
        missing_fields=[str(item) for item in payload.get("missing_fields") or []],
        connector_statistics=[
            ConnectorStatisticResponse(
                connector=str(item.get("connector")),
                success_rate=float(item.get("success_rate") or 0.0),
                average_latency_ms=float(item.get("average_latency_ms") or 0.0),
                failure_rate=float(item.get("failure_rate") or 0.0),
                coverage=float(item.get("coverage") or 0.0),
                fields_returned=int(item.get("fields_returned") or 0),
                average_confidence=float(item.get("average_confidence") or 0.0),
                companies_enriched=int(item.get("companies_enriched") or 0),
            )
            for item in payload.get("connector_statistics") or []
        ],
        verification_report_id=UUID(str(report_id)) if report_id else None,
        created_at=payload.get("created_at"),
        processing_latency_ms=float(payload.get("processing_latency_ms") or 0.0),
    )
