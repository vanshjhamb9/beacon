from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import DatabaseDep, SettingsDep
from app.repositories.copilot import SalesCopilotRepository
from app.schemas.copilot import (
    DraftResponse,
    GenerateResponse,
    GenerationMetaResponse,
    QualityScoresResponse,
    ReviewRequestBody,
    ReviewResponse,
    SalesPackageHistoryItem,
    SalesPackageHistoryResponse,
    SalesPackageResponse,
    SectionResponse,
    StyleVariantResponse,
)
from app.services.copilot import AISalesCopilotService
from sales_copilot.models.types import ReviewAction, ReviewRequest

router = APIRouter(prefix="/copilot", tags=["sales-copilot"])


def get_copilot_service(database: DatabaseDep, settings: SettingsDep) -> AISalesCopilotService:
    return AISalesCopilotService(SalesCopilotRepository(database), settings=settings)


CopilotServiceDep = Annotated[AISalesCopilotService, Depends(get_copilot_service)]


def _bundle_response(bundle: dict) -> SalesPackageResponse:
    package = bundle["package"]
    drafts = bundle.get("drafts") or []
    style_variants_payload = list(package.style_variants or [])
    if not style_variants_payload and drafts:
        grouped: dict[str, list] = {}
        for draft in drafts:
            grouped.setdefault(draft.style, []).append(draft)
        style_variants = [
            StyleVariantResponse(
                style=style,
                drafts=[
                    DraftResponse(
                        id=item.id,
                        kind=item.kind,
                        style=item.style,
                        title=item.title,
                        body=item.body,
                        subject_lines=list(item.subject_lines or []),
                        attribution=dict(item.attribution or {}),
                    )
                    for item in items
                ],
            )
            for style, items in grouped.items()
        ]
    else:
        style_variants = [
            StyleVariantResponse(
                style=variant.get("style") if isinstance(variant, dict) else variant["style"],
                drafts=[
                    DraftResponse(
                        kind=draft.get("kind"),
                        style=draft.get("style"),
                        title=draft.get("title"),
                        body=draft.get("body"),
                        subject_lines=list(draft.get("subject_lines") or []),
                        attribution=dict(draft.get("attribution") or {}),
                    )
                    for draft in (variant.get("drafts") if isinstance(variant, dict) else [])
                ],
            )
            for variant in style_variants_payload
        ]

    quality = dict(package.quality_scores or {})
    return SalesPackageResponse(
        id=package.id,
        company_id=package.company_id,
        opportunity_id=package.opportunity_id,
        company_name=package.company_name,
        opportunity_score=package.opportunity_score,
        recommended_service=package.recommended_service,
        business_pain=package.business_pain,
        version=package.version,
        review_status=package.review_status,
        is_favorite=package.is_favorite,
        sections=[
            SectionResponse(
                key=item.get("key", ""),
                title=item.get("title", ""),
                content=item.get("content", ""),
                attribution=dict(item.get("attribution") or {}),
            )
            for item in (package.sections or [])
        ],
        style_variants=style_variants,
        drafts=[
            DraftResponse(
                id=item.id,
                kind=item.kind,
                style=item.style,
                title=item.title,
                body=item.body,
                subject_lines=list(item.subject_lines or []),
                attribution=dict(item.attribution or {}),
            )
            for item in drafts
        ],
        evidence_chain=list(package.evidence_chain or []),
        quality=QualityScoresResponse(
            personalization=float(quality.get("personalization") or 0.0),
            evidence_coverage=float(quality.get("evidence_coverage") or 0.0),
            readability=float(quality.get("readability") or 0.0),
            professional_tone=float(quality.get("professional_tone") or 0.0),
            length=float(quality.get("length") or 0.0),
            call_to_action=float(quality.get("call_to_action") or 0.0),
            confidence=float(quality.get("confidence") or 0.0),
            overall=float(quality.get("overall") or 0.0),
        ),
        generation=GenerationMetaResponse(
            prompt_version=package.prompt_version,
            llm_provider=package.llm_provider,
            llm_model=package.llm_model,
            temperature=package.temperature,
            prompt_tokens=package.prompt_tokens,
            completion_tokens=package.completion_tokens,
            total_tokens=package.total_tokens,
            latency_ms=package.latency_ms,
            generation_time_ms=package.generation_time_ms,
            cost_estimate_usd=package.cost_estimate_usd,
        ),
        package_payload=dict(package.package_payload or {}),
        created_at=package.created_at,
    )


@router.get("/company/{company_id}", response_model=SalesPackageResponse)
async def get_company_copilot(company_id: UUID, service: CopilotServiceDep) -> SalesPackageResponse:
    bundle = await service.company_package(company_id)
    if bundle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales package not found")
    return _bundle_response(bundle)


@router.get("/opportunity/{opportunity_id}", response_model=SalesPackageResponse)
async def get_opportunity_copilot(opportunity_id: UUID, service: CopilotServiceDep) -> SalesPackageResponse:
    bundle = await service.opportunity_package(opportunity_id)
    if bundle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales package not found")
    return _bundle_response(bundle)


@router.post("/generate/{entity_id}", response_model=GenerateResponse)
async def generate_copilot(entity_id: UUID, service: CopilotServiceDep) -> GenerateResponse:
    result = await service.generate(entity_id)
    package = result.get("package")
    return GenerateResponse(
        generated=bool(result.get("generated")),
        package=_bundle_response(package) if package else None,
    )


@router.post("/regenerate/{entity_id}", response_model=GenerateResponse)
async def regenerate_copilot(entity_id: UUID, service: CopilotServiceDep) -> GenerateResponse:
    result = await service.regenerate(entity_id)
    package = result.get("package")
    return GenerateResponse(
        generated=bool(result.get("generated")),
        package=_bundle_response(package) if package else None,
    )


@router.post("/review/{package_id}", response_model=ReviewResponse)
async def review_copilot(
    package_id: UUID,
    body: ReviewRequestBody,
    service: CopilotServiceDep,
) -> ReviewResponse:
    try:
        action = ReviewAction(body.action)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid review action") from exc
    result = await service.review(
        package_id,
        ReviewRequest(action=action, reviewer=body.reviewer, notes=body.notes, rating=body.rating),
    )
    package = result.get("package")
    return ReviewResponse(
        reviewed=bool(result.get("reviewed") or result.get("generated")),
        package=_bundle_response(package) if package else None,
    )


@router.get("/history/{entity_id}", response_model=SalesPackageHistoryResponse)
async def copilot_history(entity_id: UUID, service: CopilotServiceDep) -> SalesPackageHistoryResponse:
    rows = await service.history(entity_id)
    return SalesPackageHistoryResponse(
        results=[
            SalesPackageHistoryItem(
                id=row.id,
                company_id=row.company_id,
                opportunity_id=row.opportunity_id,
                version=row.version,
                review_status=row.review_status,
                is_favorite=row.is_favorite,
                prompt_version=row.prompt_version,
                llm_provider=row.llm_provider,
                llm_model=row.llm_model,
                quality_overall=float((row.quality_scores or {}).get("overall") or 0.0),
                created_at=row.created_at,
            )
            for row in rows
        ]
    )
