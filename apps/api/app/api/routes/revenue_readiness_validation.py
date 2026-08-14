from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import DatabaseDep, SettingsDep
from app.services.revenue_readiness_validation import RevenueReadinessValidationService

router = APIRouter(prefix="/revenue-readiness", tags=["revenue-readiness-validation"])


def get_m1_service(database: DatabaseDep, settings: SettingsDep) -> RevenueReadinessValidationService:
    return RevenueReadinessValidationService(database, settings)


M1ServiceDep = Annotated[RevenueReadinessValidationService, Depends(get_m1_service)]


@router.get("/report")
async def m1_full_report(service: M1ServiceDep) -> dict:
    return await service.full_report()


@router.get("/collection")
async def m1_collection(service: M1ServiceDep) -> dict:
    phase = await service.phase_collection()
    return phase.model_dump(mode="json")


@router.get("/sales-readiness-audit")
async def m1_sre_audit(service: M1ServiceDep) -> dict:
    phase = await service.phase_sales_readiness_audit()
    return phase.model_dump(mode="json")


@router.get("/success-metrics")
async def m1_success_metrics(service: M1ServiceDep) -> dict:
    report = await service.full_report()
    return {
        "success_metrics": report["success_metrics"],
        "estimated_qualified_per_100": report["estimated_qualified_per_100"],
        "overall_status": report["overall_status"],
        "production_allowed": report["production_allowed"],
        "recommendations": report["recommendations"],
        "scoring_version": report["scoring_version"],
    }
