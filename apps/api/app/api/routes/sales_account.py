from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.api.dependencies import DatabaseDep, SettingsDep
from app.repositories.ecommerce_leads import EcommerceLeadRepository
from app.repositories.sales_account import SalesAccountRepository
from app.schemas.sales_account import (
    SalesAccountListResponse,
    SalesAccountRefreshResponse,
    SalesAccountResponse,
    SalesAccountRefreshRequest,
    SalesDashboardResponse,
)
from app.services.sales_account import SalesAccountService

router = APIRouter(prefix="/accounts", tags=["sales-accounts"])


def get_account_service(
    database: DatabaseDep, settings: SettingsDep
) -> SalesAccountService:
    return SalesAccountService(
        SalesAccountRepository(database),
        EcommerceLeadRepository(database),
        settings=settings,
    )


AccountServiceDep = Annotated[SalesAccountService, Depends(get_account_service)]


@router.get("", response_model=SalesAccountListResponse)
async def list_accounts(
    service: AccountServiceDep,
    status: str | None = Query(None),
    platform: str | None = Query(None),
    category: str | None = Query(None),
    score: float | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> SalesAccountListResponse:
    result = await service.list_accounts(
        status=status, platform=platform, category=category,
        min_score=score, limit=limit, offset=offset,
    )
    return SalesAccountListResponse(
        accounts=[SalesAccountResponse.model_validate(a) for a in result["accounts"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/dashboard", response_model=SalesDashboardResponse)
async def get_dashboard(service: AccountServiceDep) -> SalesDashboardResponse:
    stats = await service.get_dashboard()
    return SalesDashboardResponse(**stats)


@router.get("/export")
async def export_accounts(
    service: AccountServiceDep,
    status: str | None = Query(None),
) -> Response:
    excel_bytes = await service.export_accounts(status=status)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=sales_ready_accounts.xlsx"},
    )


@router.get("/{account_id}", response_model=SalesAccountResponse)
async def get_account(
    account_id: UUID, service: AccountServiceDep
) -> SalesAccountResponse:
    account = await service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return SalesAccountResponse.model_validate(account)


@router.get("/{account_id}/contacts")
async def get_account_contacts(
    account_id: UUID, service: AccountServiceDep
) -> dict:
    result = await service.get_account_contacts(account_id)
    if not result:
        raise HTTPException(status_code=404, detail="Account not found")
    return result


@router.get("/{account_id}/committee")
async def get_account_committee(
    account_id: UUID, service: AccountServiceDep
) -> dict:
    result = await service.get_account_committee(account_id)
    if not result:
        raise HTTPException(status_code=404, detail="Account not found")
    return result


@router.get("/{account_id}/health")
async def get_account_health(
    account_id: UUID, service: AccountServiceDep
) -> dict:
    result = await service.get_account_health(account_id)
    if not result:
        raise HTTPException(status_code=404, detail="Account not found")
    return result


@router.get("/{account_id}/evidence")
async def get_account_evidence(
    account_id: UUID, service: AccountServiceDep
) -> dict:
    result = await service.get_account_evidence(account_id)
    if not result:
        raise HTTPException(status_code=404, detail="Account not found")
    return result


@router.post("/{account_id}/refresh")
async def refresh_account(
    account_id: UUID, service: AccountServiceDep
) -> SalesAccountRefreshResponse:
    result = await service.refresh_account(str(account_id))
    return SalesAccountRefreshResponse(
        status=result["status"],
        processed=1,
        message=result.get("message", f"Account refreshed: {result.get('status_label', '')}"),
    )


@router.post("/bulk-refresh", response_model=SalesAccountRefreshResponse)
async def bulk_refresh(
    request: SalesAccountRefreshRequest,
    service: AccountServiceDep,
) -> SalesAccountRefreshResponse:
    result = await service.bulk_refresh(limit=500)
    return SalesAccountRefreshResponse(
        status=result["status"],
        processed=result["processed"],
        message=f"Refreshed {result['processed']} of {result['total_leads']} leads",
    )
