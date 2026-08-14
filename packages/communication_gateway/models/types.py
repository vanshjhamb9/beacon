from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CommunicationMode(StrEnum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class ProviderName(StrEnum):
    SANDBOX_EMAIL = "sandbox_email"
    GMAIL = "gmail"
    MICROSOFT_GRAPH = "microsoft_graph"
    SMTP = "smtp"
    SANDBOX_WHATSAPP = "sandbox_whatsapp"
    META_WHATSAPP = "meta_whatsapp"
    SANDBOX_CALENDAR = "sandbox_calendar"
    GOOGLE_CALENDAR = "google_calendar"
    OUTLOOK_CALENDAR = "outlook_calendar"
    CALENDLY = "calendly"
    REDDIT = "reddit"
    INDIEHACKERS = "indiehackers"
    PRODUCTHUNT = "producthunt"
    SANDBOX_REDDIT = "sandbox_reddit"
    SANDBOX_INDIEHACKERS = "sandbox_indiehackers"
    SANDBOX_PRODUCTHUNT = "sandbox_producthunt"


class ChannelType(StrEnum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    CALENDAR = "calendar"
    REDDIT = "reddit"
    INDIEHACKERS = "indiehackers"
    PRODUCTHUNT = "producthunt"


class DeliveryState(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    CLICKED = "clicked"
    REPLIED = "replied"
    MEETING = "meeting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueueName(StrEnum):
    OUTGOING = "outgoing"
    RETRY = "retry"
    DEAD_LETTER = "dead_letter"
    PRIORITY = "priority"
    DELAYED = "delayed"
    WORKER = "worker"


class StopReason(StrEnum):
    REPLY_RECEIVED = "reply_received"
    MEETING_BOOKED = "meeting_booked"
    CAMPAIGN_CANCELLED = "campaign_cancelled"
    MANUAL_STOP = "manual_stop"


class Attachment(BaseModel):
    model_config = ConfigDict(frozen=True)

    filename: str
    content_type: str = "application/octet-stream"
    size_bytes: int = 0
    content_base64: str | None = None
    url: str | None = None


class OutboundMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    channel: ChannelType
    provider: ProviderName
    to_address: str
    from_address: str | None = None
    subject: str | None = None
    body_text: str = ""
    body_html: str | None = None
    thread_id: str | None = None
    conversation_id: str | None = None
    campaign_id: UUID | None = None
    campaign_step_id: UUID | None = None
    company_id: UUID | None = None
    opportunity_id: UUID | None = None
    attachments: list[Attachment] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    priority: int = 100
    scheduled_at: datetime | None = None
    is_draft: bool = False
    idempotency_key: str | None = None
    require_campaign_approved: bool = False
    campaign_approved: bool = False


class DeliveryResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    state: DeliveryState
    provider: ProviderName
    provider_message_id: str | None = None
    thread_id: str | None = None
    conversation_id: str | None = None
    sandbox: bool = True
    error_code: str | None = None
    error_message: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class InboundEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    channel: ChannelType
    provider: ProviderName
    event_type: str
    provider_message_id: str | None = None
    thread_id: str | None = None
    conversation_id: str | None = None
    from_address: str | None = None
    to_address: str | None = None
    subject: str | None = None
    body_text: str = ""
    occurred_at: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class OAuthTokenBundle(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: ProviderName
    access_token: str
    refresh_token: str | None = None
    expires_at: datetime | None = None
    scopes: list[str] = Field(default_factory=list)
    account_email: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CalendarEventRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    description: str = ""
    start_at: datetime
    end_at: datetime
    timezone: str = "UTC"
    attendees: list[str] = Field(default_factory=list)
    location: str | None = None
    campaign_id: UUID | None = None
    company_id: UUID | None = None
    opportunity_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CalendarBookingResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: ProviderName
    event_id: str
    meeting_url: str | None = None
    status: str = "booked"
    sandbox: bool = True
    raw: dict[str, Any] = Field(default_factory=dict)


class GatewayConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: CommunicationMode = CommunicationMode.SANDBOX
    allow_production_send: bool = False
    encryption_key: str | None = None
    gmail_client_id: str | None = None
    gmail_client_secret: str | None = None
    microsoft_client_id: str | None = None
    microsoft_client_secret: str | None = None
    microsoft_tenant_id: str = "common"
    meta_whatsapp_token: str | None = None
    meta_whatsapp_phone_number_id: str | None = None
    meta_whatsapp_business_account_id: str | None = None
    meta_whatsapp_app_secret: str | None = None
    meta_whatsapp_verify_token: str | None = None
    calendly_api_key: str | None = None
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str = "BeaconOutreach/1.0"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_from_address: str | None = None
    indiehackers_username: str | None = None
    indiehackers_password: str | None = None
    producthunt_api_key: str | None = None
    oauth_redirect_uri: str = "http://localhost:8000/api/v1/communication/oauth/callback"
    daily_email_quota: int = 500
    daily_reddit_quota: int = 15
    daily_indiehackers_quota: int = 10
    daily_producthunt_quota: int = 5
    max_retries: int = 5
