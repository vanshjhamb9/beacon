from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ClientProfile(BaseModel):
    __tablename__ = "client_profiles"
    __table_args__ = (
        Index("ix_aep_profiles_company_created", "company_id", "created_at"),
        Index("ix_aep_profiles_stage", "stage"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    contract_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    health_status: Mapped[str] = mapped_column(String(32), nullable=False, default="healthy")
    overall_health: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="aep-v1")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ClientProject(BaseModel):
    __tablename__ = "client_projects"
    __table_args__ = (Index("ix_aep_projects_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    profile_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("client_profiles.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str | None] = mapped_column(String(64))
    blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    at_risk: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class ClientHealthSnapshot(BaseModel):
    __tablename__ = "client_health_snapshots"
    __table_args__ = (Index("ix_aep_health_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    profile_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("client_profiles.id"))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    overall_health: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    renewal_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    upsell_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class ClientMemoryRow(BaseModel):
    __tablename__ = "client_memory"
    __table_args__ = (
        Index("ix_aep_memory_company_created", "company_id", "created_at"),
        Index("ix_aep_memory_type", "record_type"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    profile_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("client_profiles.id"))
    record_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    searchable_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ClientHandoffRow(BaseModel):
    __tablename__ = "client_handoffs"
    __table_args__ = (Index("ix_aep_handoffs_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    profile_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("client_profiles.id"))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class UpsellRecommendationRow(BaseModel):
    __tablename__ = "upsell_recommendations"
    __table_args__ = (
        Index("ix_aep_upsells_company_created", "company_id", "created_at"),
        Index("ix_aep_upsells_rec_id", "recommendation_id"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    profile_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("client_profiles.id"))
    recommendation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    service: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    requires_founder_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    modifies_production: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_approval")
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[str | None] = mapped_column(String(128))


class RenewalPredictionRow(BaseModel):
    __tablename__ = "renewal_predictions"
    __table_args__ = (Index("ix_aep_renewals_company_created", "company_id", "created_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    profile_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("client_profiles.id"))
    renewal_date: Mapped[str | None] = mapped_column(String(64))
    probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class DeliverySnapshot(BaseModel):
    __tablename__ = "delivery_snapshots"
    __table_args__ = (Index("ix_aep_delivery_created", "created_at"),)

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    founder_view: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="aep-v1")
