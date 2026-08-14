from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class DecisionDiscoveryReport(BaseModel):
    __tablename__ = "decision_discovery_reports"
    __table_args__ = (
        Index("ix_decision_discovery_reports_company_created", "company_id", "created_at"),
        Index("ix_decision_discovery_reports_opportunity_created", "opportunity_id", "created_at"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    enrichment_report_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrichment_reports.id"), nullable=True
    )
    verification_report_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verification_reports.id"), nullable=True
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)
    business_pain: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_service: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_decision_maker_name: Mapped[str | None] = mapped_column(String(255))
    primary_decision_maker_role: Mapped[str | None] = mapped_column(String(128))
    secondary_decision_maker_name: Mapped[str | None] = mapped_column(String(255))
    secondary_decision_maker_role: Mapped[str | None] = mapped_column(String(128))
    buyer_match_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    overall_discovery_score: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    no_public_contact_message: Mapped[str | None] = mapped_column(Text)
    best_outreach_sequence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    source_attribution: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    report_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    processing_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class DecisionMaker(BaseModel):
    __tablename__ = "decision_makers"
    __table_args__ = (
        Index("ix_decision_makers_report_role", "discovery_report_id", "role"),
        Index("ix_decision_makers_company_role", "company_id", "role"),
    )

    discovery_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("decision_discovery_reports.id"), nullable=False
    )
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(128), nullable=False)
    normalized_role: Mapped[str] = mapped_column(String(128), nullable=False)
    department: Mapped[str | None] = mapped_column(String(128))
    seniority_rank: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    work_email: Mapped[str | None] = mapped_column(String(255))
    business_phone: Mapped[str | None] = mapped_column(String(64))
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_secondary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    buyer_match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[str] = mapped_column(Text, nullable=False, default="")


class CompanyDepartment(BaseModel):
    __tablename__ = "company_departments"
    __table_args__ = (Index("ix_company_departments_report_name", "discovery_report_id", "name"),)

    discovery_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("decision_discovery_reports.id"), nullable=False
    )
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    signal_strength: Mapped[float] = mapped_column(Float, nullable=False)
    headcount_signal: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[str] = mapped_column(Text, nullable=False, default="")


class CompanyContactChannel(BaseModel):
    __tablename__ = "company_contact_channels"
    __table_args__ = (
        Index("ix_company_contact_channels_report_rank", "discovery_report_id", "rank"),
        Index("ix_company_contact_channels_company_kind", "company_id", "kind"),
    )

    discovery_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("decision_discovery_reports.id"), nullable=False
    )
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str | None] = mapped_column(String(255))
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    is_verified_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    evidence: Mapped[str] = mapped_column(Text, nullable=False, default="")


class CompanyPublicProfile(BaseModel):
    __tablename__ = "company_public_profiles"
    __table_args__ = (Index("ix_company_public_profiles_report_platform", "discovery_report_id", "platform"),)

    discovery_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("decision_discovery_reports.id"), nullable=False
    )
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    handle: Mapped[str | None] = mapped_column(String(255))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)


class CompanyLeadership(BaseModel):
    __tablename__ = "company_leadership"
    __table_args__ = (Index("ix_company_leadership_report_title", "discovery_report_id", "title"),)

    discovery_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("decision_discovery_reports.id"), nullable=False
    )
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    department: Mapped[str | None] = mapped_column(String(128))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[str] = mapped_column(Text, nullable=False, default="")


class DecisionConfidence(BaseModel):
    __tablename__ = "decision_confidence"
    __table_args__ = (Index("ix_decision_confidence_report", "discovery_report_id"),)

    discovery_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("decision_discovery_reports.id"), nullable=False
    )
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    leadership_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    department_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    contact_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    buyer_match_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    overall_discovery_score: Mapped[float] = mapped_column(Float, nullable=False)


class DecisionHistory(BaseModel):
    __tablename__ = "decision_history"
    __table_args__ = (Index("ix_decision_history_company_created", "company_id", "created_at"),)

    discovery_report_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("decision_discovery_reports.id"), nullable=False
    )
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
