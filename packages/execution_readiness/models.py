"""Pydantic domain models for execution readiness (not ORM)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from execution_readiness.enums import ExecutionMode, ProviderKind

VERSION = "er-v1"
DEFAULT_ORG_ID = "00000000-0000-4000-8000-000000000001"


class ProviderSnapshot(BaseModel):
    provider: ProviderKind
    connected: bool = False
    oauth_valid: bool = False
    webhook_verified: bool = False
    can_send: bool = False
    can_receive: bool = False
    last_sync: str | None = None
    detail: str = ""


class ReadinessCheck(BaseModel):
    name: str
    passed: bool
    detail: str = ""


class ExecutionStatusSnapshot(BaseModel):
    organization_id: str = DEFAULT_ORG_ID
    execution_mode: ExecutionMode = ExecutionMode.PLANNING
    reason: str = "No verified communication provider connected."
    communication_ready: bool = False
    email_ready: bool = False
    whatsapp_ready: bool = False
    tracking_ready: bool = False
    followup_ready: bool = False
    providers: list[ProviderSnapshot] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    recommendation: str = "Connect Gmail or Meta WhatsApp Business to begin outreach."
    messages_sent: int = 0
    deliveries: int = 0
    open_tracking: str = "Disabled"
    reply_tracking: str = "Disabled"
    learning_mode: str = "Offline"
    scoring_version: str = VERSION


class VerifiedDelivery(BaseModel):
    company_id: str | None = None
    message_id: str | None = None
    provider: str | None = None
    delivered_at: str | None = None
