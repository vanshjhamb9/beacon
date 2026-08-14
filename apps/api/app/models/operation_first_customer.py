from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class OfcOutreachRecord(BaseModel):
    __tablename__ = "ofc_outreach_records"

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="READY", nullable=False, index=True)
    status_history: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    brief: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    pipeline_value: Mapped[float] = mapped_column(Float, default=5000.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="ofc-v2", nullable=False)


class OfcTimelineEvent(BaseModel):
    __tablename__ = "ofc_timeline_events"

    record_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class OfcFounderNote(BaseModel):
    __tablename__ = "ofc_founder_notes"

    record_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class OfcObjectionEvent(BaseModel):
    __tablename__ = "ofc_objection_events"

    record_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class OfcDailyReport(BaseModel):
    __tablename__ = "ofc_daily_reports"

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    today_action: Mapped[str] = mapped_column(Text, default="", nullable=False)
    vansh_ready_answer: Mapped[str] = mapped_column(String(8), default="NO", nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="ofc-v2", nullable=False)
