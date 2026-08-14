from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class OduConnectorHealth(BaseModel):
    __tablename__ = "odu_connector_health"

    connector: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    health: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class OduSourceToken(BaseModel):
    __tablename__ = "odu_source_tokens"

    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    env_key: Mapped[str | None] = mapped_column(String(128))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class OduConnectorMetric(BaseModel):
    __tablename__ = "odu_connector_metrics"

    connector: Mapped[str] = mapped_column(String(64), nullable=False)
    signals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    websites: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    emails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    decision_makers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    yield_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class OduDailyReport(BaseModel):
    __tablename__ = "odu_daily_reports"

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    verified_companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    business_emails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    decision_makers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sales_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    vansh_ready_answer: Mapped[str] = mapped_column(String(8), default="NO", nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="odu-v1", nullable=False)


class OduRecoveryQueue(BaseModel):
    __tablename__ = "odu_recovery_queue"

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    domain: Mapped[str | None] = mapped_column(String(255))
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class OduOperationLog(BaseModel):
    __tablename__ = "odu_operation_logs"

    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
