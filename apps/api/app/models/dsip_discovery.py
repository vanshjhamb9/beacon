"""DSIP: Discovery Job & Discovered Company Models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel, TimestampMixin


class DiscoveryJob(BaseModel):
    """A discovery run triggered by the orchestrator."""
    __tablename__ = "dsip_discovery_job"

    # Input Parameters
    icp_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    icp_profile: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Full ICP snapshot
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)
    revenue_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    company_size_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    company_size_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    technology_filters: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    pain_filters: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    intent_filters: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    negative_icp: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Source Selection
    sources_selected: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{source_id, priority, reason}]
    sources_used: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, running, completed, failed, cancelled
    priority: Mapped[int] = mapped_column(Integer, default=50)

    # Results Summary
    total_discovered: Mapped[int] = mapped_column(Integer, default=0)
    total_accepted: Mapped[int] = mapped_column(Integer, default=0)
    total_rejected: Mapped[int] = mapped_column(Integer, default=0)
    total_duplicates: Mapped[int] = mapped_column(Integer, default=0)
    total_queued: Mapped[int] = mapped_column(Integer, default=0)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)

    # Error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class DiscoveredCompany(BaseModel):
    """Raw company data extracted from a source before canonical resolution."""
    __tablename__ = "dsip_discovered_company"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    connector_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Raw Extracted Data
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Original extraction

    # Normalized Fields
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    canonical_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    primary_domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sub_industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)
    business_model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    marketplace_presence: Mapped[bool] = mapped_column(Boolean, default=False)

    # Store Data
    store_status: Mapped[str | None] = mapped_column(String(50), nullable=True)  # active, inactive, closed
    store_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Size
    estimated_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_employees: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_traffic: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Contacts
    emails: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{email, type, confidence}]
    phones: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    social_profiles: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Technology
    technologies: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Discovery Metadata
    discovery_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    discovery_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Evidence
    evidence: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{field, value, source, timestamp, confidence}]
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Quality
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_grade: Mapped[str | None] = mapped_column(String(5), nullable=True)
    quality_issues: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="new")  # new, validated, duplicate, rejected, canonical, queued
    rejection_reasons: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Canonical Link
    canonical_company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    # Dedup
    duplicate_of: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_canonical: Mapped[bool] = mapped_column(Boolean, default=False)
