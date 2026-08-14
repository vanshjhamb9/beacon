from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CampaignTemplate(BaseModel):
    __tablename__ = "campaign_templates"
    __table_args__ = (Index("ix_campaign_templates_channel_style", "channel", "style"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(64), nullable=False)
    style: Mapped[str] = mapped_column(String(64), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False, default="v1")


class CampaignChannel(BaseModel):
    __tablename__ = "campaign_channels"
    __table_args__ = (UniqueConstraint("kind", name="uq_campaign_channels_kind"),)

    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    supports_async: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    supports_attachments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_daily_sends: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    min_gap_hours: Mapped[float] = mapped_column(Float, nullable=False, default=24.0)
    business_hours_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    constraints: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    delivery_ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class Campaign(BaseModel):
    __tablename__ = "campaigns"
    __table_args__ = (
        Index("ix_campaigns_company_created", "company_id", "created_at"),
        Index("ix_campaigns_status_priority", "status", "priority"),
        Index("ix_campaigns_opportunity_created", "opportunity_id", "created_at"),
    )

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False)
    sales_package_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_packages.id"))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="needs_review")
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    primary_channel: Mapped[str] = mapped_column(String(64), nullable=False)
    secondary_channel: Mapped[str | None] = mapped_column(String(64))
    follow_up_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delay_hours_between_messages: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    expected_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    channel_choice_reason: Mapped[str] = mapped_column(Text, nullable=False)
    timing_reason: Mapped[str] = mapped_column(Text, nullable=False)
    message_selection_reason: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_service: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    business_pain: Mapped[str] = mapped_column(Text, nullable=False, default="")
    buyer_persona: Mapped[str | None] = mapped_column(String(128))
    industry: Mapped[str | None] = mapped_column(String(128))
    communication_style: Mapped[str] = mapped_column(String(64), nullable=False, default="professional")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    schedule_rules: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    quality: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    plan_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class CampaignStep(BaseModel):
    __tablename__ = "campaign_steps"
    __table_args__ = (Index("ix_campaign_steps_campaign_sequence", "campaign_id", "sequence"),)

    campaign_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[str] = mapped_column(String(64), nullable=False)
    delay_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    draft_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    draft_style: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_preview: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body_preview: Mapped[str] = mapped_column(Text, nullable=False, default="")
    message_selection_reason: Mapped[str] = mapped_column(Text, nullable=False)
    timing_reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned")
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    sales_draft_ref: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class CampaignSchedule(BaseModel):
    __tablename__ = "campaign_schedules"
    __table_args__ = (
        Index("ix_campaign_schedules_planned", "planned_at", "status"),
        Index("ix_campaign_schedules_campaign", "campaign_id", "planned_at"),
    )

    campaign_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    campaign_step_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campaign_steps.id"))
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    planned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned")
    rules_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    timing_reason: Mapped[str] = mapped_column(Text, nullable=False)


class CampaignApproval(BaseModel):
    __tablename__ = "campaign_approvals"
    __table_args__ = (Index("ix_campaign_approvals_campaign_created", "campaign_id", "created_at"),)

    campaign_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class CampaignExecutionLog(BaseModel):
    __tablename__ = "campaign_execution_logs"
    __table_args__ = (Index("ix_campaign_execution_logs_campaign_created", "campaign_id", "created_at"),)

    campaign_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    campaign_step_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campaign_steps.id"))
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="none")
    delivery_attempted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class CampaignAudit(BaseModel):
    __tablename__ = "campaign_audit"
    __table_args__ = (
        Index("ix_campaign_audit_campaign_created", "campaign_id", "created_at"),
        Index("ix_campaign_audit_company_created", "company_id", "created_at"),
    )

    campaign_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    before_state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    after_state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
