from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep
from app.repositories.campaign import CampaignRepository
from app.schemas.campaign import (
    CampaignActionBody,
    CampaignApprovalResponse,
    CampaignBulkActionBody,
    CampaignDashboardResponse,
    CampaignListResponse,
    CampaignMutationResponse,
    CampaignResponse,
    CampaignScheduleResponse,
    CampaignStepResponse,
)
from app.services.campaign import CampaignService

router = APIRouter(prefix="/campaigns", tags=["campaign-intelligence"])


def get_campaign_service(database: DatabaseDep) -> CampaignService:
    return CampaignService(CampaignRepository(database))


CampaignServiceDep = Annotated[CampaignService, Depends(get_campaign_service)]


def _campaign_response(bundle: dict) -> CampaignResponse:
    campaign = bundle["campaign"]
    return CampaignResponse(
        id=campaign.id,
        company_id=campaign.company_id,
        opportunity_id=campaign.opportunity_id,
        sales_package_id=campaign.sales_package_id,
        company_name=campaign.company_name,
        status=campaign.status,
        priority=campaign.priority,
        primary_channel=campaign.primary_channel,
        secondary_channel=campaign.secondary_channel,
        follow_up_count=campaign.follow_up_count,
        delay_hours_between_messages=[float(x) for x in (campaign.delay_hours_between_messages or [])],
        expected_confidence=campaign.expected_confidence,
        channel_choice_reason=campaign.channel_choice_reason,
        timing_reason=campaign.timing_reason,
        message_selection_reason=campaign.message_selection_reason,
        recommended_service=campaign.recommended_service,
        business_pain=campaign.business_pain,
        buyer_persona=campaign.buyer_persona,
        industry=campaign.industry,
        communication_style=campaign.communication_style,
        timezone=campaign.timezone,
        evidence=list(campaign.evidence or []),
        quality=dict(campaign.quality or {}),
        steps=[
            CampaignStepResponse(
                id=step.id,
                sequence=step.sequence,
                kind=step.kind,
                channel=step.channel,
                delay_hours=step.delay_hours,
                draft_kind=step.draft_kind,
                draft_style=step.draft_style,
                subject_preview=step.subject_preview,
                body_preview=step.body_preview,
                message_selection_reason=step.message_selection_reason,
                timing_reason=step.timing_reason,
                confidence=step.confidence,
                status=step.status,
                evidence=list(step.evidence or []),
            )
            for step in bundle.get("steps") or []
        ],
        schedules=[
            CampaignScheduleResponse(
                id=item.id,
                campaign_id=item.campaign_id,
                campaign_step_id=item.campaign_step_id,
                planned_at=item.planned_at,
                timezone=item.timezone,
                status=item.status,
                timing_reason=item.timing_reason,
            )
            for item in bundle.get("schedules") or []
        ],
        approvals=[
            CampaignApprovalResponse(
                id=item.id,
                action=item.action,
                from_status=item.from_status,
                to_status=item.to_status,
                actor=item.actor,
                notes=item.notes,
                created_at=item.created_at,
            )
            for item in bundle.get("approvals") or []
        ],
        created_at=campaign.created_at,
    )


def _list_item(campaign) -> CampaignResponse:
    return CampaignResponse(
        id=campaign.id,
        company_id=campaign.company_id,
        opportunity_id=campaign.opportunity_id,
        sales_package_id=campaign.sales_package_id,
        company_name=campaign.company_name,
        status=campaign.status,
        priority=campaign.priority,
        primary_channel=campaign.primary_channel,
        secondary_channel=campaign.secondary_channel,
        follow_up_count=campaign.follow_up_count,
        delay_hours_between_messages=[float(x) for x in (campaign.delay_hours_between_messages or [])],
        expected_confidence=campaign.expected_confidence,
        channel_choice_reason=campaign.channel_choice_reason,
        timing_reason=campaign.timing_reason,
        message_selection_reason=campaign.message_selection_reason,
        recommended_service=campaign.recommended_service,
        business_pain=campaign.business_pain,
        buyer_persona=campaign.buyer_persona,
        industry=campaign.industry,
        communication_style=campaign.communication_style,
        timezone=campaign.timezone,
        evidence=list(campaign.evidence or []),
        quality=dict(campaign.quality or {}),
        created_at=campaign.created_at,
    )


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    service: CampaignServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> CampaignListResponse:
    rows = await service.list_campaigns(limit=limit, offset=offset)
    return CampaignListResponse(campaigns=[_list_item(item) for item in rows])


