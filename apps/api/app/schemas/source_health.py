from datetime import datetime

from pydantic import BaseModel


class SourceHealthItem(BaseModel):
    source: str
    status: str
    last_success_at: datetime | None
    last_failure_at: datetime | None
    last_checked_at: datetime | None
    last_error: str | None
    consecutive_failures: int
    average_latency_ms: float | None


class SourceHealthResponse(BaseModel):
    sources: list[SourceHealthItem]
