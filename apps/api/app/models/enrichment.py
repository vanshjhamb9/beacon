from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class EnrichedCompanyProfile(BaseModel):
    """Sales-ready company profile snapshot.

    Named distinctly from Context Engine `company_profiles` (Company DNA).
    """

    __tablename__ = "enriched_company_profiles"
    __table_args__ = (
        Index("ix_enriched_company_profiles_company_created", "company_id", "created_at"),
        Index("ix_enriched_company_profiles_opportunity", "opportunity_id"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    enrichment_report_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("enrichment_reports.id"))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(String(512))
    domain: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(128))
    sub_industry: Mapped[str | None] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(128))
    founded_year: Mapped[int | None] = mapped_column(Integer)
    employee_count_estimate: Mapped[int | None] = mapped_column(Integer)
    company_size_range: Mapped[str | None] = mapped_column(String(64))
    revenue_estimate: Mapped[str | None] = mapped_column(String(128))
    field_attributions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class CompanyContact(BaseModel):
    __tablename__ = "company_contacts"
    __table_args__ = (Index("ix_company_contacts_company_kind", "company_id", "kind"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    enrichment_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrichment_reports.id"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[str] = mapped_column(String(512), nullable=False)
    label: Mapped[str | None] = mapped_column(String(128))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024))
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CompanyPerson(BaseModel):
    __tablename__ = "company_people"
    __table_args__ = (Index("ix_company_people_company_role", "company_id", "role"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    enrichment_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrichment_reports.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(128), nullable=False)
    department: Mapped[str | None] = mapped_column(String(128))
    linkedin_url: Mapped[str | None] = mapped_column(String(1024))
    work_email: Mapped[str | None] = mapped_column(String(320))
    business_phone: Mapped[str | None] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024))


class CompanySocialProfile(BaseModel):
    __tablename__ = "company_social_profiles"
    __table_args__ = (Index("ix_company_social_profiles_company_platform", "company_id", "platform"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    enrichment_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrichment_reports.id"), nullable=False
    )
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    handle: Mapped[str | None] = mapped_column(String(255))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)


class CompanyTechnology(BaseModel):
    __tablename__ = "company_technologies"
    __table_args__ = (Index("ix_company_technologies_company_name", "company_id", "name"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    enrichment_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrichment_reports.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024))
    signal: Mapped[str | None] = mapped_column(String(255))


class CompanyTeamInsight(BaseModel):
    __tablename__ = "company_team_insights"
    __table_args__ = (Index("ix_company_team_insights_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    enrichment_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrichment_reports.id"), nullable=False
    )
    leadership_team_size: Mapped[int | None] = mapped_column(Integer)
    engineering_team_estimate: Mapped[int | None] = mapped_column(Integer)
    support_team_estimate: Mapped[int | None] = mapped_column(Integer)
    operations_team_estimate: Mapped[int | None] = mapped_column(Integer)
    recent_hires: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    open_positions: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    hiring_trends: Mapped[str | None] = mapped_column(Text)
    attributions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)


class CompanyJob(BaseModel):
    __tablename__ = "company_jobs"
    __table_args__ = (Index("ix_company_jobs_company_title", "company_id", "title"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    enrichment_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrichment_reports.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(128))
    location: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(1024))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024))


class CompanyEnrichmentHistory(BaseModel):
    __tablename__ = "company_enrichment_history"
    __table_args__ = (Index("ix_company_enrichment_history_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    enrichment_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrichment_reports.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class EnrichmentSource(BaseModel):
    __tablename__ = "enrichment_sources"
    __table_args__ = (Index("ix_enrichment_sources_report_source", "enrichment_report_id", "source"),)

    enrichment_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrichment_reports.id"), nullable=False
    )
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024))
    fields: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    licensed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)


class EnrichmentReport(BaseModel):
    __tablename__ = "enrichment_reports"
    __table_args__ = (
        Index("ix_enrichment_reports_company_created", "company_id", "created_at"),
        Index("ix_enrichment_reports_opportunity_created", "opportunity_id", "created_at"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)
    business_pain: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_service: Mapped[str] = mapped_column(String(255), nullable=False)
    buyer_persona: Mapped[str] = mapped_column(String(128), nullable=False)
    estimated_budget: Mapped[str | None] = mapped_column(String(128))
    priority: Mapped[str | None] = mapped_column(String(32))
    why_now: Mapped[str] = mapped_column(Text, nullable=False)
    best_outreach_angle: Mapped[str] = mapped_column(Text, nullable=False)
    profile_completeness: Mapped[float] = mapped_column(Float, nullable=False)
    contact_availability: Mapped[float] = mapped_column(Float, nullable=False)
    technology_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    decision_maker_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    overall_enrichment_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_chain: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    lead_profile: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    processing_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
