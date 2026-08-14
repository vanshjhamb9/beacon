from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseDep, RedisDep, SettingsDep
from app.services.production_hardening import ProductionHardeningService

router = APIRouter(prefix="/production-hardening", tags=["production-hardening"])


def get_ph_service(
    database: DatabaseDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> ProductionHardeningService:
    return ProductionHardeningService(database, redis, settings)


PHServiceDep = Annotated[ProductionHardeningService, Depends(get_ph_service)]


@router.get("/company/{company_id}")
async def founder_company_card(company_id: UUID, service: PHServiceDep, persist: bool = False) -> dict:
    card = await service.evaluate_company(company_id, persist=persist)
    if card.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return card


@router.post("/company/{company_id}/evaluate")
async def evaluate_company(company_id: UUID, service: PHServiceDep) -> dict:
    card = await service.evaluate_company(company_id, persist=True)
    if card.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return card


@router.get("/opportunities")
async def opportunities_v2(service: PHServiceDep, limit: int = Query(100, ge=1, le=500)) -> dict:
    return await service.opportunities_v2(limit=limit)


@router.get("/trust")
async def trust_dashboard(service: PHServiceDep) -> dict:
    return await service.trust_dashboard()


@router.get("/duplicates")
async def duplicate_plans(service: PHServiceDep) -> dict:
    return await service.plan_duplicates()


@router.get("/health/signals")
async def live_health_signals(service: PHServiceDep) -> dict:
    signals = await service.live_component_signals()
    return {"component_signals": signals, "scoring_version": "ph1-v1", "hardcoded": False}