@router.get("/dashboard", response_model=CampaignDashboardResponse)
async def campaign_dashboard(service: CampaignServiceDep) -> CampaignDashboardResponse:
    data = await service.dashboard()
    return CampaignDashboardResponse(**data)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: UUID, service: CampaignServiceDep) -> CampaignResponse:
    bundle = await service.get_campaign(campaign_id)
    if bundle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return _campaign_response(bundle)


@router.post("/create/{company_id}", response_model=CampaignMutationResponse)
async def create_campaign(company_id: UUID, service: CampaignServiceDep) -> CampaignMutationResponse:
    result = await service.create_for_company(company_id)
    package = result.get("campaign")
    return CampaignMutationResponse(
        created=bool(result.get("created")),
        detail=result.get("detail"),
        campaign=_campaign_response(package) if package else None,
    )


@router.post("/approve/{campaign_id}", response_model=CampaignMutationResponse)
async def approve_campaign(
    campaign_id: UUID,
    service: CampaignServiceDep,
    body: CampaignActionBody | None = None,
) -> CampaignMutationResponse:
    payload = body or CampaignActionBody()
    result = await service.approve(campaign_id, actor=payload.actor, notes=payload.notes)
    package = result.get("campaign")
    if not result.get("updated") and result.get("detail") == "Campaign not found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return CampaignMutationResponse(
        updated=bool(result.get("updated")),
        detail=result.get("detail"),
        campaign=_campaign_response(package) if package else None,
    )


@router.post("/reject/{campaign_id}", response_model=CampaignMutationResponse)
async def reject_campaign(
    campaign_id: UUID,
    service: CampaignServiceDep,
    body: CampaignActionBody | None = None,
) -> CampaignMutationResponse:
    payload = body or CampaignActionBody()
    result = await service.reject(campaign_id, actor=payload.actor, notes=payload.notes)
    package = result.get("campaign")
    if not result.get("updated") and result.get("detail") == "Campaign not found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return CampaignMutationResponse(
        updated=bool(result.get("updated")),
        detail=result.get("detail"),
        campaign=_campaign_response(package) if package else None,
    )


@router.post("/bulk-approve")
async def bulk_approve_campaigns(
    service: CampaignServiceDep,
    body: CampaignBulkActionBody,
) -> dict:
    return await service.bulk_approve(body.campaign_ids, actor=body.actor, notes=body.notes)


@router.post("/bulk-reject")
async def bulk_reject_campaigns(
    service: CampaignServiceDep,
    body: CampaignBulkActionBody,
) -> dict:
    return await service.bulk_reject(body.campaign_ids, actor=body.actor, notes=body.notes)


@router.post("/pause/{campaign_id}", response_model=CampaignMutationResponse)
async def pause_campaign(
    campaign_id: UUID,
    service: CampaignServiceDep,
    body: CampaignActionBody | None = None,
) -> CampaignMutationResponse:
    payload = body or CampaignActionBody()
    result = await service.pause(campaign_id, actor=payload.actor, notes=payload.notes)
    package = result.get("campaign")
    if not result.get("updated") and result.get("detail") == "Campaign not found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return CampaignMutationResponse(
        updated=bool(result.get("updated")),
        detail=result.get("detail"),
        campaign=_campaign_response(package) if package else None,
    )


@router.post("/cancel/{campaign_id}", response_model=CampaignMutationResponse)
async def cancel_campaign(
    campaign_id: UUID,
    service: CampaignServiceDep,
    body: CampaignActionBody | None = None,
) -> CampaignMutationResponse:
    payload = body or CampaignActionBody()
    result = await service.cancel(campaign_id, actor=payload.actor, notes=payload.notes)
    package = result.get("campaign")
    if not result.get("updated") and result.get("detail") == "Campaign not found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return CampaignMutationResponse(
        updated=bool(result.get("updated")),
        detail=result.get("detail"),
        campaign=_campaign_response(package) if package else None,
    )
