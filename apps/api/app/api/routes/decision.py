from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep, SettingsDep
from app.repositories.decision import DecisionDiscoveryRepository
from app.schemas.decision import (
    ConfidenceResponse,
    ContactChannelResponse,
    DecisionDiscoveryResponse,
    DecisionMakerEntryResponse,
    DecisionRefreshResponse,
    DecisionSearchResponse,
    DepartmentResponse,
    LeadershipResponse,
    PublicProfileResponse,
)
from app.services.decision import DecisionMakerDiscoveryService

router = APIRouter(prefix="/decision", tags=["decision-discovery"])


def get_decision_service(database: DatabaseDep, settings: SettingsDep) -> DecisionMakerDiscoveryService:
    return DecisionMakerDiscoveryService(DecisionDiscoveryRepository(database), settings=settings)


DecisionServiceDep = Annotated[DecisionMakerDiscoveryService, Depends(get_decision_service)]


def _maker_response(item) -> DecisionMakerEntryResponse:
    return DecisionMakerEntryResponse(
        id=item.id,
        name=item.name,
        role=item.role,
        normalized_role=item.normalized_role,
        department=item.department,
        work_email=item.work_email,
        business_phone=item.business_phone,
        linkedin_url=item.linkedin_url,
        is_primary=item.is_primary,
        is_secondary=item.is_secondary,
        buyer_match_score=item.buyer_match_score,
        confidence=item.confidence,
        source=item.source,
        source_url=item.source_url,
        evidence=item.evidence,
    )


def _bundle_response(bundle: dict) -> DecisionDiscoveryResponse:
    report = bundle["report"]
    makers = bundle["decision_makers"]
    primary = next((item for item in makers if item.is_primary), None)
    secondary = next((item for item in makers if item.is_secondary), None)
    channels = bundle["contact_channels"]
    confidence = bundle["confidence"]
    return DecisionDiscoveryResponse(
        id=report.id,
        company_id=report.company_id,
        opportunity_id=report.opportunity_id,
        company_name=report.company_name,
        opportunity_score=report.opportunity_score,
        business_pain=report.business_pain,
        recommended_service=report.recommended_service,
        primary_decision_maker=_maker_response(primary) if primary else None,
        secondary_decision_maker=_maker_response(secondary) if secondary else None,
        decision_makers=[_maker_response(item) for item in makers],
        departments=[
            DepartmentResponse(
                name=item.name,
                signal_strength=item.signal_strength,
                headcount_signal=item.headcount_signal,
                source=item.source,
                source_url=item.source_url,
                evidence=item.evidence,
            )
            for item in bundle["departments"]
        ],
        leadership=[
            LeadershipResponse(
                name=item.name,
                title=item.title,
                department=item.department,
                confidence=item.confidence,
                source=item.source,
                source_url=item.source_url,
                evidence=item.evidence,
            )
            for item in bundle["leadership"]
        ],
        contact_channels=[
            ContactChannelResponse(
                kind=item.kind,
                value=item.value,
                label=item.label,
                rank=item.rank,
                confidence=item.confidence,
                source=item.source,
                source_url=item.source_url,
                is_verified_public=item.is_verified_public,
                evidence=item.evidence,
            )
            for item in channels
        ],
        public_emails=sorted({item.value.lower() for item in channels if "@" in item.value}),
        public_phones=sorted({item.value for item in channels if item.kind == "business_phone"}),
        public_profiles=[
            PublicProfileResponse(
                platform=item.platform,
                url=item.url,
                handle=item.handle,
                confidence=item.confidence,
                source=item.source,
            )
            for item in bundle["public_profiles"]
        ],
        best_outreach_sequence=list(report.best_outreach_sequence or []),
        no_public_contact_message=report.no_public_contact_message,
        buyer_match_confidence=report.buyer_match_confidence,
        reason=report.reason,
        evidence_chain=list(report.evidence_chain or []),
        source_attribution=list(report.source_attribution or []),
        confidence=ConfidenceResponse(
            leadership_confidence=confidence.leadership_confidence if confidence else 0.0,
            department_confidence=confidence.department_confidence if confidence else 0.0,
            contact_confidence=confidence.contact_confidence if confidence else 0.0,
            buyer_match_confidence=confidence.buyer_match_confidence if confidence else 0.0,
            overall_discovery_score=confidence.overall_discovery_score if confidence else report.overall_discovery_score,
        ),
        created_at=report.created_at,
    )


@router.get("/company/{company_id}", response_model=DecisionDiscoveryResponse)
async def get_company_decision(company_id: UUID, service: DecisionServiceDep) -> DecisionDiscoveryResponse:
    bundle = await service.company_report(company_id)
    if bundle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision discovery report not found")
    return _bundle_response(bundle)


@router.get("/opportunity/{opportunity_id}", response_model=DecisionDiscoveryResponse)
async def get_opportunity_decision(opportunity_id: UUID, service: DecisionServiceDep) -> DecisionDiscoveryResponse:
    bundle = await service.opportunity_report(opportunity_id)
    if bundle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision discovery report not found")
    return _bundle_response(bundle)


@router.post("/refresh/{entity_id}", response_model=DecisionRefreshResponse)
async def refresh_decision(entity_id: UUID, service: DecisionServiceDep) -> DecisionRefreshResponse:
    result = await service.refresh(entity_id)
    report = result.get("report")
    return DecisionRefreshResponse(
        refreshed=bool(result.get("refreshed")),
        report=_bundle_response(report) if report else None,
    )


@router.get("/search", response_model=DecisionSearchResponse)
async def search_decision_makers(
    service: DecisionServiceDep,
    q: str | None = Query(default=None),
    role: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> DecisionSearchResponse:
    rows = await service.search(query=q, role=role, limit=limit, offset=offset)
    return DecisionSearchResponse(results=[_maker_response(item) for item in rows])
