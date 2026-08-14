from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProductionValidationPackResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    snapshot_id: str | None = None
    overall_score: float | None = None
    overall_status: str | None = None
    health: dict[str, Any] = Field(default_factory=dict)
    revenue: dict[str, Any] = Field(default_factory=dict)
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    readiness_report: dict[str, Any] = Field(default_factory=dict)
    founder_board: dict[str, Any] = Field(default_factory=dict)
    weekly_report: dict[str, Any] = Field(default_factory=dict)
    security_audit: dict[str, Any] = Field(default_factory=dict)
    scoring_version: str | None = None
