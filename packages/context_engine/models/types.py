from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BuyingStage(StrEnum):
    UNAWARE = "unaware"
    AWARE = "aware"
    PROBLEM_AWARE = "problem_aware"
    SOLUTION_EXPLORING = "solution_exploring"
    VENDOR_EVALUATING = "vendor_evaluating"


class DecisionStage(StrEnum):
    INDIVIDUAL_RESEARCH = "individual_research"
    TEAM_DISCUSSION = "team_discussion"
    BUDGET_DISCOVERY = "budget_discovery"
    EXECUTIVE_REVIEW = "executive_review"


class GrowthStage(StrEnum):
    UNKNOWN = "unknown"
    EARLY = "early"
    SCALING = "scaling"
    EXPANDING = "expanding"
    MATURE = "mature"


class BusinessContextInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    classified_signal_id: UUID
    raw_event_id: UUID
    category: str
    subcategory: str | None
    signal_confidence: float
    business_function: str
    urgency: str
    polarity: str
    title: str
    content: str
    source: str
    published_at: datetime
    quality_report_id: UUID
    quality_score: float
    timeline_item_id: UUID | None = None
    knowledge_node_ids: list[UUID] = Field(default_factory=list)
    company_attributes: dict[str, Any] = Field(default_factory=dict)
    signal_evidence: dict[str, Any] = Field(default_factory=dict)

    @property
    def text(self) -> str:
        return f"{self.title}\n{self.content}".lower()


class EvidenceChain(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_events: list[UUID]
    timeline_references: list[UUID] = Field(default_factory=list)
    knowledge_graph_references: list[UUID] = Field(default_factory=list)
    rule_references: list[str] = Field(default_factory=list)
    quality_references: list[UUID] = Field(default_factory=list)
    confidence_breakdown: dict[str, float] = Field(default_factory=dict)
    explanation: str


class ContextInference(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: str
    category: str
    value: str
    confidence: float
    evidence: EvidenceChain
    attributes: dict[str, Any] = Field(default_factory=dict)


class BusinessContextResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    classified_signal_id: UUID
    raw_event_id: UUID
    business_pain: ContextInference
    business_goal: ContextInference
    business_trigger: ContextInference
    business_impact: ContextInference
    business_urgency: str
    buying_stage: BuyingStage
    decision_stage: DecisionStage
    growth_stage: GrowthStage
    digital_maturity: float
    ai_readiness: float
    automation_readiness: float
    budget_probability: float
    technology_maturity: float
    expansion_probability: float
    operational_pressure: float
    customer_experience_pressure: float
    support_pressure: float
    engineering_pressure: float
    marketing_pressure: float
    sales_pressure: float
    confidence: float
    evidence: EvidenceChain
    processing_time_ms: float


class CompanyDNAResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    industry: str | None
    business_model: str
    company_stage: GrowthStage
    growth_pattern: str
    technology_stack: list[str]
    digital_maturity: float
    ai_adoption: float
    automation_adoption: float
    hiring_pattern: str
    expansion_pattern: str
    innovation_score: float
    support_maturity: float
    operational_maturity: float
    technology_maturity: float
    customer_maturity: float
    evidence: EvidenceChain
    completeness_score: float
