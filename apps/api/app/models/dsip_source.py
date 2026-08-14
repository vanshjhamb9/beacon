"""DSIP: Source Registry & Source Reliability Models."""

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


class SourceRegistry(BaseModel):
    """Every discovery source is registered here."""
    __tablename__ = "dsip_source_registry"

    source_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # search, directory, ecommerce, technology, startup, registry, review, jobs, social, news, marketplace, crm, csv, upload
    connector_type: Mapped[str] = mapped_column(String(100), nullable=False)  # google_search, crunchbase, shopify_store, indian_directory, social_media, job_board, news_rss, csv_upload, etc.

    # Authentication
    auth_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # api_key, oauth, none
    auth_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Encrypted auth details

    # Rate Limits
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60)
    rate_limit_per_day: Mapped[int] = mapped_column(Integer, default=10000)
    rate_limit_per_month: Mapped[int] = mapped_column(Integer, default=300000)

    # Coverage
    supported_countries: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["IN", "US", "AE"]
    supported_industries: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["beauty", "fashion"]
    supported_platforms: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["shopify", "woocommerce"]
    supported_languages: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["en", "hi"]

    # Quality Metrics
    average_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    average_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)

    # Cost
    cost_per_request: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_cost_limit: Mapped[float] = mapped_column(Float, default=0.0)
    current_monthly_cost: Mapped[float] = mapped_column(Float, default=0.0)

    # Priority & Freshness
    priority: Mapped[int] = mapped_column(Integer, default=50)  # 0-100
    freshness_hours: Mapped[int] = mapped_column(Integer, default=168)  # How often to re-crawl (7 days default)

    # Health
    health_status: Mapped[str] = mapped_column(String(20), default="unknown")  # healthy, degraded, unhealthy, unknown
    health_score: Mapped[float] = mapped_column(Float, default=0.0)
    last_health_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_successful_crawl: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, paused, deprecated, error
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    connector_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class SourceReliability(BaseModel):
    """Dynamic trust score for every source."""
    __tablename__ = "dsip_source_reliability"

    source_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Core Metrics (0-100)
    accuracy_score: Mapped[float] = mapped_column(Float, default=50.0)
    coverage_score: Mapped[float] = mapped_column(Float, default=50.0)
    freshness_score: Mapped[float] = mapped_column(Float, default=50.0)
    latency_score: Mapped[float] = mapped_column(Float, default=50.0)
    reliability_score: Mapped[float] = mapped_column(Float, default=50.0)  # Composite

    # Failure Tracking
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    successful_requests: Mapped[int] = mapped_column(Integer, default=0)
    failed_requests: Mapped[int] = mapped_column(Integer, default=0)
    timeout_requests: Mapped[int] = mapped_column(Integer, default=0)

    # Quality Tracking
    total_extracted: Mapped[int] = mapped_column(Integer, default=0)
    verified_extracted: Mapped[int] = mapped_column(Integer, default=0)
    conflicted_extracted: Mapped[int] = mapped_column(Integer, default=0)
    fabricated_detected: Mapped[int] = mapped_column(Integer, default=0)

    # Conflict Rate
    conflict_rate: Mapped[float] = mapped_column(Float, default=0.0)
    verification_rate: Mapped[float] = mapped_column(Float, default=0.0)
    fabrication_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Historical
    reliability_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{date, score}]
    last_calculated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SourceCrawlLog(BaseModel):
    """Log of every source crawl attempt."""
    __tablename__ = "dsip_source_crawl_log"

    source_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)

    # Results
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success, partial, failed, timeout
    companies_found: Mapped[int] = mapped_column(Integer, default=0)
    companies_accepted: Mapped[int] = mapped_column(Integer, default=0)
    companies_rejected: Mapped[int] = mapped_column(Integer, default=0)
    duplicates_found: Mapped[int] = mapped_column(Integer, default=0)

    # Error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Rate Limit
    requests_made: Mapped[int] = mapped_column(Integer, default=0)
    rate_limit_remaining: Mapped[int] = mapped_column(Integer, default=0)

    # Cost
    cost_incurred: Mapped[float] = mapped_column(Float, default=0.0)

    # Metadata
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
