from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AccountProfileRow(BaseModel):
    __tablename__ = "aip_account_profiles"
    __table_args__ = (
        Index("ix_aip_profiles_company", "company_id", "created_at"),
        Index("ix_aip_profiles_name", "company_name"),
    )

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    sales_readiness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sales_readiness_category: Mapped[str] = mapped_column(String(32), nullable=False, default="cold")
    ai_readiness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="aip-v1")


class AIPCompanyLocationRow(BaseModel):
    __tablename__ = "aip_company_locations"
    __table_args__ = (Index("ix_aip_locations_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class CompanyDepartmentRow(BaseModel):
    __tablename__ = "aip_company_departments"
    __table_args__ = (Index("ix_aip_departments_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class AIPBuyingCommitteeRow(BaseModel):
    __tablename__ = "aip_buying_committee"
    __table_args__ = (Index("ix_aip_committee_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fabricated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class VerifiedContactRow(BaseModel):
    __tablename__ = "aip_verified_contacts"
    __table_args__ = (Index("ix_aip_contacts_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_email: Mapped[str | None] = mapped_column(String(255))
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class ContactVerificationRow(BaseModel):
    __tablename__ = "aip_contact_verification"
    __table_args__ = (Index("ix_aip_contact_ver_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    field: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class AIPTechnologyProfileRow(BaseModel):
    __tablename__ = "technology_profiles_aip"
    __table_args__ = (Index("ix_aip_tech_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class WebsiteProfileV2Row(BaseModel):
    __tablename__ = "website_profiles_v2"
    __table_args__ = (Index("ix_aip_website_v2_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class FinancialProfileRow(BaseModel):
    __tablename__ = "aip_financial_profiles"
    __table_args__ = (Index("ix_aip_financial_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class BusinessProfileRow(BaseModel):
    __tablename__ = "aip_business_profiles"
    __table_args__ = (Index("ix_aip_business_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    growth_stage: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class GrowthProfileRow(BaseModel):
    __tablename__ = "aip_growth_profiles"
    __table_args__ = (Index("ix_aip_growth_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class AIReadinessReportRow(BaseModel):
    __tablename__ = "ai_readiness_reports"
    __table_args__ = (Index("ix_aip_ai_ready_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    overall: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class SalesReadinessReportRow(BaseModel):
    __tablename__ = "sales_readiness_reports"
    __table_args__ = (Index("ix_aip_sales_ready_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="cold")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class RelationshipGraphNodeRow(BaseModel):
    __tablename__ = "aip_relationship_graph_nodes"
    __table_args__ = (Index("ix_aip_rel_nodes_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    node_id: Mapped[str] = mapped_column(String(64), nullable=False)
    node_type: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class RelationshipGraphEdgeRow(BaseModel):
    __tablename__ = "aip_relationship_graph_edges"
    __table_args__ = (Index("ix_aip_rel_edges_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    edge_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    relation: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ConfidenceReportRow(BaseModel):
    __tablename__ = "aip_confidence_reports"
    __table_args__ = (Index("ix_aip_confidence_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    overall: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class VerificationHistoryRow(BaseModel):
    __tablename__ = "aip_verification_history"
    __table_args__ = (Index("ix_aip_verhist_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    field: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class FieldSourceRow(BaseModel):
    __tablename__ = "aip_field_sources"
    __table_args__ = (Index("ix_aip_field_sources_company", "company_key", "created_at"),)

    company_key: Mapped[str] = mapped_column(String(64), nullable=False)
    field: Mapped[str] = mapped_column(String(128), nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class IndustryBenchmarkRow(BaseModel):
    __tablename__ = "aip_industry_benchmarks"
    __table_args__ = (Index("ix_aip_benchmarks_industry", "industry", "created_at"),)

    industry: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
