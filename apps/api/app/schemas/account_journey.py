from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AccountJourneyPackResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    journey_id: str | None = None
    company_id: str | None = None
    company_name: str | None = None
    stage: str | None = None
    health_category: str | None = None
    overall_engagement: float | None = None
    engagement: dict[str, Any] = Field(default_factory=dict)
    health: dict[str, Any] = Field(default_factory=dict)
    follow_up: dict[str, Any] = Field(default_factory=dict)
    buying_committee: dict[str, Any] = Field(default_factory=dict)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    scoring_version: str | None = None
