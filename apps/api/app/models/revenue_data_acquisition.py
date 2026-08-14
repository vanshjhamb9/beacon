from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RdapSourceMetric(BaseModel):
    __tablename__ = "rdap_source_metrics"

    connector: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    roles: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    signals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RdapConnectorScore(BaseModel):
    __tablename__ = "rdap_connector_scores"

    connector: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    grade: Mapped[str] = mapped_column(String(32), nullable=False)
    verified_companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    business_emails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    decision_makers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_yield: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RdapCompanyProfile(BaseModel):
    __tablename__ = "rdap_company_profiles"

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    domain: Mapped[str | None] = mapped_column(String(255), index=True)
    website: Mapped[str | None] = mapped_column(String(1024))
    trust_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sales_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revenue_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dossier: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="rdap-v1", nullable=False)


class RdapContactRecovery(BaseModel):
    __tablename__ = "rdap_contact_recovery"

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    domain: Mapped[str | None] = mapped_column(String(255), index=True)
    email: Mapped[str] = mapped_column(String(512), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    collector: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RdapDmRecovery(BaseModel):
    __tablename__ = "rdap_dm_recovery"

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    domain: Mapped[str | None] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(128))
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence_url: Mapped[str | None] = mapped_column(String(1024))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RdapRecoveryQueue(BaseModel):
    __tablename__ = "rdap_recovery_queue"

    signal_id: Mapped[str | None] = mapped_column(String(128))
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RdapRevenueYield(BaseModel):
    __tablename__ = "rdap_revenue_yield"

    connector: Mapped[str] = mapped_column(String(64), nullable=False)
    signals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    emails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    decision_makers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    yield_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RdapDailyReport(BaseModel):
    __tablename__ = "rdap_daily_reports"

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    verified_companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    business_emails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    decision_makers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sales_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    vansh_ready_answer: Mapped[str] = mapped_column(String(8), default="NO", nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="rdap-v1", nullable=False)
