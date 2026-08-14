from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConversationChannel(StrEnum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    MEETING = "meeting"
    NOTE = "note"
    SYSTEM = "system"


class ConversationItemType(StrEnum):
    MESSAGE = "message"
    REPLY = "reply"
    MEETING = "meeting"
    ATTACHMENT = "attachment"
    NOTE = "note"
    INTERNAL_COMMENT = "internal_comment"
    AI_SUMMARY = "ai_summary"
    STATUS = "status"


class ConversationItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID | None = None
    conversation_id: UUID | None = None
    company_id: UUID
    opportunity_id: UUID | None = None
    campaign_id: UUID | None = None
    channel: ConversationChannel
    item_type: ConversationItemType
    direction: str = "outbound"
    subject: str | None = None
    body: str = ""
    from_address: str | None = None
    to_address: str | None = None
    provider_message_id: str | None = None
    thread_id: str | None = None
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    unread: bool = False
    pinned: bool = False
    occurred_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationThread(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID | None = None
    company_id: UUID
    opportunity_id: UUID | None = None
    campaign_id: UUID | None = None
    subject: str = ""
    participants: list[str] = Field(default_factory=list)
    channels: list[ConversationChannel] = Field(default_factory=list)
    unread_count: int = 0
    pinned: bool = False
    last_activity_at: datetime | None = None
    ai_summary: str | None = None
    items: list[ConversationItem] = Field(default_factory=list)


class ConversationFilter(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID | None = None
    channel: ConversationChannel | None = None
    unread_only: bool = False
    pinned_only: bool = False
    query: str | None = None
    limit: int = 50
    offset: int = 0
