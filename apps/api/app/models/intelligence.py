from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Company(BaseModel):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_companies_normalized_name"),
        Index("ix_companies_last_seen_at", "last_seen_at"),
        Index("ix_companies_signal_frequency", "signal_frequency"),
        Index("ix_companies_primary_domain", "primary_domain"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_domain: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(String(128))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    signal_frequency: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    memory_summary: Mapped[str | None] = mapped_column(Text)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class Person(BaseModel):
    __tablename__ = "people"
    __table_args__ = (
        UniqueConstraint("normalized_name", "company_id", name="uq_people_name_company"),
        Index("ix_people_normalized_name", "normalized_name"),
        Index("ix_people_company_id", "company_id"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class Domain(BaseModel):
    __tablename__ = "domains"
    __table_args__ = (
        UniqueConstraint("domain", name="uq_domains_domain"),
        Index("ix_domains_company_id", "company_id"),
    )

    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class CompanyAlias(BaseModel):
    __tablename__ = "company_aliases"
    __table_args__ = (
        UniqueConstraint("company_id", "normalized_alias", name="uq_company_aliases_company_alias"),
        Index("ix_company_aliases_normalized_alias", "normalized_alias"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    evidence_event_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"))


class SignalEntity(BaseModel):
    __tablename__ = "signal_entities"
    __table_args__ = (
        Index("ix_signal_entities_event_id", "event_id"),
        Index("ix_signal_entities_company_id", "company_id"),
        Index("ix_signal_entities_entity_type_value", "entity_type", "normalized_value"),
    )

    event_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"), nullable=False)
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    person_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("people.id"))
    domain_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("domains.id"))
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[str] = mapped_column(String(512), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(512), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ClassifiedSignal(BaseModel):
    __tablename__ = "classified_signals"
    __table_args__ = (
        UniqueConstraint("event_id", "company_id", "category", name="uq_classified_signals_event_company_category"),
        Index("ix_classified_signals_company_created", "company_id", "created_at"),
        Index("ix_classified_signals_category", "category"),
        Index("ix_classified_signals_urgency", "urgency"),
        Index("ix_classified_signals_overall_confidence", "overall_confidence"),
    )

    event_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"), nullable=False)
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    subcategory: Mapped[str | None] = mapped_column(String(128))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    business_function: Mapped[str] = mapped_column(String(128), nullable=False)
    urgency: Mapped[str] = mapped_column(String(32), nullable=False)
    positive_or_negative: Mapped[str] = mapped_column(String(32), nullable=False)
    source_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    entity_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    classification_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    freshness_score: Mapped[float] = mapped_column(Float, nullable=False)
    reliability_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_explanation: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class CompanyTimeline(BaseModel):
    __tablename__ = "company_timelines"
    __table_args__ = (
        UniqueConstraint("company_id", "event_id", "signal_type", name="uq_company_timeline_item"),
        Index("ix_company_timelines_company_timestamp", "company_id", "timestamp"),
        Index("ix_company_timelines_signal_type", "signal_type"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    event_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class CompanyRelationship(BaseModel):
    __tablename__ = "company_relationships"
    __table_args__ = (
        Index("ix_company_relationships_source_company", "source_company_id"),
        Index("ix_company_relationships_target_company", "target_company_id"),
        Index("ix_company_relationships_type", "relationship_type"),
    )

    source_company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    target_company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_event_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"))
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class KnowledgeGraphNode(BaseModel):
    __tablename__ = "knowledge_graph_nodes"
    __table_args__ = (
        UniqueConstraint("node_type", "external_id", name="uq_knowledge_graph_nodes_type_external"),
        Index("ix_knowledge_graph_nodes_type", "node_type"),
        Index("ix_knowledge_graph_nodes_label", "label"),
    )

    node_type: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    properties: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class KnowledgeGraphEdge(BaseModel):
    __tablename__ = "knowledge_graph_edges"
    __table_args__ = (
        UniqueConstraint("from_node_id", "to_node_id", "edge_type", name="uq_knowledge_graph_edges_triplet"),
        Index("ix_knowledge_graph_edges_from", "from_node_id"),
        Index("ix_knowledge_graph_edges_to", "to_node_id"),
        Index("ix_knowledge_graph_edges_type", "edge_type"),
    )

    from_node_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_graph_nodes.id"), nullable=False)
    to_node_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_graph_nodes.id"), nullable=False)
    edge_type: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_event_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_events.id"))
    properties: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
