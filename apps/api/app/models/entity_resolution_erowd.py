from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class EntityResolutionRunRow(BaseModel):
    __tablename__ = "entity_resolution_runs"

    signal_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    raw_event_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"))
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    admitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    identity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="erowd-v1", nullable=False)


class EntityCandidateRow(BaseModel):
    __tablename__ = "entity_candidates"

    run_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("entity_resolution_runs.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    aliases: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    organization: Mapped[str | None] = mapped_column(String(255))
    domain: Mapped[str | None] = mapped_column(String(255))
    official_website: Mapped[str | None] = mapped_column(String(1024))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class OfficialWebsiteRow(BaseModel):
    __tablename__ = "official_websites"

    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    website: Mapped[str] = mapped_column(String(1024), nullable=False)
    discovered: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    signal_id: Mapped[str | None] = mapped_column(String(128))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class WebsiteAttributionRow(BaseModel):
    __tablename__ = "website_attributions"

    website: Mapped[str | None] = mapped_column(String(1024))
    domain: Mapped[str | None] = mapped_column(String(255))
    discovery_source: Mapped[str] = mapped_column(String(128), nullable=False)
    collector: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    attributed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    signal_id: Mapped[str | None] = mapped_column(String(128))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class IdentityScoreRow(BaseModel):
    __tablename__ = "identity_scores"

    signal_id: Mapped[str] = mapped_column(String(128), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="erowd-v1", nullable=False)


class CanonicalEntityRow(BaseModel):
    __tablename__ = "canonical_entities"

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    official_website: Mapped[str | None] = mapped_column(String(1024))
    domain: Mapped[str | None] = mapped_column(String(255), index=True)
    logo_url: Mapped[str | None] = mapped_column(String(1024))
    industry: Mapped[str | None] = mapped_column(String(128))
    country: Mapped[str | None] = mapped_column(String(128))
    linkedin_url: Mapped[str | None] = mapped_column(String(1024))
    description: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class WebsiteValidationRow(BaseModel):
    __tablename__ = "website_validation"

    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    website: Mapped[str | None] = mapped_column(String(1024))
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    https: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    title: Mapped[str | None] = mapped_column(String(512))
    favicon_url: Mapped[str | None] = mapped_column(String(1024))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class EntityAliasRow(BaseModel):
    __tablename__ = "entity_aliases"

    canonical_entity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_entities.id"))
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String(255))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
