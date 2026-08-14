from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ComponentHealth(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    status: str
    score: float = Field(ge=0.0, le=100.0)
    latency_ms: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class SystemHealthReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    overall_score: float
    status: str
    components: list[ComponentHealth] = Field(default_factory=list)
    mode: str = "sandbox"
    recommendations: list[str] = Field(default_factory=list)


class E2EStepResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    passed: bool
    detail: str = ""
    duration_ms: float = 0.0


class E2ERunResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    scenario: str
    passed: bool
    steps: list[E2EStepResult] = Field(default_factory=list)
    mode: str = "sandbox"
