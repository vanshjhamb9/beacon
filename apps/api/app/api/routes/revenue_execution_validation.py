from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseDep
from app.services.revenue_execution_validation import RevenueExecutionValidationService

router = APIRouter(prefix="/revenue-execution-validation", tags=["revenue-execution-validation"])


def get_rev_service(database: DatabaseDep) -> RevenueExecutionValidationService:
    return RevenueExecutionValidationService(database)


RevServiceDep = Annotated[RevenueExecutionValidationService, Depends(get_rev_service)]


@router.get("/dashboard")
async def dashboard(service: RevServiceDep) -> dict[str, Any]:
    return await service.dashboard()


@router.get("/funnel")
async def funnel(service: RevServiceDep) -> dict[str, Any]:
    return await service.reality_funnel()


@router.get("/rejections")
async def rejections(service: RevServiceDep) -> dict[str, Any]:
    return await service.rejections()


@router.get("/connectors")
async def connectors(service: RevServiceDep) -> dict[str, Any]:
    return await service.connector_scoreboard()


@router.get("/founder-queue")
async def founder_queue(service: RevServiceDep) -> dict[str, Any]:
    return await service.founder_queue_v3()


@router.get("/qa/pending")
async def qa_pending(service: RevServiceDep) -> dict[str, Any]:
    return await service.qa_pending()


@router.post("/qa")
async def qa_submit(payload: dict[str, Any], service: RevServiceDep) -> dict[str, Any]:
    return await service.qa_submit(
        company_id=payload.get("company_id"),
        company_name=payload.get("company_name"),
        rating=str(payload.get("rating") or "Average"),
        reviewer=str(payload.get("reviewer") or "founder"),
        notes=payload.get("notes"),
    )


@router.get("/qa/analytics")
async def qa_analytics(service: RevServiceDep) -> dict[str, Any]:
    return await service.qa_analytics()


@router.get("/daily-report")
async def daily_report(service: RevServiceDep) -> dict[str, Any]:
    return await service.daily_report()


@router.get("/acceptance")
async def acceptance(service: RevServiceDep) -> dict[str, Any]:
    return await service.acceptance()


@router.post("/evaluate")
async def evaluate(payload: dict[str, Any], service: RevServiceDep) -> dict[str, Any]:
    return service.evaluate(payload)


@router.post("/rebuild")
async def rebuild(service: RevServiceDep, limit: int = Query(default=500, ge=1, le=5000)) -> dict[str, Any]:
    return await service.rebuild(persist=True, limit=limit)
