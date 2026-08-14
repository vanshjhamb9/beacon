from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AnalyticsTrackBody(BaseModel):
    event_type: str
    action: str
    actor: str = "founder"
    company_id: UUID | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class FounderOsPackResponse(BaseModel):
    brief_id: str | None = None
    brief: dict[str, Any] = Field(default_factory=dict)
    command_center: dict[str, Any] = Field(default_factory=dict)
    assistant: dict[str, Any] = Field(default_factory=dict)
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    kpis: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    proposals: list[dict[str, Any]] = Field(default_factory=list)
    meeting_packs: list[dict[str, Any]] = Field(default_factory=list)
    timeline_events: list[dict[str, Any]] = Field(default_factory=list)
    scoring_version: str | None = None
