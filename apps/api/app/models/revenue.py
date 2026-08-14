from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ServiceCategory(BaseModel):
    __tablename__ = "service_categories"
    __table_args__ = (Index("ix_service_categories_key", "category_key"),)

    category_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class ServiceCatalog(BaseModel):
    __tablename__ = "services"
    __table_args__ = (Index("ix_services_key_enabled", "service_key", "enabled"),)

    service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_key: Mapped[str] = mapped_column(String(128), nullable=False)
    base_price: Mapped[float] = mapped_column(Float, nullable=False)
    monthly_price: Mapped[float] = mapped_column(Float, nullable=False)
    complexity: Mapped[str] = mapped_column(String(32), nullable=False)
    matching_terms: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    target_pains: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    target_industries: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ServiceRule(BaseModel):
    __tablename__ = "service_rules"
    __table_args__ = (Index("ix_service_rules_service_version", "service_key", "version"),)

    service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_key: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    conditions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)


class SolutionMatch(BaseModel):
    __tablename__ = "solution_matches"
    __table_args__ = (Index("ix_solution_matches_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    primary_service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    secondary_service_key: Mapped[str | None] = mapped_column(String(128))
    cross_sell_service_keys: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    upsell_service_keys: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RevenueBuyerPersona(BaseModel):
    __tablename__ = "buyer_personas"
    __table_args__ = (Index("ix_buyer_personas_company_persona", "company_id", "persona"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    solution_match_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("solution_matches.id"), nullable=False)
    persona: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SalesPlaybook(BaseModel):
    __tablename__ = "sales_playbooks"
    __table_args__ = (Index("ix_sales_playbooks_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    solution_match_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("solution_matches.id"), nullable=False)
    business_pain: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_service: Mapped[str] = mapped_column(String(255), nullable=False)
    why: Mapped[str] = mapped_column(Text, nullable=False)
    conversation_angle: Mapped[str] = mapped_column(Text, nullable=False)
    decision_maker: Mapped[str] = mapped_column(String(128), nullable=False)
    expected_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    risk: Mapped[str] = mapped_column(Text, nullable=False)
    playbook: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class DealEstimate(BaseModel):
    __tablename__ = "deal_estimates"
    __table_args__ = (Index("ix_deal_estimates_match_created", "solution_match_id", "created_at"),)

    solution_match_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("solution_matches.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    project_size: Mapped[str] = mapped_column(String(64), nullable=False)
    implementation_complexity: Mapped[str] = mapped_column(String(64), nullable=False)
    estimated_budget_range: Mapped[str] = mapped_column(String(64), nullable=False)
    priority_level: Mapped[str] = mapped_column(String(32), nullable=False)
    mrr_potential: Mapped[float] = mapped_column(Float, nullable=False)
    one_time_revenue: Mapped[float] = mapped_column(Float, nullable=False)
    expansion_potential: Mapped[float] = mapped_column(Float, nullable=False)
    renewal_potential: Mapped[float] = mapped_column(Float, nullable=False)
    strategic_account_value: Mapped[float] = mapped_column(Float, nullable=False)
    revenue_score: Mapped[float] = mapped_column(Float, nullable=False)
    urgency: Mapped[float] = mapped_column(Float, nullable=False)
    closing_probability: Mapped[float] = mapped_column(Float, nullable=False)
    strategic_importance: Mapped[float] = mapped_column(Float, nullable=False)
    expected_sales_cycle_days: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)


class IndustryPlaybook(BaseModel):
    __tablename__ = "industry_playbooks"
    __table_args__ = (Index("ix_industry_playbooks_industry_service", "industry", "service_key"),)

    industry: Mapped[str] = mapped_column(String(128), nullable=False)
    service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    playbook: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)


class DealPredictionModel(BaseModel):
    __tablename__ = "deal_predictions"
    __table_args__ = (Index("ix_deal_predictions_match_created", "solution_match_id", "created_at"),)

    solution_match_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("solution_matches.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    revenue_score: Mapped[float] = mapped_column(Float, nullable=False)
    urgency: Mapped[float] = mapped_column(Float, nullable=False)
    closing_probability: Mapped[float] = mapped_column(Float, nullable=False)
    strategic_importance: Mapped[float] = mapped_column(Float, nullable=False)
    customer_lifetime_value: Mapped[float] = mapped_column(Float, nullable=False)
    implementation_complexity: Mapped[float] = mapped_column(Float, nullable=False)
    priority_level: Mapped[str] = mapped_column(String(32), nullable=False)
    expected_sales_cycle_days: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)


class SalesCycle(BaseModel):
    __tablename__ = "sales_cycles"
    __table_args__ = (Index("ix_sales_cycles_match_created", "solution_match_id", "created_at"),)

    solution_match_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("solution_matches.id"), nullable=False)
    expected_days: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_plan: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)


class CustomerLifetimeModel(BaseModel):
    __tablename__ = "customer_lifetime_models"
    __table_args__ = (Index("ix_customer_lifetime_models_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    solution_match_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("solution_matches.id"), nullable=False)
    lifetime_value: Mapped[float] = mapped_column(Float, nullable=False)
    renewal_probability: Mapped[float] = mapped_column(Float, nullable=False)
    expansion_probability: Mapped[float] = mapped_column(Float, nullable=False)
    model_details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class CrossSellRule(BaseModel):
    __tablename__ = "cross_sell_rules"
    __table_args__ = (Index("ix_cross_sell_rules_service", "service_key"),)

    service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    related_service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    conditions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class UpsellRule(BaseModel):
    __tablename__ = "upsell_rules"
    __table_args__ = (Index("ix_upsell_rules_service", "service_key"),)

    service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    upsell_service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    conditions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ServiceFeedback(BaseModel):
    __tablename__ = "service_feedback"
    __table_args__ = (Index("ix_service_feedback_match_outcome", "solution_match_id", "review_outcome"),)

    solution_match_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("solution_matches.id"), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(128), nullable=False)
    review_outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    revenue_outcome: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)


class RevenueHistory(BaseModel):
    __tablename__ = "revenue_history"
    __table_args__ = (Index("ix_revenue_history_match_action", "solution_match_id", "action"),)

    solution_match_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("solution_matches.id"))
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RecommendationHistory(BaseModel):
    __tablename__ = "recommendation_history"
    __table_args__ = (Index("ix_recommendation_history_match_created", "solution_match_id", "created_at"),)

    solution_match_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("solution_matches.id"), nullable=False)
    recommendation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    recommendation: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RevenueMetric(BaseModel):
    __tablename__ = "revenue_metrics"
    __table_args__ = (Index("ix_revenue_metrics_match_name", "solution_match_id", "metric_name"),)

    solution_match_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("solution_matches.id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    dimensions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
