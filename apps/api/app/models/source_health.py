from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SourceHealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class SourceHealth(BaseModel):
    __tablename__ = "source_health"
    __table_args__ = (UniqueConstraint("source", name="uq_source_health_source"),)

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[SourceHealthStatus] = mapped_column(
        Enum(SourceHealthStatus, name="source_health_status"),
        default=SourceHealthStatus.HEALTHY,
        nullable=False,
    )
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    consecutive_failures: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    average_latency_ms: Mapped[float | None] = mapped_column(Float)
