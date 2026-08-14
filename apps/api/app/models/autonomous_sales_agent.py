from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AutonomousSalesAgentRun(BaseModel):
    """Append-only ASA evaluation snapshot."""

    __tablename__ = "autonomous_sales_agent_runs"
    __table_args__ = (
        Index("ix_asa_runs_company_created", "company_id", "created_at"),
        Index("ix_asa_runs_stage", "stage"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    next_action: Mapped[str] = mapped_column(String(64), nullable=False, default="wait")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="asa-v1")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class AutonomousSalesWorkflowTransition(BaseModel):
    """Append-only workflow transitions with reason/evidence/actor/next_action."""

    __tablename__ = "asa_workflow_transitions"
    __table_args__ = (
        Index("ix_asa_transitions_company_ts", "company_id", "occurred_at"),
        Index("ix_asa_transitions_stage", "to_stage"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    run_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("autonomous_sales_agent_runs.id"))
    from_stage: Mapped[str | None] = mapped_column(String(64))
    to_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    next_action: Mapped[str] = mapped_column(String(128), nullable=False, default="continue")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AutonomousSalesTimelineEvent(BaseModel):
    """Append-only relationship timeline."""

    __tablename__ = "asa_timeline_events"
    __table_args__ = (Index("ix_asa_timeline_company_occurred", "company_id", "occurred_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    run_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("autonomous_sales_agent_runs.id"))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    actor: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AutonomousSalesWorkQueueSnapshot(BaseModel):
    """Append-only founder work-queue / morning-brief snapshot."""

    __tablename__ = "asa_work_queue_snapshots"
    __table_args__ = (Index("ix_asa_wq_created", "created_at"),)

    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="work_queue")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue_forecast: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="asa-v1")
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
