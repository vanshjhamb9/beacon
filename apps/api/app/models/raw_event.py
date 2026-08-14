from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, Enum, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RawEventStatus(StrEnum):
    RECEIVED = "RECEIVED"
    PROCESSED = "PROCESSED"
    REJECTED = "REJECTED"


class RawEvent(BaseModel):
    __tablename__ = "raw_events"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_raw_events_idempotency_key"),
        Index("ix_raw_events_source_published_at", "source", "published_at"),
        Index("ix_raw_events_url", "url"),
    )

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stream_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[RawEventStatus] = mapped_column(
        Enum(RawEventStatus, name="raw_event_status"),
        default=RawEventStatus.RECEIVED,
        nullable=False,
    )
    event_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
