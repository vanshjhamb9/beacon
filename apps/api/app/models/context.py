from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BusinessContext(BaseModel):
    __tablename__ = "business_contexts"
    __table_args__ = (
        Index("ix_business_contexts_company_created", "company_id", "created_at"),
        Index("ix_business_contexts_signal", "classified_signal_id"),
        Index("ix_business_contexts_confidence", "confidence"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    classified_signal_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("classified_signals.id"), nullable=False)
    raw_event_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"), nullable=False)
    quality_report_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quality_reports.id"), nullable=False)
    business_urgency: Mapped[str] = mapped_column(String(32), nullable=False)
    buying_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    decision_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    growth_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    digital_maturity: Mapped[float] = mapped_column(Float, nullable=False)
    ai_readiness: Mapped[float] = mapped_column(Float, nullable=False)
    automation_readiness: Mapped[float] = mapped_column(Float, nullable=False)
    budget_probability: Mapped[float] = mapped_column(Float, nullable=False)
    technology_maturity: Mapped[float] = mapped_column(Float, nullable=False)
    expansion_probability: Mapped[float] = mapped_column(Float, nullable=False)
    operational_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    customer_experience_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    support_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    engineering_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    marketing_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    sales_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class BusinessPain(BaseModel):
    __tablename__ = "business_pains"
    __table_args__ = (Index("ix_business_pains_company_category", "company_id", "category"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    business_context_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("business_contexts.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class BusinessGoal(BaseModel):
    __tablename__ = "business_goals"
    __table_args__ = (Index("ix_business_goals_company_category", "company_id", "category"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    business_context_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("business_contexts.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class BusinessTrigger(BaseModel):
    __tablename__ = "business_triggers"
    __table_args__ = (Index("ix_business_triggers_company_category", "company_id", "category"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    business_context_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("business_contexts.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class BusinessImpact(BaseModel):
    __tablename__ = "business_impacts"
    __table_args__ = (Index("ix_business_impacts_company_category", "company_id", "category"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    business_context_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("business_contexts.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class DecisionSignal(BaseModel):
    __tablename__ = "decision_signals"
    __table_args__ = (Index("ix_decision_signals_company_stage", "company_id", "decision_stage"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    business_context_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("business_contexts.id"), nullable=False)
    buying_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    decision_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    decision_maker_type: Mapped[str] = mapped_column(String(128), nullable=False)
    implementation_complexity: Mapped[str] = mapped_column(String(64), nullable=False)
    potential_budget_range: Mapped[str] = mapped_column(String(64), nullable=False)
    implementation_urgency: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class TechnologySignal(BaseModel):
    __tablename__ = "technology_signals"
    __table_args__ = (Index("ix_technology_signals_company_technology", "company_id", "technology"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    business_context_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("business_contexts.id"), nullable=False)
    technology: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    maturity_score: Mapped[float] = mapped_column(Float, nullable=False)
    adoption_signal: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class IndustryProfile(BaseModel):
    __tablename__ = "industry_profiles"
    __table_args__ = (Index("ix_industry_profiles_industry", "industry"),)

    industry: Mapped[str] = mapped_column(String(128), nullable=False)
    profile_version: Mapped[int] = mapped_column(Integer, nullable=False)
    maturity_benchmarks: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    common_pains: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    technology_patterns: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)


class CompanyProfile(BaseModel):
    __tablename__ = "company_profiles"
    __table_args__ = (Index("ix_company_profiles_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    business_context_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("business_contexts.id"))
    industry: Mapped[str | None] = mapped_column(String(128))
    business_model: Mapped[str] = mapped_column(String(128), nullable=False)
    company_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    growth_pattern: Mapped[str] = mapped_column(String(128), nullable=False)
    technology_stack: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    digital_maturity: Mapped[float] = mapped_column(Float, nullable=False)
    ai_adoption: Mapped[float] = mapped_column(Float, nullable=False)
    automation_adoption: Mapped[float] = mapped_column(Float, nullable=False)
    hiring_pattern: Mapped[str] = mapped_column(String(128), nullable=False)
    expansion_pattern: Mapped[str] = mapped_column(String(128), nullable=False)
    innovation_score: Mapped[float] = mapped_column(Float, nullable=False)
    support_maturity: Mapped[float] = mapped_column(Float, nullable=False)
    operational_maturity: Mapped[float] = mapped_column(Float, nullable=False)
    technology_maturity: Mapped[float] = mapped_column(Float, nullable=False)
    customer_maturity: Mapped[float] = mapped_column(Float, nullable=False)
    completeness_score: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ContextHistory(BaseModel):
    __tablename__ = "context_history"
    __table_args__ = (Index("ix_context_history_company_action", "company_id", "action"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    business_context_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("business_contexts.id"))
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ContextEvidence(BaseModel):
    __tablename__ = "context_evidence"
    __table_args__ = (Index("ix_context_evidence_context_type", "business_context_id", "evidence_type"),)

    business_context_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("business_contexts.id"), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    reference_key: Mapped[str | None] = mapped_column(String(255))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ContextFeedback(BaseModel):
    __tablename__ = "context_feedback"
    __table_args__ = (Index("ix_context_feedback_context_outcome", "business_context_id", "review_outcome"),)

    business_context_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("business_contexts.id"), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(128), nullable=False)
    review_outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    corrected_fields: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    ground_truth: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
