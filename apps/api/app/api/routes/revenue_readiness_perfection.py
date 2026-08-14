from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import DatabaseDep
from app.services.revenue_readiness_perfection import RevenueReadinessPerfectionService

router = APIRouter(prefix="/revenue-ready", tags=["revenue-ready"])


def get_rrp(database: DatabaseDep) -> RevenueReadinessPerfectionService:
    return RevenueReadinessPerfectionService(database)


RrpDep = Annotated[RevenueReadinessPerfectionService, Depends(get_rrp)]


class ReviewBody(BaseModel):
    label: str = Field(min_length=1, max_length=64)


@router.get("/dashboard")
async def dashboard(service: RrpDep) -> dict[str, Any]:
    return await service.dashboard()


@router.get("/founder-queue")
async def founder_queue(service: RrpDep) -> dict[str, Any]:
    return await service.founder_queue_v4()


@router.post("/perfect")
async def perfect(service: RrpDep) -> dict[str, Any]:
    return await service.perfect(crawl_dm=True)


@router.post("/company/{company_id}/review")
async def review(company_id: UUID, body: ReviewBody, service: RrpDep) -> dict[str, Any]:
    return await service.submit_review(company_id, body.label)


@router.get("/report")
async def report(service: RrpDep) -> dict[str, Any]:
    dash = await service.dashboard()
    return {
        "vansh_ready_answer": dash.get("vansh_ready_answer"),
        "kpis": dash.get("kpis"),
        "promoted": dash.get("promoted"),
        "still_blocked": dash.get("still_blocked"),
        "blockers": dash.get("blockers"),
    }
