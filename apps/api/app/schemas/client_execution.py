from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ClientExecutionPackResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    profile_id: str | None = None
    company_id: str | None = None
    company_name: str | None = None
    stage: str | None = None
    health_status: str | None = None
    overall_health: float | None = None
    workspace: dict[str, Any] = Field(default_factory=dict)
    handoff: dict[str, Any] = Field(default_factory=dict)
    health: dict[str, Any] = Field(default_factory=dict)
    upsells: list[dict[str, Any]] = Field(default_factory=list)
    scoring_version: str | None = None
