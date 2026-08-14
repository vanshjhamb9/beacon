from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SignalCategory(StrEnum):
    HIRING = "hiring"
    FUNDING = "funding"
    EXPANSION = "expansion"
    CUSTOMER_SUPPORT = "customer_support"
    AI_ADOPTION = "ai_adoption"
    AUTOMATION = "automation"
    TECHNOLOGY_MIGRATION = "technology_migration"
    PARTNERSHIP = "partnership"
    PRODUCT_LAUNCH = "product_launch"
    CUSTOMER_COMPLAINTS = "customer_complaints"
    HIRING_FREEZE = "hiring_freeze"
    LAYOFFS = "layoffs"
    PRICING_CHANGES = "pricing_changes"
    MARKET_MENTION = "market_mention"


class Polarity(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Urgency(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RawSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID | None = None
    source: str
    url: str
    title: str
    content: str
    published_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def searchable_text(self) -> str:
        return f"{self.title}\n{self.content}".lower()


class ResolvedEntity(BaseModel):
    model_config = ConfigDict(frozen=True)

    entity_type: str
    value: str
    normalized_value: str
    confidence: float
    evidence: dict[str, Any] = Field(default_factory=dict)


class EntityResolutionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    company: ResolvedEntity | None = None
    domain: ResolvedEntity | None = None
    person: ResolvedEntity | None = None
    technologies: list[ResolvedEntity] = Field(default_factory=list)
    products: list[ResolvedEntity] = Field(default_factory=list)


class ClassifiedSignalResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: SignalCategory
    subcategory: str | None
    confidence: float
    business_function: str
    urgency: Urgency
    positive_or_negative: Polarity
    evidence: dict[str, Any] = Field(default_factory=dict)


class ConfidenceResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_confidence: float
    entity_confidence: float
    classification_confidence: float
    freshness_score: float
    reliability_score: float
    overall_confidence: float
    explanation: dict[str, Any]


class TimelineItemDraft(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp: datetime
    source: str
    signal_type: str
    summary: str
    confidence: float
    evidence: dict[str, Any]


class MemoryUpdate(BaseModel):
    model_config = ConfigDict(frozen=True)

    last_seen_at: datetime
    signal_frequency_increment: int
    memory_summary: str
    attributes: dict[str, Any]


class GraphNodeDraft(BaseModel):
    model_config = ConfigDict(frozen=True)

    node_type: str
    external_id: str
    label: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdgeDraft(BaseModel):
    model_config = ConfigDict(frozen=True)

    from_external_id: str
    from_node_type: str
    to_external_id: str
    to_node_type: str
    edge_type: str
    confidence: float
    properties: dict[str, Any] = Field(default_factory=dict)
