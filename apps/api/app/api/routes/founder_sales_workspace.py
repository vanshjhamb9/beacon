"""Founder Sales Workspace (FSW) API routes — Sprint 38."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import DatabaseDep
from app.repositories.founder_sales_workspace import FSWRepository
from app.schemas.founder_sales_workspace import (
    ActionResponse,
    AssignRequest,
    BulkDeleteRequest,
    BulkMoveRequest,
    FilterValuesResponse,
    GarbageRequest,
    LeadStageCreateRequest,
    LeadStageListResponse,
    LeadStageResponse,
    LeadStageUpdateRequest,
    ManualStatusRequest,
    MoveLeadRequest,
    NoteCreateRequest,
    NoteResponse,
    SnoozeRequest,
    StageCountsResponse,
    TaskCreateRequest,
    TaskResponse,
    TimelineResponse,
)
from app.services.founder_sales_workspace import FSWService

router = APIRouter(prefix="/fsw", tags=["Founder Sales Workspace"])


def get_service(database: DatabaseDep) -> FSWService:
    return FSWService(FSWRepository(database))


FSWServiceDep = Annotated[FSWService, Depends(get_service)]


# ── Lead Stages ──


@router.get("/leads", response_model=LeadStageListResponse)
async def list_leads(
    service: FSWServiceDep,
    stage: str | None = None,
    owner: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    service_match: str | None = None,
    connector: str | None = None,
    trigger: str | None = None,
    manual_status: str | None = None,
    score_min: float | None = None,
    score_max: float | None = None,
    age_days: int | None = None,
    search: str | None = None,
    include_garbage: bool = False,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> LeadStageListResponse:
    leads = await service.list_leads(
        stage=stage,
        owner=owner,
        industry=industry,
        country=country,
        service=service_match,
        connector=connector,
        trigger=trigger,
        manual_status=manual_status,
        score_min=score_min,
        score_max=score_max,
        age_days_max=age_days,
        search=search,
        include_garbage=include_garbage,
        limit=limit,
        offset=offset,
    )
    counts = await service.get_stage_counts()
    total = sum(counts.values())
    return LeadStageListResponse(
        items=[LeadStageResponse.model_validate(lead, from_attributes=True) for lead in leads],
        total=total,
        stage_counts=counts,
    )


@router.get("/leads/{lead_id}", response_model=LeadStageResponse)
async def get_lead(service: FSWServiceDep, lead_id: UUID) -> LeadStageResponse:
    lead = await service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadStageResponse.model_validate(lead, from_attributes=True)


@router.post("/leads", response_model=LeadStageResponse, status_code=201)
async def create_lead(service: FSWServiceDep, data: LeadStageCreateRequest) -> LeadStageResponse:
    lead = await service.create_lead(data.model_dump())
    return LeadStageResponse.model_validate(lead, from_attributes=True)


@router.patch("/leads/{lead_id}", response_model=LeadStageResponse)
async def update_lead(service: FSWServiceDep, lead_id: UUID, data: LeadStageUpdateRequest) -> LeadStageResponse:
    lead = await service.update_lead(lead_id, data.model_dump(exclude_unset=True))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadStageResponse.model_validate(lead, from_attributes=True)


@router.post("/leads/{lead_id}/move", response_model=LeadStageResponse)
async def move_lead(service: FSWServiceDep, lead_id: UUID, data: MoveLeadRequest) -> LeadStageResponse:
    lead = await service.move_lead(lead_id, data.stage, data.sort_order)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadStageResponse.model_validate(lead, from_attributes=True)


@router.post("/leads/{lead_id}/garbage", response_model=LeadStageResponse)
async def send_to_garbage(service: FSWServiceDep, lead_id: UUID, data: GarbageRequest) -> LeadStageResponse:
    lead = await service.send_to_garbage(lead_id, data.reason, data.note)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadStageResponse.model_validate(lead, from_attributes=True)


@router.post("/leads/{lead_id}/restore", response_model=LeadStageResponse)
async def restore_from_garbage(service: FSWServiceDep, lead_id: UUID) -> LeadStageResponse:
    lead = await service.restore_from_garbage(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found or not in garbage")
    return LeadStageResponse.model_validate(lead, from_attributes=True)


@router.post("/leads/{lead_id}/archive", response_model=LeadStageResponse)
async def archive_lead(service: FSWServiceDep, lead_id: UUID) -> LeadStageResponse:
    lead = await service.archive_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadStageResponse.model_validate(lead, from_attributes=True)


@router.post("/leads/{lead_id}/snooze", response_model=LeadStageResponse)
async def snooze_lead(service: FSWServiceDep, lead_id: UUID, data: SnoozeRequest) -> LeadStageResponse:
    lead = await service.snooze_lead(lead_id, data.until, data.reason)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadStageResponse.model_validate(lead, from_attributes=True)


@router.post("/leads/{lead_id}/status", response_model=LeadStageResponse)
async def set_manual_status(service: FSWServiceDep, lead_id: UUID, data: ManualStatusRequest) -> LeadStageResponse:
    lead = await service.set_manual_status(lead_id, data.status)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadStageResponse.model_validate(lead, from_attributes=True)


@router.post("/leads/{lead_id}/assign", response_model=LeadStageResponse)
async def assign_lead(service: FSWServiceDep, lead_id: UUID, data: AssignRequest) -> LeadStageResponse:
    lead = await service.assign_lead(lead_id, data.owner)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadStageResponse.model_validate(lead, from_attributes=True)


# ── Bulk Operations ──


@router.post("/bulk/move")
async def bulk_move(service: FSWServiceDep, data: BulkMoveRequest) -> dict:
    count = await service.bulk_move(data.lead_ids, data.stage)
    return {"moved": count}


@router.post("/bulk/delete")
async def bulk_delete(service: FSWServiceDep, data: BulkDeleteRequest) -> dict:
    count = await service.bulk_delete(data.lead_ids)
    return {"deleted": count}


# ── Notes ──


@router.get("/leads/{lead_id}/notes", response_model=list[NoteResponse])
async def list_notes(service: FSWServiceDep, lead_id: UUID) -> list[NoteResponse]:
    notes = await service.list_notes(lead_id)
    return [NoteResponse.model_validate(n, from_attributes=True) for n in notes]


@router.post("/leads/{lead_id}/notes", response_model=NoteResponse, status_code=201)
async def add_note(service: FSWServiceDep, lead_id: UUID, data: NoteCreateRequest) -> NoteResponse:
    note = await service.add_note(lead_id, data.content, data.author)
    return NoteResponse.model_validate(note, from_attributes=True)


@router.delete("/notes/{note_id}")
async def delete_note(service: FSWServiceDep, note_id: UUID) -> dict:
    ok = await service.delete_note(note_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"deleted": True}


# ── Tasks ──


@router.get("/leads/{lead_id}/tasks", response_model=list[TaskResponse])
async def list_tasks(
    service: FSWServiceDep,
    lead_id: UUID,
    include_completed: bool = True,
) -> list[TaskResponse]:
    tasks = await service.list_tasks(lead_id, include_completed=include_completed)
    return [TaskResponse.model_validate(t, from_attributes=True) for t in tasks]


@router.post("/leads/{lead_id}/tasks", response_model=TaskResponse, status_code=201)
async def add_task(service: FSWServiceDep, lead_id: UUID, data: TaskCreateRequest) -> TaskResponse:
    task = await service.add_task(lead_id, data.title, data.description, data.due_date, data.priority, data.owner)
    return TaskResponse.model_validate(task, from_attributes=True)


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(service: FSWServiceDep, task_id: UUID) -> TaskResponse:
    task = await service.complete_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate(task, from_attributes=True)


@router.delete("/tasks/{task_id}")
async def delete_task(service: FSWServiceDep, task_id: UUID) -> dict:
    ok = await service.delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": True}


# ── Timeline ──


@router.get("/leads/{lead_id}/timeline", response_model=list[TimelineResponse])
async def list_timeline(service: FSWServiceDep, lead_id: UUID) -> list[TimelineResponse]:
    events = await service.list_timeline(lead_id)
    return [TimelineResponse.model_validate(e, from_attributes=True) for e in events]


# ── Stats & Filters ──


@router.get("/stage-counts", response_model=StageCountsResponse)
async def stage_counts(service: FSWServiceDep) -> StageCountsResponse:
    counts = await service.get_stage_counts()
    return StageCountsResponse(counts=counts, total=sum(counts.values()))


@router.get("/filter-values", response_model=FilterValuesResponse)
async def filter_values(service: FSWServiceDep) -> FilterValuesResponse:
    vals = await service.get_filter_values()
    return FilterValuesResponse(**vals)
