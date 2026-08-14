from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class IdentityCoverageSnapshot(BaseModel):
    __tablename__ = "identity_coverage_snapshots"

    signal_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), index=True)
    website: Mapped[str | None] = mapped_column(String(1024))
    admitted_hint: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="ice-v1", nullable=False)


class IdentityProviderResult(BaseModel):
    __tablename__ = "identity_provider_results"

    snapshot_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("identity_coverage_snapshots.id"))
    provider: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    field: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    collector: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class IdentityAliasGraph(BaseModel):
    __tablename__ = "identity_alias_graph"

    primary_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    aliases: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    official_domain: Mapped[str | None] = mapped_column(String(255), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    merge_evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class IdentityDomainIntelligence(BaseModel):
    __tablename__ = "identity_domain_intelligence"

    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    dns_ok: Mapped[bool | None] = mapped_column(Boolean)
    ssl_ok: Mapped[bool | None] = mapped_column(Boolean)
    mx: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class IdentityCollectorMetric(BaseModel):
    __tablename__ = "identity_collector_metrics"

    collector: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    recommendation: Mapped[str] = mapped_column(String(32), default="KEEP", nullable=False)
    signals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    official_websites: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    business_emails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    decision_makers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    identity_precision: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    identity_recall: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class IdentityRecoveryQueue(BaseModel):
    __tablename__ = "identity_recovery_queue"

    signal_id: Mapped[str] = mapped_column(String(128), nullable=False)
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    reason: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String(255))
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class IdentityDailyReport(BaseModel):
    __tablename__ = "identity_daily_reports"

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    coverage_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    vansh_ready_answer: Mapped[str] = mapped_column(String(8), default="NO", nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="ice-v1", nullable=False)
