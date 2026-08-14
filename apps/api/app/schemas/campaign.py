from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CampaignStepResponse(BaseModel):
    id: UUID
    sequence: int
    kind: str
    channel: str
    delay_hours: float
    draft_kind: str
    draft_style: str
    subject_preview: str
    body_preview: str
    message_selection_reason: str
    timing_reason: str
    confidence: float
    status: str
    evidence: list[dict[str, Any]] = Field(default_factory=list)


class CampaignScheduleResponse(BaseModel):
    id: UUID
    campaign_id: UUID
    campaign_step_id: UUID | None = None
    planned_at: datetime
    timezone: str
    status: str
    timing_reason: str


class CampaignApprovalResponse(BaseModel):
    id: UUID
    action: str
    from_status: str
    to_status: str
    actor: str
    notes: str
    created_at: datetime


class CampaignResponse(BaseModel):
    id: UUID
    company_id: UUID
    opportunity_id: UUID
    sales_package_id: UUID | None = None
    company_name: str
    status: str
    priority: str
    primary_channel: str
    secondary_channel: str | None = None
    follow_up_count: int
    delay_hours_between_messages: list[float] = Field(default_factory=list)
    expected_confidence: float
    channel_choice_reason: str
    timing_reason: str
    message_selection_reason: str
    recommended_service: str
    business_pain: str
    buyer_persona: str | None = None
    industry: str | None = None
    communication_style: str
    timezone: str
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    quality: dict[str, Any] = Field(default_factory=dict)
    steps: list[CampaignStepResponse] = Field(default_factory=list)
    schedules: list[CampaignScheduleResponse] = Field(default_factory=list)
    approvals: list[CampaignApprovalResponse] = Field(default_factory=list)
    created_at: datetime


class CampaignListResponse(BaseModel):
    campaigns: list[CampaignResponse]


class CampaignMutationResponse(BaseModel):
    updated: bool = False
    created: bool = False
    detail: str | None = None
    campaign: CampaignResponse | None = None


class CampaignDashboardResponse(BaseModel):
    total_campaigns: int
    needs_review: int
    approved_or_scheduled: int
    paused: int
    cancelled: int
    completed: int
    average_confidence: float
    by_status: dict[str, int] = Field(default_factory=dict)
    by_priority: dict[str, int] = Field(default_factory=dict)
    by_primary_channel: dict[str, int] = Field(default_factory=dict)
    delivery_enabled: bool = False
    pending_approvals: list[dict[str, Any]] = Field(default_factory=list)
    upcoming_schedules: list[dict[str, Any]] = Field(default_factory=list)


class CampaignActionBody(BaseModel):
    actor: str = "operator"
    notes: str = ""


class CampaignBulkActionBody(BaseModel):
    campaign_ids: list[UUID]
    actor: str = "founder"
    notes: str = ""
