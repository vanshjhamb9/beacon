from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import DatabaseDep
from app.services.operation_first_customer import OperationFirstCustomerService

router = APIRouter(prefix="/first-customer", tags=["first-customer"])


def get_ofc(database: DatabaseDep) -> OperationFirstCustomerService:
    return OperationFirstCustomerService(database)


OfcDep = Annotated[OperationFirstCustomerService, Depends(get_ofc)]


class TransitionBody(BaseModel):
    status: str = Field(min_length=1, max_length=32)
    note: str | None = Field(default=None, max_length=500)


class TimelineBody(BaseModel):
    event_type: str = Field(min_length=1, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)


class NoteBody(BaseModel):
    note: str = Field(min_length=1, max_length=4000)


class ObjectionBody(BaseModel):
    label: str = Field(min_length=1, max_length=64)


@router.post("/sync")
async def sync(service: OfcDep) -> dict[str, Any]:
    return await service.sync_from_revenue_ready()


@router.get("/workspace")
async def workspace(service: OfcDep) -> dict[str, Any]:
    return await service.list_records()


@router.get("/records/{record_id}")
async def get_record(record_id: UUID, service: OfcDep) -> dict[str, Any]:
    return await service.get_record(record_id)


@router.post("/records/{record_id}/transition")
async def transition(record_id: UUID, body: TransitionBody, service: OfcDep) -> dict[str, Any]:
    return await service.transition(record_id, body.status, note=body.note)


@router.post("/records/{record_id}/timeline")
async def timeline(record_id: UUID, body: TimelineBody, service: OfcDep) -> dict[str, Any]:
    return await service.add_timeline(record_id, body.event_type, payload=body.payload)


@router.post("/records/{record_id}/notes")
async def notes(record_id: UUID, body: NoteBody, service: OfcDep) -> dict[str, Any]:
    return await service.add_note(record_id, body.note)


@router.post("/records/{record_id}/objections")
async def objections(record_id: UUID, body: ObjectionBody, service: OfcDep) -> dict[str, Any]:
    return await service.add_objection(record_id, body.label)


@router.get("/revenue-dashboard")
async def revenue_dashboard(service: OfcDep) -> dict[str, Any]:
    return await service.revenue_dashboard()


@router.get("/learning")
async def learning(service: OfcDep) -> dict[str, Any]:
    return await service.learning_dashboard()


@router.get("/today")
async def today(service: OfcDep) -> dict[str, Any]:
    records = await service.list_records()
    return {
        "question": "What should Vansh do today to close the next customer?",
        "today_action": records.get("today_action"),
        "count": records.get("count"),
    }


@router.get("/report")
async def report(service: OfcDep) -> dict[str, Any]:
    return await service.build_report()
