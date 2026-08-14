from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AutonomousSalesAgentPackResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    run_id: str | None = None
    company_id: str | None = None
    company_name: str | None = None
    stage: str | None = None
    next_action: str | None = None
    confidence: float | None = None
    next_best_action: dict[str, Any] = Field(default_factory=dict)
    follow_up: dict[str, Any] = Field(default_factory=dict)
    work_queue: list[dict[str, Any]] = Field(default_factory=list)
    morning_brief: dict[str, Any] = Field(default_factory=dict)
    meeting_intelligence: dict[str, Any] | None = None
    case_study: dict[str, Any] | None = None
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    scoring_version: str | None = None


class FounderWorkQueueResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    items: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    scoring_version: str = "asa-v1"
    founder_focus: list[str] = Field(default_factory=list)


class MorningBriefResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    priorities: list[str] = Field(default_factory=list)
    expected_meetings: list[dict[str, Any]] = Field(default_factory=list)
    expected_replies: list[dict[str, Any]] = Field(default_factory=list)
    high_risk_deals: list[dict[str, Any]] = Field(default_factory=list)
    companies_requiring_attention: list[dict[str, Any]] = Field(default_factory=list)
    revenue_forecast: float = 0.0
    follow_ups_due: list[dict[str, Any]] = Field(default_factory=list)
    scoring_version: str = "asa-v1"
