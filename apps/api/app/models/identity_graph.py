from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class IgfResolutionRun(BaseModel):
    __tablename__ = "igf_resolution_runs"

    signal_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    raw_event_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"))
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_role: Mapped[str] = mapped_column(String(32), nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    admitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    identity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(1024))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="igf-v1", nullable=False)


class IgfIdentityCandidate(BaseModel):
    __tablename__ = "igf_identity_candidates"

    run_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("igf_resolution_runs.id"))
    signal_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    aliases: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    possible_domain: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_role: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class IgfIdentityEvidence(BaseModel):
    __tablename__ = "igf_identity_evidence"

    run_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("igf_resolution_runs.id"))
    canonical_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    field: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    collector: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class IgfCanonicalCompany(BaseModel):
    __tablename__ = "igf_canonical_companies"

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    aliases: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    official_domain: Mapped[str | None] = mapped_column(String(255), index=True)
    website: Mapped[str | None] = mapped_column(String(1024))
    linkedin_company_url: Mapped[str | None] = mapped_column(String(1024))
    github_organization: Mapped[str | None] = mapped_column(String(255))
    crunchbase: Mapped[str | None] = mapped_column(String(1024))
    industry: Mapped[str | None] = mapped_column(String(128))
    country: Mapped[str | None] = mapped_column(String(128))
    employee_range: Mapped[str | None] = mapped_column(String(64))
    founded: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collectors: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    signals: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="igf-v1", nullable=False)


class IgfFunnelSnapshot(BaseModel):
    __tablename__ = "igf_funnel_snapshots"

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    signals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    candidates: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    official_websites: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified_companies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="igf-v1", nullable=False)
