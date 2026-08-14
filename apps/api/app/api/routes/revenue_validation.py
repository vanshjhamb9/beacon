from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import DatabaseDep
from app.services.revenue_validation import RevenueValidationService

router = APIRouter(prefix="/revenue-validation", tags=["revenue-validation"])


def get_clr(database: DatabaseDep) -> RevenueValidationService:
    return RevenueValidationService(database)


ClrDep = Annotated[RevenueValidationService, Depends(get_clr)]


class TransitionBody(BaseModel):
    outcome: str = Field(min_length=1, max_length=64)
    notes: str | None = Field(default=None, max_length=2000)
    actor: str = Field(default="founder", max_length=128)
    revenue_amount: float | None = None


class NoteBody(BaseModel):
    note: str = Field(min_length=1, max_length=4000)


class PredictionBody(BaseModel):
    interested: str = "UNKNOWN"
    decision_maker_correct: str = "UNKNOWN"
    why_now_accurate: str = "UNKNOWN"
    service_accepted: str = "UNKNOWN"
    confidence_realistic: str = "UNKNOWN"
    notes: str | None = None


@router.post("/sync")
async def sync(service: ClrDep, seed_contacted: bool = False) -> dict[str, Any]:
    return await service.sync_from_ofc(seed_contacted=seed_contacted)


@router.get("/dashboard")
async def dashboard(service: ClrDep) -> dict[str, Any]:
    return await service.dashboard()


@router.get("/daily-brief")
async def daily_brief(service: ClrDep) -> dict[str, Any]:
    return await service.daily_brief()


@router.get("/executive")
async def executive(service: ClrDep) -> dict[str, Any]:
    return await service.executive()


@router.get("/company/{company_id}")
async def company(company_id: UUID, service: ClrDep) -> dict[str, Any]:
    return await service.company_detail(company_id)


@router.get("/outcomes")
async def outcomes(service: ClrDep) -> dict[str, Any]:
    return await service.list_outcomes()


@router.post("/company/{company_id}/transition")
async def transition(company_id: UUID, body: TransitionBody, service: ClrDep) -> dict[str, Any]:
    return await service.transition(
        company_id,
        body.outcome,
        notes=body.notes,
        actor=body.actor,
        revenue_amount=body.revenue_amount,
    )


@router.post("/company/{company_id}/notes")
async def notes(company_id: UUID, body: NoteBody, service: ClrDep) -> dict[str, Any]:
    return await service.add_notes(company_id, body.note)


@router.post("/company/{company_id}/prediction")
async def prediction(company_id: UUID, body: PredictionBody, service: ClrDep) -> dict[str, Any]:
    return await service.validate_prediction(company_id, body.model_dump())


@router.get("/weekly-review")
async def weekly_review(service: ClrDep) -> dict[str, Any]:
    return await service.weekly_review()


@router.get("/production-readiness")
async def production_readiness(service: ClrDep) -> dict[str, Any]:
    return await service.production_readiness()


@router.get("/report")
async def report(service: ClrDep) -> dict[str, Any]:
    return await service.build_report()
