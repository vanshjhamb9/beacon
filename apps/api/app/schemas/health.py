from pydantic import BaseModel, Field


class DependencyStatus(BaseModel):
    status: str = Field(examples=["ok"])
    latency_ms: float | None = None


class HealthResponse(BaseModel):
    status: str
    environment: str
    dependencies: dict[str, DependencyStatus]
