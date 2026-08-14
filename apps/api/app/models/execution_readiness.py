from typing import Any

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CommunicationProviderStatus(BaseModel):
    __tablename__ = "communication_provider_status"

    organization_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    oauth_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_sync: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    webhook_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_send: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_receive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ExecutionStatusRow(BaseModel):
    __tablename__ = "execution_status"

    organization_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    execution_mode: Mapped[str] = mapped_column(String(32), default="PLANNING", nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    communication_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    whatsapp_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tracking_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    followup_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
