from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Opportunity(BaseModel):
    __tablename__ = "opportunities"
    __table_args__ = (
        Index("ix_opportunities_company_created", "company_id", "created_at"),
        Index("ix_opportunities_status_score", "status", "opportunity_score"),
        Index("ix_opportunities_recommendation", "recommendation"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    recommendation: Mapped[str] = mapped_column(String(64), nullable=False)
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    timing_score: Mapped[float] = mapped_column(Float, nullable=False)
    urgency_score: Mapped[float] = mapped_column(Float, nullable=False)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    created_from_context_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    delta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class OpportunityScore(BaseModel):
    __tablename__ = "opportunity_scores"
    __table_args__ = (Index("ix_opportunity_scores_opportunity_name", "opportunity_id", "score_name"),)

    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    score_name: Mapped[str] = mapped_column(String(128), nullable=False)
    score_value: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)


class OpportunityEvidence(BaseModel):
    __tablename__ = "opportunity_evidence"
    __table_args__ = (Index("ix_opportunity_evidence_opportunity_type", "opportunity_id", "source_type"),)

    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    polarity: Mapped[str] = mapped_column(String(32), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class OpportunityHistory(BaseModel):
    __tablename__ = "opportunity_history"
    __table_args__ = (Index("ix_opportunity_history_opportunity_action", "opportunity_id", "action"),)

    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class OpportunityRecommendation(BaseModel):
    __tablename__ = "opportunity_recommendations"
    __table_args__ = (Index("ix_opportunity_recommendations_opportunity_action", "opportunity_id", "action"),)

    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    next_step: Mapped[str] = mapped_column(Text, nullable=False)


class OpportunityTimeline(BaseModel):
    __tablename__ = "opportunity_timeline"
    __table_args__ = (Index("ix_opportunity_timeline_opportunity_created", "opportunity_id", "created_at"),)

    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    reference_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class OpportunityFeedback(BaseModel):
    __tablename__ = "opportunity_feedback"
    __table_args__ = (Index("ix_opportunity_feedback_opportunity_outcome", "opportunity_id", "review_outcome"),)

    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(128), nullable=False)
    review_outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    corrected_fields: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    outcome_label: Mapped[str | None] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text)


class OpportunityConflict(BaseModel):
    __tablename__ = "opportunity_conflicts"
    __table_args__ = (Index("ix_opportunity_conflicts_opportunity_type", "opportunity_id", "conflict_type"),)

    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    conflict_type: Mapped[str] = mapped_column(String(128), nullable=False)
    supporting_signal: Mapped[str] = mapped_column(String(128), nullable=False)
    contradicting_signal: Mapped[str] = mapped_column(String(128), nullable=False)
    severity: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)


class OpportunityLifecycle(BaseModel):
    __tablename__ = "opportunity_lifecycle"
    __table_args__ = (Index("ix_opportunity_lifecycle_opportunity_state", "opportunity_id", "to_status"),)

    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(64))
    to_status: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    rule_key: Mapped[str] = mapped_column(String(128), nullable=False)


class OpportunityMetric(BaseModel):
    __tablename__ = "opportunity_metrics"
    __table_args__ = (Index("ix_opportunity_metrics_name_created", "metric_name", "created_at"),)

    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    dimensions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
