"""RICVP: Revenue Intelligence Calibration & Validation Platform Models."""

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


class ValidationEvent(BaseModel):
    """Every validation event tracked."""
    __tablename__ = "ricvp_validation_event"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # field_validated, cross_source_checked, score_calibrated, confidence_updated
    field_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_method: Mapped[str] = mapped_column(String(50), nullable=False)  # format_check, cross_source, manual, api_verified
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    source_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class EvidenceSource(BaseModel):
    """Evidence trail for every data point."""
    __tablename__ = "ricvp_evidence_source"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    field_value: Mapped[str] = mapped_column(Text, nullable=False)

    # Source
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # website, api, curated, search, manual
    evidence_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    evidence_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Confidence
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Cross-source
    agreeing_sources: Mapped[int] = mapped_column(Integer, default=1)
    conflicting_sources: Mapped[int] = mapped_column(Integer, default=0)
    source_reliability: Mapped[float] = mapped_column(Float, default=0.5)

    # Freshness
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_verified: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FieldValidation(BaseModel):
    """Validation status for every field."""
    __tablename__ = "ricvp_field_validation"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Current value
    current_value: Mapped[str] = mapped_column(Text, nullable=False)
    previous_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Validation
    validation_status: Mapped[str] = mapped_column(String(20), default="pending")  # verified, unverified, conflicting, rejected, stale
    validation_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Confidence
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_trend: Mapped[str | None] = mapped_column(String(20), nullable=True)  # improving, stable, declining

    # Evidence
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    agreeing_sources: Mapped[int] = mapped_column(Integer, default=0)
    conflicting_sources: Mapped[int] = mapped_column(Integer, default=0)

    # Freshness
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_verified: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    next_verification: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ConfidenceScore(BaseModel):
    """Multi-dimensional confidence for every company."""
    __tablename__ = "ricvp_confidence_score"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True, unique=True)

    # Overall
    overall_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_grade: Mapped[str | None] = mapped_column(String(5), nullable=True)  # A, B, C, D, F

    # Component Confidence (0-100)
    discovery_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    technology_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    growth_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    intent_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    pain_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    decision_maker_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    revenue_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    contact_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    quality_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Metadata
    fields_verified: Mapped[int] = mapped_column(Integer, default=0)
    fields_total: Mapped[int] = mapped_column(Integer, default=0)
    evidence_sources: Mapped[int] = mapped_column(Integer, default=0)
    last_calculated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class CalibrationHistory(BaseModel):
    """Score calibration history."""
    __tablename__ = "ricvp_calibration_history"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    score_type: Mapped[str] = mapped_column(String(50), nullable=False)  # revenue, technology, growth, intent, pain, overall

    # Before calibration
    raw_score: Mapped[float] = mapped_column(Float, nullable=False)
    raw_confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Calibration
    calibration_factor: Mapped[float] = mapped_column(Float, default=1.0)
    calibration_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # After calibration
    calibrated_score: Mapped[float] = mapped_column(Float, nullable=False)
    calibrated_confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Accuracy tracking
    predicted_outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)
    actual_outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prediction_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Metadata
    calibration_model: Mapped[str] = mapped_column(String(50), default="v1")
    calibrated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class PredictionHistory(BaseModel):
    """Track every prediction for accuracy measurement."""
    __tablename__ = "ricvp_prediction_history"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    prediction_type: Mapped[str] = mapped_column(String(50), nullable=False)  # close_probability, revenue, buying_window, classification

    # Prediction
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Actual (filled later)
    actual_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prediction_error: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Outcome
    outcome_recorded: Mapped[bool] = mapped_column(Boolean, default=False)
    outcome_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    model_version: Mapped[str] = mapped_column(String(20), default="v1")


class SalesOutcome(BaseModel):
    """Track sales outcomes for continuous learning."""
    __tablename__ = "ricvp_sales_outcome"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Pipeline
    stage: Mapped[str] = mapped_column(String(50), nullable=False)  # lead, engaged, meeting, proposal, negotiation, won, lost
    previous_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Outcome
    outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)  # won, lost, cancelled
    lost_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)  # competitor, budget, timing, no_response, no_fit
    competitor_won: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Revenue
    deal_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    annual_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Contact
    decision_maker_contacted: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Learning
    prediction_at_entry: Mapped[float | None] = mapped_column(Float, nullable=True)
    prediction_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Timing
    engaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meeting_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    days_to_close: Mapped[int | None] = mapped_column(Integer, nullable=True)


