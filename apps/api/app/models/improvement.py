from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LearningEvent(BaseModel):
    __tablename__ = "learning_events"
    __table_args__ = (Index("ix_learning_events_area_created", "area", "created_at"),)

    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    area: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_key: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class FeedbackEvent(BaseModel):
    __tablename__ = "feedback_events"
    __table_args__ = (Index("ix_feedback_events_source_area", "source", "area"),)

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    area: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_key: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class GroundTruth(BaseModel):
    __tablename__ = "ground_truth"
    __table_args__ = (Index("ix_ground_truth_entity", "entity_type", "entity_id"),)

    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)


class CollectorPerformance(BaseModel):
    __tablename__ = "collector_performance"
    __table_args__ = (Index("ix_collector_performance_collector_created", "collector", "created_at"),)

    collector: Mapped[str] = mapped_column(String(128), nullable=False)
    precision: Mapped[float] = mapped_column(Float, nullable=False)
    recall: Mapped[float] = mapped_column(Float, nullable=False)
    spam_rate: Mapped[float] = mapped_column(Float, nullable=False)
    duplicate_rate: Mapped[float] = mapped_column(Float, nullable=False)
    conversion_rate: Mapped[float] = mapped_column(Float, nullable=False)
    average_quality: Mapped[float] = mapped_column(Float, nullable=False)
    average_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class QualityRulePerformance(BaseModel):
    __tablename__ = "quality_rule_performance"
    __table_args__ = (Index("ix_quality_rule_performance_rule_created", "rule_key", "created_at"),)

    rule_key: Mapped[str] = mapped_column(String(128), nullable=False)
    times_fired: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_decisions: Mapped[int] = mapped_column(Integer, nullable=False)
    incorrect_decisions: Mapped[int] = mapped_column(Integer, nullable=False)
    override_rate: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    historical_trend: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)


class ClassifierPerformance(BaseModel):
    __tablename__ = "classifier_performance"
    __table_args__ = (Index("ix_classifier_performance_rule_created", "rule_key", "created_at"),)

    rule_key: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    times_fired: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_decisions: Mapped[int] = mapped_column(Integer, nullable=False)
    incorrect_decisions: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    historical_trend: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)


class ContextAccuracy(BaseModel):
    __tablename__ = "context_accuracy"
    __table_args__ = (Index("ix_context_accuracy_context_created", "business_context_id", "created_at"),)

    business_context_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("business_contexts.id"))
    accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)
    corrected_fields: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    ground_truth: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class OpportunityAccuracy(BaseModel):
    __tablename__ = "opportunity_accuracy"
    __table_args__ = (Index("ix_opportunity_accuracy_opportunity_created", "opportunity_id", "created_at"),)

    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    predicted_score: Mapped[float] = mapped_column(Float, nullable=False)
    actual_outcome_score: Mapped[float] = mapped_column(Float, nullable=False)
    prediction_error: Mapped[float] = mapped_column(Float, nullable=False)
    outcome_label: Mapped[str] = mapped_column(String(128), nullable=False)


class RecommendationAccuracy(BaseModel):
    __tablename__ = "recommendation_accuracy"
    __table_args__ = (Index("ix_recommendation_accuracy_action_created", "recommended_action", "created_at"),)

    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    recommended_action: Mapped[str] = mapped_column(String(128), nullable=False)
    actual_outcome: Mapped[str] = mapped_column(String(128), nullable=False)
    accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)


class PredictionHistory(BaseModel):
    __tablename__ = "prediction_history"
    __table_args__ = (Index("ix_prediction_history_entity_created", "entity_type", "entity_id", "created_at"),)

    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    prediction_type: Mapped[str] = mapped_column(String(128), nullable=False)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[float | None] = mapped_column(Float)
    error: Mapped[float | None] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(128), nullable=False)


class ConversionOutcome(BaseModel):
    __tablename__ = "conversion_outcomes"
    __table_args__ = (Index("ix_conversion_outcomes_opportunity_outcome", "opportunity_id", "outcome"),)

    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    outcome: Mapped[str] = mapped_column(String(128), nullable=False)
    outcome_value: Mapped[float] = mapped_column(Float, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class WeightAdjustment(BaseModel):
    __tablename__ = "weight_adjustments"
    __table_args__ = (Index("ix_weight_adjustments_target_created", "target_key", "created_at"),)

    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_key: Mapped[str] = mapped_column(String(255), nullable=False)
    current_weight: Mapped[float | None] = mapped_column(Float)
    recommended_weight: Mapped[float | None] = mapped_column(Float)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    requires_approval: Mapped[str] = mapped_column(String(8), nullable=False)


class ExperimentRun(BaseModel):
    __tablename__ = "experiment_runs"
    __table_args__ = (Index("ix_experiment_runs_key_created", "experiment_key", "created_at"),)

    experiment_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    area: Mapped[str] = mapped_column(String(64), nullable=False)
    variant_a: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    variant_b: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)


class ExperimentResult(BaseModel):
    __tablename__ = "experiment_results"
    __table_args__ = (Index("ix_experiment_results_run_variant", "experiment_run_id", "variant"),)

    experiment_run_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiment_runs.id"), nullable=False)
    variant: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ModelVersion(BaseModel):
    __tablename__ = "model_versions"
    __table_args__ = (Index("ix_model_versions_key_version", "model_key", "version"),)

    model_key: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    area: Mapped[str] = mapped_column(String(64), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)


class RuleVersion(BaseModel):
    __tablename__ = "rule_versions"
    __table_args__ = (Index("ix_rule_versions_key_version", "rule_key", "version"),)

    rule_key: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    area: Mapped[str] = mapped_column(String(64), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
