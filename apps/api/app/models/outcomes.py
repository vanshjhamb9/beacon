from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class OpportunityOutcome(BaseModel):
    __tablename__ = "opportunity_outcomes"
    __table_args__ = (
        UniqueConstraint("opportunity_id", name="uq_opportunity_outcomes_opportunity_id"),
        Index("ix_opportunity_outcomes_opportunity_stage", "opportunity_id", "lifecycle_stage"),
        Index("ix_opportunity_outcomes_company_updated", "company_id", "updated_at"),
    )

    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    lifecycle_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(128))
    revenue: Mapped[float | None] = mapped_column(Float)
    close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meeting_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    proposal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recommended_service: Mapped[str | None] = mapped_column(String(255))
    buyer_persona: Mapped[str | None] = mapped_column(String(128))
    industry: Mapped[str | None] = mapped_column(String(128))
    collector: Mapped[str | None] = mapped_column(String(64))
    technology: Mapped[str | None] = mapped_column(String(128))
    decision_maker_role: Mapped[str | None] = mapped_column(String(128))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ContactAttempt(BaseModel):
    __tablename__ = "contact_attempts"
    __table_args__ = (Index("ix_contact_attempts_opportunity_created", "opportunity_id", "created_at"),)

    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    outcome_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunity_outcomes.id"))
    channel: Mapped[str] = mapped_column(String(64), nullable=False)
    owner: Mapped[str | None] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    replied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class Meeting(BaseModel):
    __tablename__ = "meetings"
    __table_args__ = (Index("ix_meetings_opportunity_scheduled", "opportunity_id", "scheduled_at"),)

    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    outcome_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunity_outcomes.id"))
    meeting_type: Mapped[str | None] = mapped_column(String(64))
    owner: Mapped[str | None] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class Proposal(BaseModel):
    __tablename__ = "proposals"
    __table_args__ = (Index("ix_proposals_opportunity_sent", "opportunity_id", "sent_at"),)

    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    outcome_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunity_outcomes.id"))
    value: Mapped[float | None] = mapped_column(Float)
    owner: Mapped[str | None] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="sent")
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class Deal(BaseModel):
    __tablename__ = "deals"
    __table_args__ = (Index("ix_deals_opportunity_closed", "opportunity_id", "closed_at"),)

    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    outcome_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunity_outcomes.id"))
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(16), nullable=False, default="USD")
    owner: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class CustomerFeedback(BaseModel):
    __tablename__ = "customer_feedback"
    __table_args__ = (Index("ix_customer_feedback_company_created", "company_id", "created_at"),)

    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    outcome_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunity_outcomes.id"))
    score: Mapped[float | None] = mapped_column(Float)
    feedback_text: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(128))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class PredictionAccuracy(BaseModel):
    __tablename__ = "prediction_accuracy"
    __table_args__ = (Index("ix_prediction_accuracy_key_created", "metric_key", "created_at"),)

    metric_key: Mapped[str] = mapped_column(String(128), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)
    precision: Mapped[float] = mapped_column(Float, nullable=False)
    recall: Mapped[float] = mapped_column(Float, nullable=False)
    average_prediction_error: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ServiceAccuracy(BaseModel):
    __tablename__ = "service_accuracy"
    __table_args__ = (Index("ix_service_accuracy_service_created", "service_key", "created_at"),)

    service_key: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)
    precision: Mapped[float] = mapped_column(Float, nullable=False)
    recall: Mapped[float] = mapped_column(Float, nullable=False)
    average_prediction_error: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class CollectorAccuracy(BaseModel):
    __tablename__ = "collector_accuracy"
    __table_args__ = (Index("ix_collector_accuracy_collector_created", "collector", "created_at"),)

    collector: Mapped[str] = mapped_column(String(64), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)
    precision: Mapped[float] = mapped_column(Float, nullable=False)
    recall: Mapped[float] = mapped_column(Float, nullable=False)
    average_prediction_error: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class PersonaAccuracy(BaseModel):
    __tablename__ = "persona_accuracy"
    __table_args__ = (Index("ix_persona_accuracy_persona_created", "persona", "created_at"),)

    persona: Mapped[str] = mapped_column(String(128), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)
    precision: Mapped[float] = mapped_column(Float, nullable=False)
    recall: Mapped[float] = mapped_column(Float, nullable=False)
    average_prediction_error: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class IndustryAccuracy(BaseModel):
    __tablename__ = "industry_accuracy"
    __table_args__ = (Index("ix_industry_accuracy_industry_created", "industry", "created_at"),)

    industry: Mapped[str] = mapped_column(String(128), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)
    precision: Mapped[float] = mapped_column(Float, nullable=False)
    recall: Mapped[float] = mapped_column(Float, nullable=False)
    average_prediction_error: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class LearningMetric(BaseModel):
    __tablename__ = "learning_metrics"
    __table_args__ = (Index("ix_learning_metrics_area_created", "area", "created_at"),)

    area: Mapped[str] = mapped_column(String(64), nullable=False)
    target_key: Mapped[str] = mapped_column(String(255), nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    expected_impact: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
