from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RevenueOperationsDashboardResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    snapshot_id: str | None = None
    revenue_score: float | None = None
    pipeline_value: float | None = None
    expected_revenue: float | None = None
    control_tower: dict[str, Any] = Field(default_factory=dict)
    command_center: dict[str, Any] = Field(default_factory=dict)
    forecast: dict[str, Any] = Field(default_factory=dict)
    founder_assistant: dict[str, Any] = Field(default_factory=dict)
    operational_metrics: dict[str, Any] = Field(default_factory=dict)
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    scoring_version: str | None = None
