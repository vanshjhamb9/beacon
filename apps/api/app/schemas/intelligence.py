from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class CompanyResponse(BaseModel):
    id: UUID
    name: str
    normalized_name: str
    primary_domain: str | None
    industry: str | None
    last_seen_at: datetime | None
    signal_frequency: int
    memory_summary: str | None
    attributes: dict[str, Any]


class CompaniesResponse(BaseModel):
    companies: list[CompanyResponse]


class TimelineItemResponse(BaseModel):
    id: UUID
    timestamp: datetime
    event_id: UUID
    source: str
    signal_type: str
    summary: str
    confidence: float
    evidence: dict[str, Any]


class CompanyTimelineResponse(BaseModel):
    timeline: list[TimelineItemResponse]


class ClassifiedSignalResponse(BaseModel):
    id: UUID
    event_id: UUID
    company_id: UUID | None
    category: str
    subcategory: str | None
    confidence: float
    business_function: str
    urgency: str
    positive_or_negative: str
    source_confidence: float
    entity_confidence: float
    classification_confidence: float
    freshness_score: float
    reliability_score: float
    overall_confidence: float
    confidence_explanation: dict[str, Any]
    evidence: dict[str, Any]


class ClassifiedSignalsResponse(BaseModel):
    signals: list[ClassifiedSignalResponse]


class KnowledgeGraphNodeResponse(BaseModel):
    id: UUID
    node_type: str
    external_id: str
    label: str
    properties: dict[str, Any]


class KnowledgeGraphEdgeResponse(BaseModel):
    id: UUID
    from_node_id: UUID
    to_node_id: UUID
    edge_type: str
    confidence: float
    evidence_event_id: UUID | None
    properties: dict[str, Any]


class KnowledgeGraphResponse(BaseModel):
    node: KnowledgeGraphNodeResponse
    edges: list[KnowledgeGraphEdgeResponse]
