from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SalesPromptVersion(BaseModel):
    __tablename__ = "sales_prompt_versions"
    __table_args__ = (Index("ix_sales_prompt_versions_active", "is_active", "created_at"),)

    version: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)
    model_hint: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_hint: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SalesTemplate(BaseModel):
    __tablename__ = "sales_templates"
    __table_args__ = (Index("ix_sales_templates_kind_style", "kind", "style"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    style: Mapped[str] = mapped_column(String(64), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False, default="v1")


class SalesPackage(BaseModel):
    __tablename__ = "sales_packages"
    __table_args__ = (
        Index("ix_sales_packages_company_created", "company_id", "created_at"),
        Index("ix_sales_packages_opportunity_version", "opportunity_id", "version"),
        Index("ix_sales_packages_review_status", "review_status", "created_at"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommended_service: Mapped[str] = mapped_column(String(255), nullable=False)
    business_pain: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    llm_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    llm_model: Mapped[str] = mapped_column(String(128), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    generation_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cost_estimate_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    quality_scores: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    sections: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    style_variants: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    evidence_chain: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    package_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SalesDraft(BaseModel):
    __tablename__ = "sales_drafts"
    __table_args__ = (Index("ix_sales_drafts_package_kind_style", "package_id", "kind", "style"),)

    package_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_packages.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    style: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    subject_lines: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    attribution: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SalesGenerationLog(BaseModel):
    __tablename__ = "sales_generation_logs"
    __table_args__ = (Index("ix_sales_generation_logs_company_created", "company_id", "created_at"),)

    package_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_packages.id"))
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    llm_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    llm_model: Mapped[str] = mapped_column(String(128), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    generation_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cost_estimate_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="succeeded")
    error_message: Mapped[str | None] = mapped_column(Text)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    response_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SalesFeedback(BaseModel):
    __tablename__ = "sales_feedback"
    __table_args__ = (Index("ix_sales_feedback_package_created", "package_id", "created_at"),)

    package_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_packages.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(128), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rating: Mapped[float | None] = mapped_column(Float)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SalesVersion(BaseModel):
    __tablename__ = "sales_versions"
    __table_args__ = (
        Index("ix_sales_versions_company_version", "company_id", "version"),
        UniqueConstraint("opportunity_id", "version", name="uq_sales_versions_opportunity_id_version"),
    )

    package_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_packages.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    change_reason: Mapped[str] = mapped_column(String(255), nullable=False, default="generated")
