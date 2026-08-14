from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class QualityReport(BaseModel):
    __tablename__ = "quality_reports"
    __table_args__ = (
        Index("ix_quality_reports_raw_event_created", "raw_event_id", "created_at"),
        Index("ix_quality_reports_decision_created", "decision", "created_at"),
        Index("ix_quality_reports_source_created", "source", "created_at"),
        Index("ix_quality_reports_overall_quality", "overall_quality_score"),
    )

    raw_event_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    grade: Mapped[str] = mapped_column(String(16), nullable=False)
    schema_score: Mapped[float] = mapped_column(Float, nullable=False)
    spam_score: Mapped[float] = mapped_column(Float, nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    freshness_score: Mapped[float] = mapped_column(Float, nullable=False)
    completeness_score: Mapped[float] = mapped_column(Float, nullable=False)
    entity_confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    duplicate_probability: Mapped[float] = mapped_column(Float, nullable=False)
    overall_quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    queue_time_ms: Mapped[float | None] = mapped_column(Float)
    reason_codes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    explanation: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class QualityMetric(BaseModel):
    __tablename__ = "quality_metrics"
    __table_args__ = (
        Index("ix_quality_metrics_report_stage", "quality_report_id", "stage"),
        Index("ix_quality_metrics_metric_name_created", "metric_name", "created_at"),
    )

    quality_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quality_reports.id"), nullable=False
    )
    raw_event_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    reason_codes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class QualityRule(BaseModel):
    __tablename__ = "quality_rules"
    __table_args__ = (
        Index("ix_quality_rules_key_version", "rule_key", "version"),
        Index("ix_quality_rules_category_enabled", "category", "enabled"),
    )

    rule_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SourceStatistic(BaseModel):
    __tablename__ = "source_statistics"
    __table_args__ = (
        Index("ix_source_statistics_source_window", "source", "window_start", "window_end"),
        Index("ix_source_statistics_average_quality", "average_quality"),
    )

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    signals_collected: Mapped[int] = mapped_column(Integer, nullable=False)
    signals_accepted: Mapped[int] = mapped_column(Integer, nullable=False)
    signals_rejected: Mapped[int] = mapped_column(Integer, nullable=False)
    spam_rate: Mapped[float] = mapped_column(Float, nullable=False)
    duplicate_rate: Mapped[float] = mapped_column(Float, nullable=False)
    average_quality: Mapped[float] = mapped_column(Float, nullable=False)
    average_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    average_processing_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    collector_health: Mapped[str] = mapped_column(String(32), nullable=False)
    historical_trend: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)


class SpamPattern(BaseModel):
    __tablename__ = "spam_patterns"
    __table_args__ = (
        Index("ix_spam_patterns_pattern_hash", "pattern_hash"),
        Index("ix_spam_patterns_source_seen", "source", "last_seen_at"),
    )

    pattern_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    pattern_type: Mapped[str] = mapped_column(String(64), nullable=False)
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    occurrences: Mapped[int] = mapped_column(Integer, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class QualityAudit(BaseModel):
    __tablename__ = "quality_audit"
    __table_args__ = (
        Index("ix_quality_audit_raw_event_created", "raw_event_id", "created_at"),
        Index("ix_quality_audit_action", "action"),
    )

    raw_event_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"))
    quality_report_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quality_reports.id")
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class QualityFeedback(BaseModel):
    __tablename__ = "quality_feedback"
    __table_args__ = (
        Index("ix_quality_feedback_report_created", "quality_report_id", "created_at"),
        Index("ix_quality_feedback_event_outcome", "raw_event_id", "review_outcome"),
    )

    quality_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quality_reports.id"), nullable=False
    )
    raw_event_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(128), nullable=False)
    review_outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    corrected_decision: Mapped[str | None] = mapped_column(String(32))
    corrected_reason_codes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
