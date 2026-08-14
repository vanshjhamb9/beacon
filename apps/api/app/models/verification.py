from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class VerificationReport(BaseModel):
    __tablename__ = "verification_reports"
    __table_args__ = (
        Index("ix_verification_reports_company_created", "company_id", "created_at"),
        Index("ix_verification_reports_enrichment", "enrichment_report_id"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    enrichment_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrichment_reports.id"), nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    overall_data_quality: Mapped[float] = mapped_column(Float, nullable=False)
    overall_readiness: Mapped[float] = mapped_column(Float, nullable=False)
    coverage_percent: Mapped[float] = mapped_column(Float, nullable=False)
    verification_percent: Mapped[float] = mapped_column(Float, nullable=False)
    freshness_score: Mapped[float] = mapped_column(Float, nullable=False)
    freshness_status: Mapped[str] = mapped_column(String(32), nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(String(64), nullable=False)
    automatic_actions: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    reason_codes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    missing_fields: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    readiness_checklist: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    explanation: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    result_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    processing_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)


class ProfileCompleteness(BaseModel):
    __tablename__ = "profile_completeness"
    __table_args__ = (Index("ix_profile_completeness_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    verification_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verification_reports.id"), nullable=False
    )
    enrichment_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrichment_reports.id"), nullable=False
    )
    overall_completeness: Mapped[float] = mapped_column(Float, nullable=False)
    company_profile_completeness: Mapped[float] = mapped_column(Float, nullable=False)
    contact_completeness: Mapped[float] = mapped_column(Float, nullable=False)
    leadership_completeness: Mapped[float] = mapped_column(Float, nullable=False)
    technology_completeness: Mapped[float] = mapped_column(Float, nullable=False)
    revenue_completeness: Mapped[float] = mapped_column(Float, nullable=False)
    hiring_completeness: Mapped[float] = mapped_column(Float, nullable=False)
    social_profile_completeness: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_completeness: Mapped[float] = mapped_column(Float, nullable=False)
    timeline_completeness: Mapped[float] = mapped_column(Float, nullable=False)


class FieldVerification(BaseModel):
    __tablename__ = "field_verification"
    __table_args__ = (Index("ix_field_verification_report_field", "verification_report_id", "field_name"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    verification_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verification_reports.id"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[Any] = mapped_column(JSONB, nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024))
    connector: Mapped[str] = mapped_column(String(64), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    freshness_score: Mapped[float] = mapped_column(Float, nullable=False)
    freshness_status: Mapped[str] = mapped_column(String(32), nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False)
    confirmed_by: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    conflicting_sources: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    is_canonical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    conflict_explanation: Mapped[str | None] = mapped_column(Text)


class CoverageMetric(BaseModel):
    __tablename__ = "coverage_metrics"
    __table_args__ = (Index("ix_coverage_metrics_report_category", "verification_report_id", "category"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    verification_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verification_reports.id"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    present_fields: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_fields: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    missing_fields: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)


class FreshnessMetric(BaseModel):
    __tablename__ = "freshness_metrics"
    __table_args__ = (Index("ix_freshness_metrics_report_created", "verification_report_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    verification_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verification_reports.id"), nullable=False
    )
    field_name: Mapped[str | None] = mapped_column(String(255))
    freshness_score: Mapped[float] = mapped_column(Float, nullable=False)
    freshness_status: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)


class TrustScore(BaseModel):
    __tablename__ = "trust_scores"
    __table_args__ = (Index("ix_trust_scores_report_scope", "verification_report_id", "scope"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    verification_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verification_reports.id"), nullable=False
    )
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str | None] = mapped_column(String(64))
    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class VerificationHistory(BaseModel):
    __tablename__ = "verification_history"
    __table_args__ = (Index("ix_verification_history_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    verification_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verification_reports.id"), nullable=False
    )
    enrichment_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrichment_reports.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ConnectorStatisticRow(BaseModel):
    __tablename__ = "connector_statistics"
    __table_args__ = (
        Index("ix_connector_statistics_report_connector", "verification_report_id", "connector"),
        {"extend_existing": True},
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    verification_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verification_reports.id"), nullable=False
    )
    connector: Mapped[str] = mapped_column(String(64), nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, nullable=False)
    average_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    failure_rate: Mapped[float] = mapped_column(Float, nullable=False)
    coverage: Mapped[float] = mapped_column(Float, nullable=False)
    fields_returned: Mapped[int] = mapped_column(Integer, nullable=False)
    average_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    companies_enriched: Mapped[int] = mapped_column(Integer, nullable=False)


class FieldStatistic(BaseModel):
    __tablename__ = "field_statistics"
    __table_args__ = (Index("ix_field_statistics_report_field", "verification_report_id", "field_name"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    verification_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verification_reports.id"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    present: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    freshness_score: Mapped[float] = mapped_column(Float, nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_count: Mapped[int] = mapped_column(Integer, nullable=False)
