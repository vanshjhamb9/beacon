from typing import Any

from sqlalchemy import Boolean, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SourceConnectorRow(BaseModel):
    __tablename__ = "source_connectors"
    __table_args__ = (Index("ix_goap_connectors_connector_id", "connector_id"),)

    connector_id: Mapped[str] = mapped_column(String(64), nullable=False)
    connector_name: Mapped[str] = mapped_column(String(128), nullable=False)
    access_mode: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="general")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="goap-v1")


class SourceRunRow(BaseModel):
    __tablename__ = "source_runs"
    __table_args__ = (Index("ix_goap_runs_connector_created", "connector_id", "created_at"),)

    connector_id: Mapped[str] = mapped_column(String(64), nullable=False)
    signals_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    companies_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    opportunities_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    errors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class OpportunityGraphNodeRow(BaseModel):
    __tablename__ = "opportunity_graph_nodes"
    __table_args__ = (Index("ix_goap_nodes_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    node_id: Mapped[str] = mapped_column(String(64), nullable=False)
    node_type: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class OpportunityGraphEdgeRow(BaseModel):
    __tablename__ = "opportunity_graph_edges"
    __table_args__ = (Index("ix_goap_edges_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    edge_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    relation: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ConnectorScoreRow(BaseModel):
    __tablename__ = "connector_scores"
    __table_args__ = (Index("ix_goap_scores_connector", "connector_id", "created_at"),)

    connector_id: Mapped[str] = mapped_column(String(64), nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    coverage_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    freshness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    roi_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class ConnectorBenchmarkRow(BaseModel):
    __tablename__ = "connector_benchmarks"
    __table_args__ = (Index("ix_goap_benchmarks_connector", "connector_id", "created_at"),)

    connector_id: Mapped[str] = mapped_column(String(64), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recommendation: Mapped[str] = mapped_column(String(64), nullable=False, default="maintain")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class WebsiteProfileRow(BaseModel):
    __tablename__ = "website_profiles"
    __table_args__ = (Index("ix_goap_website_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    modernization_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class TechnologyProfileRow(BaseModel):
    __tablename__ = "technology_profiles"
    __table_args__ = (Index("ix_goap_tech_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    technology: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class FundingEventRow(BaseModel):
    __tablename__ = "funding_events"
    __table_args__ = (Index("ix_goap_funding_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    round: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class HiringEventRow(BaseModel):
    __tablename__ = "hiring_events"
    __table_args__ = (Index("ix_goap_hiring_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    growth: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class ReviewSignalRow(BaseModel):
    __tablename__ = "review_signals"
    __table_args__ = (Index("ix_goap_reviews_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class CommunitySignalRow(BaseModel):
    __tablename__ = "community_signals"
    __table_args__ = (Index("ix_goap_community_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class ProcurementSignalRow(BaseModel):
    __tablename__ = "procurement_signals"
    __table_args__ = (Index("ix_goap_procurement_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    tender_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class SourceAlertRow(BaseModel):
    __tablename__ = "source_alerts"
    __table_args__ = (Index("ix_goap_alerts_created", "created_at"),)

    alert_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    connector_id: Mapped[str | None] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class ConnectorHistoryRow(BaseModel):
    __tablename__ = "connector_history"
    __table_args__ = (Index("ix_goap_history_connector", "connector_id", "created_at"),)

    connector_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
