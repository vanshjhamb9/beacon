"""DSIP: Canonical Company, Evidence, Freshness, Queue, Metrics Models."""

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


class CanonicalCompany(BaseModel):
    """Deduplicated, canonical company record. One company = one record."""
    __tablename__ = "dsip_canonical_company"

    # Identity
    canonical_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Domains & URLs
    primary_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    all_domains: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{domain, source, verified}]
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    redirect_chain: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{from, to, status}]

    # Company Profile
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sub_industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)
    business_model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    marketplace_presence: Mapped[bool] = mapped_column(Boolean, default=False)

    # Size
    estimated_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_employees: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_traffic: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Contacts
    primary_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    all_emails: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    primary_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    all_phones: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    social_profiles: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Technology
    technologies: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tech_stack_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Decision Makers
    decision_makers: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Discovery
    discovery_sources: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{source_id, discovered_at, confidence}]
    primary_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_discovered: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Canonical Confidence
    canonical_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    identity_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    data_quality_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Discovery Score (composite)
    discovery_score: Mapped[float] = mapped_column(Float, default=0.0)
    source_quality: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_quality: Mapped[float] = mapped_column(Float, default=0.0)
    website_quality: Mapped[float] = mapped_column(Float, default=0.0)
    freshness_score: Mapped[float] = mapped_column(Float, default=0.0)
    activity_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, inactive, merged, archived
    qualified_for_arie: Mapped[bool] = mapped_column(Boolean, default=False)
    arie_classified: Mapped[str | None] = mapped_column(String(20), nullable=True)  # HOT, WARM, COLD, REJECTED

    # Merge
    merged_from: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [canonical_ids merged into this]
    merge_count: Mapped[int] = mapped_column(Integer, default=0)

    # Tags
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CompanyEvidence(BaseModel):
    """Immutable evidence for every extracted field."""
    __tablename__ = "dsip_company_evidence"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    discovered_company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # What was extracted
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)  # company_name, website, email, etc.
    field_value: Mapped[str] = mapped_column(Text, nullable=False)

    # Source
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Extraction
    extraction_method: Mapped[str] = mapped_column(String(50), nullable=False)  # html_parse, api, regex, structured_data
    extraction_version: Mapped[str] = mapped_column(String(20), default="1.0")

    # Quality
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Immutability
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    first_extracted: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_verified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Conflict
    conflicts_with: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [evidence_ids]
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)


class FreshnessRecord(BaseModel):
    """Freshness tracking for every canonical company."""
    __tablename__ = "dsip_freshness_record"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True, unique=True)

    # Last Seen
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_crawl: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_validated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Change Tracking
    last_name_change: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_tech_change: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_contact_change: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_traffic_change: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_price_change: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_review_change: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Refresh Schedule
    next_scheduled_crawl: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    crawl_frequency_hours: Mapped[int] = mapped_column(Integer, default=168)  # 7 days
    priority_refresh: Mapped[bool] = mapped_column(Boolean, default=False)

    # Freshness Score
    freshness_score: Mapped[float] = mapped_column(Float, default=100.0)  # 100=fresh, 0=stale
    days_since_last_seen: Mapped[int] = mapped_column(Integer, default=0)
    staleness_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)


class DiscoveryQueue(BaseModel):
    """Queue items for processing."""
    __tablename__ = "dsip_discovery_queue"

    canonical_company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    discovered_company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Queue
    queue_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # new_discovery, revalidation, tech_refresh, freshness_refresh, evidence_refresh, priority, manual_review, rejected, retry
    priority: Mapped[int] = mapped_column(Integer, default=50)  # 0-100, higher = more urgent

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, processing, completed, failed
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)

    # Timing
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Error
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Worker
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lock_acquired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DiscoveryMetric(BaseModel):
    """Observability metrics for DSIP."""
    __tablename__ = "dsip_discovery_metric"

    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_type: Mapped[str] = mapped_column(String(20), nullable=False)  # counter, gauge, histogram

    # Dimensions
    source_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    connector_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Value
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)  # ms, count, bytes

    # Timestamp
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Tags
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class CompanyMergeHistory(BaseModel):
    """Track all company merges for audit."""
    __tablename__ = "dsip_company_merge_history"

    surviving_canonical_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    merged_canonical_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Merge Details
    merge_reason: Mapped[str] = mapped_column(String(255), nullable=False)  # domain_match, name_match, phone_match, etc.
    merge_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    merge_method: Mapped[str] = mapped_column(String(50), nullable=False)  # automatic, manual

    # Data
    surviving_data_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    merged_data_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    data_conflicts: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{field, surviving_value, merged_value, resolution}]

    # Audit
    merged_by: Mapped[str] = mapped_column(String(100), default="system")
    merged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    reversible: Mapped[bool] = mapped_column(Boolean, default=True)
