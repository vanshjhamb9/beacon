"""Founder Sales Workspace (FSW) schemas — Sprint 38."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ── Lead Stage ──

class LeadStageResponse(BaseModel):
    id: UUID
    company_id: UUID | None = None
    opportunity_id: UUID | None = None
    target_account_id: UUID | None = None
    stage: str
    manual_status: str | None = None
    owner: str | None = None
    assigned_by: str | None = None
    revenue_opportunity_score: float = 0
    fit_score: float = 0
    intent_score: float = 0
    company_name: str
    industry: str | None = None
    country: str | None = None
    service_match: str | None = None
    source_connector: str | None = None
    trigger: str | None = None
    why_now: str | None = None
    buying_signals: list[Any] = []
    garbage_reason: str | None = None
    garbage_note: str | None = None
    garbage_at: datetime | None = None
    snoozed_until: datetime | None = None
    snooze_reason: str | None = None
    archived_at: datetime | None = None
    sort_order: int = 0
    tags: list[Any] = []
    created_at: datetime
    updated_at: datetime

    @field_validator("buying_signals", mode="before")
    @classmethod
    def parse_buying_signals(cls, v: Any) -> list[Any]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            return [v] if v else []
        return v if isinstance(v, list) else []


class LeadStageListResponse(BaseModel):
    items: list[LeadStageResponse]
    total: int
    stage_counts: dict[str, int]


class LeadStageCreateRequest(BaseModel):
    company_id: UUID | None = None
    opportunity_id: UUID | None = None
    target_account_id: UUID | None = None
    stage: str = "revenue_ready"
    owner: str | None = None
    revenue_opportunity_score: float = 0
    fit_score: float = 0
    intent_score: float = 0
    company_name: str = Field(min_length=1, max_length=255)
    industry: str | None = None
    country: str | None = None
    service_match: str | None = None
    source_connector: str | None = None
    trigger: str | None = None
    why_now: str | None = None
    buying_signals: list[Any] = []
    tags: list[Any] = []


class LeadStageUpdateRequest(BaseModel):
    stage: str | None = None
    manual_status: str | None = None
    owner: str | None = None
    tags: list[Any] | None = None


class MoveLeadRequest(BaseModel):
    stage: str
    sort_order: int | None = None


class BulkMoveRequest(BaseModel):
    lead_ids: list[UUID]
    stage: str


class BulkDeleteRequest(BaseModel):
    lead_ids: list[UUID]


# ── Garbage ──

class GarbageRequest(BaseModel):
    reason: str
    note: str | None = None


# ── Snooze ──

class SnoozeRequest(BaseModel):
    until: datetime
    reason: str | None = None


# ── Manual Status ──

class ManualStatusRequest(BaseModel):
    status: str | None = None


# ── Assignment ──

class AssignRequest(BaseModel):
    owner: str


# ── Notes ──

class NoteResponse(BaseModel):
    id: UUID
    lead_stage_id: UUID
    content: str
    author: str | None = None
    is_pinned: bool = False
    created_at: datetime


class NoteCreateRequest(BaseModel):
    content: str = Field(min_length=1)
    author: str | None = None


# ── Tasks ──

class TaskResponse(BaseModel):
    id: UUID
    lead_stage_id: UUID
    title: str
    description: str | None = None
    due_date: datetime | None = None
    priority: str = "medium"
    owner: str | None = None
    completed: bool = False
    completed_at: datetime | None = None
    created_at: datetime


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    due_date: datetime | None = None
    priority: str = "medium"
    owner: str | None = None


# ── Timeline ──

class TimelineResponse(BaseModel):
    id: UUID
    lead_stage_id: UUID
    event_type: str
    title: str
    description: str | None = None
    actor: str | None = None
    metadata_json: dict[str, Any] = {}
    created_at: datetime


# ── Actions ──

class ActionResponse(BaseModel):
    id: UUID
    lead_stage_id: UUID
    action_type: str
    performed_by: str | None = None
    details: dict[str, Any] = {}
    previous_stage: str | None = None
    new_stage: str | None = None
    created_at: datetime


# ── Filters ──

class FilterValuesResponse(BaseModel):
    industry: list[str] = []
    country: list[str] = []
    service_match: list[str] = []
    source_connector: list[str] = []
    trigger: list[str] = []
    owner: list[str] = []


# ── Stage Counts ──

class StageCountsResponse(BaseModel):
    counts: dict[str, int]
    total: int
