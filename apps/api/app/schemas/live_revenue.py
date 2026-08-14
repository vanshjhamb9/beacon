from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LREPackResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    run_id: str | None = None
    company_id: str
    company_name: str
    campaign_id: str | None = None
    stage: str | None = None
    approval_card: dict[str, Any] | None = None
    email_plan: dict[str, Any] | None = None
    whatsapp_plan: dict[str, Any] | None = None
    meeting_pack: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    analytics: dict[str, Any] | None = None
    learning_hints: list[dict[str, Any]] = Field(default_factory=list)
    lifecycle_events: list[dict[str, Any]] = Field(default_factory=list)
    scoring_version: str | None = None
    evidence_chain: list[str] = Field(default_factory=list)
    created_at: str | None = None


class LREApprovalCenterResponse(BaseModel):
    cards: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    scoring_version: str = "lre-v1"


class LREDashboardResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    total_runs: int = 0
    awaiting_approval: int = 0
    proposals: int = 0
    opens: int = 0
    clicks: int = 0
    recent_runs: list[dict[str, Any]] = Field(default_factory=list)
    scoring_version: str = "lre-v1"


class LRETrackBody(BaseModel):
    tracking_id: str
    event_type: str
    company_id: UUID | None = None
    campaign_id: UUID | None = None
    target_url: str | None = None
