"""SQLAlchemy models for COMAI Partner Outreach."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ComaiPartnerCampaign(BaseModel):
    __tablename__ = "comai_partner_campaigns"
    __table_args__ = (Index("ix_comai_partner_campaigns_status", "status"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="validating")
    kill_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    config_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    video_url: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    drafted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    queued: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    replied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    row_errors: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


class ComaiPartnerLead(BaseModel):
    __tablename__ = "comai_partner_leads"
    __table_args__ = (
        Index("ix_comai_partner_leads_campaign_id", "campaign_id"),
        Index("ix_comai_partner_leads_email", "email"),
        Index("ix_comai_partner_leads_stage", "stage"),
        Index("ix_comai_partner_leads_next_followup_at", "next_followup_at"),
    )

    campaign_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, default="")
    first_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    last_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    agency_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    agency_type: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    website: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    domain: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    services: Mapped[str] = mapped_column(Text, nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    linkedin_url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    client_examples: Mapped[str] = mapped_column(Text, nullable=False, default="")
    stage: Mapped[str] = mapped_column(String(64), nullable=False, default="uploaded")
    sequence_step: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    next_followup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stop_reason: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    subject: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    body_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body_html: Mapped[str] = mapped_column(Text, nullable=False, default="")
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reply_class: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    reply_snippet: Mapped[str] = mapped_column(Text, nullable=False, default="")
    send_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    row_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ComaiPartnerMessage(BaseModel):
    __tablename__ = "comai_partner_messages"
    __table_args__ = (
        Index("ix_comai_partner_messages_campaign_id", "campaign_id"),
        Index("ix_comai_partner_messages_lead_id", "lead_id"),
        Index("ix_comai_partner_messages_direction", "direction"),
    )

    campaign_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    lead_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False, default="outbound")
    step: Mapped[str] = mapped_column(String(32), nullable=False, default="intro")
    subject: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    body_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body_html: Mapped[str] = mapped_column(Text, nullable=False, default="")
    delivery_state: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    provider_message_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    thread_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    reply_class: Mapped[str] = mapped_column(String(64), nullable=False, default="")


class ComaiPartnerEvent(BaseModel):
    __tablename__ = "comai_partner_events"
    __table_args__ = (
        Index("ix_comai_partner_events_campaign_id", "campaign_id"),
        Index("ix_comai_partner_events_event_type", "event_type"),
    )

    campaign_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    lead_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