class BuyingWindow(BaseModel):
    """Buying window intelligence for every company."""
    __tablename__ = "ricvp_buying_window"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True, unique=True)

    # Window
    window_status: Mapped[str] = mapped_column(String(20), nullable=False)  # immediate, 30_days, 60_days, 90_days, future, dormant
    window_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    window_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Signals
    hiring_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    funding_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    product_launch_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    tech_migration_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    platform_migration_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    support_growth_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    marketing_expansion_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    holiday_season_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    traffic_growth_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    international_expansion_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    customer_complaints_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    competitor_change_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_adoption_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    website_change_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    pricing_change_signal: Mapped[bool] = mapped_column(Boolean, default=False)

    # Score
    buying_score: Mapped[float] = mapped_column(Float, default=0.0)
    urgency_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Timing
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_signal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CompetitiveProfile(BaseModel):
    """Competitive intelligence for every company."""
    __tablename__ = "ricvp_competitive_profile"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True, unique=True)

    # Current Stack
    current_chatbot: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_helpdesk: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_crm: Mapped[str | None] = mapped_column(String(100), nullable=True)
    marketing_stack: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    ai_stack: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    automation_stack: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    analytics_stack: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    payments: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    shipping: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    loyalty: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    subscriptions: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # COMAI Comparison
    technology_gaps: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    competitive_weaknesses: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    replacement_opportunities: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    migration_complexity: Mapped[str | None] = mapped_column(String(50), nullable=True)  # low, medium, high
    switching_cost: Mapped[str | None] = mapped_column(String(50), nullable=True)  # low, medium, high

    # Score
    competitive_score: Mapped[float] = mapped_column(Float, default=0.0)
    replacement_probability: Mapped[float] = mapped_column(Float, default=0.0)

    # Metadata
    last_analyzed: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class RevenueEstimation(BaseModel):
    """Revenue opportunity estimation for every company."""
    __tablename__ = "ricvp_revenue_estimation"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True, unique=True)

    # Business Metrics
    monthly_orders: Mapped[int | None] = mapped_column(Integer, nullable=True)
    monthly_visitors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    monthly_conversations: Mapped[int | None] = mapped_column(Integer, nullable=True)
    support_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    whatsapp_messages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    potential_ai_conversations: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Revenue Estimates
    expected_arr: Mapped[float] = mapped_column(Float, default=0.0)
    expansion_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    upsell_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    cross_sell_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    total_opportunity: Mapped[float] = mapped_column(Float, default=0.0)

    # ROI
    estimated_roi: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_payback_months: Mapped[int] = mapped_column(Integer, default=0)
    implementation_complexity: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Confidence
    estimation_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    data_points_used: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    estimated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    model_version: Mapped[str] = mapped_column(String(20), default="v1")


class DataDrift(BaseModel):
    """Track data changes over time."""
    __tablename__ = "ricvp_data_drift"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Change
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)  # added, modified, removed
    change_magnitude: Mapped[float] = mapped_column(Float, default=0.0)

    # Detection
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    detection_method: Mapped[str] = mapped_column(String(50), nullable=False)  # scheduled_crawl, manual, alert

    # Impact
    impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    requires_refresh: Mapped[bool] = mapped_column(Boolean, default=False)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)


class FieldFreshness(BaseModel):
    """Freshness tracking for every field."""
    __tablename__ = "ricvp_field_freshness"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Freshness
    freshness_score: Mapped[float] = mapped_column(Float, default=100.0)
    age_hours: Mapped[float] = mapped_column(Float, default=0.0)
    expected_refresh_hours: Mapped[int] = mapped_column(Integer, default=168)

    # Tracking
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_verified: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    next_refresh: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Source
    source_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_reliability: Mapped[float] = mapped_column(Float, default=0.5)


class ScoreExplanation(BaseModel):
    """Explainable intelligence for every score."""
    __tablename__ = "ricvp_score_explanation"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    score_type: Mapped[str] = mapped_column(String(50), nullable=False)  # overall, revenue, technology, growth, intent, pain

    # Score
    score_value: Mapped[float] = mapped_column(Float, nullable=False)
    score_confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Explanation
    factors: Mapped[list] = mapped_column(JSONB, nullable=False)  # [{factor, impact, evidence, weight}]
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    counter_arguments: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Evidence
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    evidence_sources: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Metadata
    explained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    model_version: Mapped[str] = mapped_column(String(20), default="v1")


class ICPPrediction(BaseModel):
    """ICP prediction tracking for calibration."""
    __tablename__ = "ricvp_icp_prediction"

    canonical_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    icp_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # Prediction
    predicted_match: Mapped[bool] = mapped_column(Boolean, nullable=False)
    predicted_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Actual Outcome
    actual_qualified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    actual_meeting: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    actual_deal: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    actual_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Calibration
    prediction_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    calibration_error: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Metadata
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    outcome_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
