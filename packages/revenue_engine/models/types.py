from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PriorityLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProjectSize(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class BudgetRange(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class BuyerPersona(StrEnum):
    FOUNDER = "Founder"
    CEO = "CEO"
    COO = "COO"
    CTO = "CTO"
    ENGINEERING_MANAGER = "Engineering Manager"
    SUPPORT_HEAD = "Support Head"
    OPERATIONS_HEAD = "Operations Head"
    MARKETING_HEAD = "Marketing Head"


class ServiceDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    service_key: str
    name: str
    category: str
    base_price: float
    monthly_price: float
    complexity: str
    matching_terms: list[str] = Field(default_factory=list)
    target_pains: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    enabled: bool = True


class RevenueOpportunityInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    opportunity_id: UUID
    opportunity_score: float
    urgency_score: float
    confidence_score: float
    recommendation: str
    narrative: str
    industry: str | None
    business_model: str | None
    company_stage: str | None
    technology_stack: list[str]
    pains: list[dict[str, Any]]
    goals: list[dict[str, Any]]
    contexts: list[dict[str, Any]]
    opportunity_evidence: list[dict[str, Any]]
    knowledge_node_ids: list[UUID]
    quality_score: float
    services: list[ServiceDefinition]


class ServiceMatch(BaseModel):
    model_config = ConfigDict(frozen=True)

    service: ServiceDefinition
    confidence: float
    reasoning: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class BuyerPersonaResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    persona: str
    confidence: float
    explanation: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class RevenueEstimate(BaseModel):
    model_config = ConfigDict(frozen=True)

    project_size: ProjectSize
    implementation_complexity: str
    estimated_budget_range: BudgetRange
    mrr_potential: float
    one_time_revenue: float
    expansion_potential: float
    renewal_potential: float
    strategic_account_value: float
    explanation: str


class DealPrediction(BaseModel):
    model_config = ConfigDict(frozen=True)

    revenue_score: float
    urgency: float
    closing_probability: float
    strategic_importance: float
    customer_lifetime_value: float
    implementation_complexity: float
    priority_level: PriorityLevel
    expected_sales_cycle_days: int
    explanation: str


class RevenuePlaybook(BaseModel):
    model_config = ConfigDict(frozen=True)

    business_pain: str
    recommended_service: str
    why: str
    conversation_angle: str
    decision_maker: str
    expected_outcome: str
    risk: str


class RevenueRecommendationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    opportunity_id: UUID
    primary_service: ServiceMatch
    secondary_service: ServiceMatch | None
    cross_sell: list[ServiceMatch]
    upsell: list[ServiceMatch]
    buyer_personas: list[BuyerPersonaResult]
    revenue_estimate: RevenueEstimate
    deal_prediction: DealPrediction
    playbook: RevenuePlaybook
    confidence: float
    reasoning: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    processing_latency_ms: float = 0.0
