from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class OAuthConnection(BaseModel):
    __tablename__ = "oauth_connections"
    __table_args__ = (Index("ix_oauth_connections_provider_status", "provider", "status"),)

    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    account_email: Mapped[str | None] = mapped_column(String(255))
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ProviderSecret(BaseModel):
    __tablename__ = "provider_secrets"
    __table_args__ = (UniqueConstraint("provider", "secret_name", name="uq_provider_secrets_provider_secret_name"),)

    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    secret_name: Mapped[str] = mapped_column(String(128), nullable=False)
    secret_value_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class CommunicationMessage(BaseModel):
    __tablename__ = "communication_messages"
    __table_args__ = (
        Index("ix_communication_messages_campaign_state", "campaign_id", "state"),
        Index("ix_communication_messages_thread", "thread_id"),
    )

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    campaign_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    campaign_step_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False, default="outbound")
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    to_address: Mapped[str | None] = mapped_column(Text)
    from_address: Mapped[str | None] = mapped_column(Text)
    subject: Mapped[str | None] = mapped_column(Text)
    body_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body_html: Mapped[str | None] = mapped_column(Text)
    provider_message_id: Mapped[str | None] = mapped_column(String(255))
    thread_id: Mapped[str | None] = mapped_column(String(255))
    conversation_id: Mapped[str | None] = mapped_column(String(255))
    sandbox: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_code: Mapped[str | None] = mapped_column(String(128))
    error_message: Mapped[str | None] = mapped_column(Text)
    attachments: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class DeliveryEvent(BaseModel):
    __tablename__ = "delivery_events"
    __table_args__ = (Index("ix_delivery_events_campaign_occurred", "campaign_id", "occurred_at"),)

    message_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("communication_messages.id"))
    campaign_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WebhookEvent(BaseModel):
    __tablename__ = "webhook_events"
    __table_args__ = (Index("ix_webhook_events_provider_created", "provider", "created_at"),)

    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    signature_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text)


class CommunicationQueueItem(BaseModel):
    __tablename__ = "communication_queue_items"
    __table_args__ = (Index("ix_communication_queue_items_queue_available", "queue_name", "available_at"),)

    queue_name: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    last_error: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    idempotency_key: Mapped[str | None] = mapped_column(String(128))


class ConversationThreadRow(BaseModel):
    __tablename__ = "conversation_threads"
    __table_args__ = (Index("ix_conversation_threads_company_activity", "company_id", "last_activity_at"),)

    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    campaign_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    participants: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    channels: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    unread_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ConversationItemRow(BaseModel):
    __tablename__ = "conversation_items"
    __table_args__ = (Index("ix_conversation_items_conversation_occurred", "conversation_id", "occurred_at"),)

    conversation_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversation_threads.id"), nullable=False)
    company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opportunity_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    campaign_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    subject: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    from_address: Mapped[str | None] = mapped_column(Text)
    to_address: Mapped[str | None] = mapped_column(Text)
    provider_message_id: Mapped[str | None] = mapped_column(String(255))
    thread_id: Mapped[str | None] = mapped_column(String(255))
    attachments: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    unread: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SandboxScenario(BaseModel):
    __tablename__ = "sandbox_scenarios"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    steps: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="sandbox")


class QAHealthSnapshot(BaseModel):
    __tablename__ = "qa_health_snapshots"
    __table_args__ = (Index("ix_qa_health_snapshots_created", "created_at"),)

    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    components: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    recommendations: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)


class CampaignStopEvent(BaseModel):
    __tablename__ = "campaign_stop_events"

    campaign_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
