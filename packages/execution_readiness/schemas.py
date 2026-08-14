"""API response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from execution_readiness.enums import ExecutionMode
from execution_readiness.models import ProviderSnapshot, ReadinessCheck, VERSION


class ExecutionStatusResponse(BaseModel):
    current_mode: ExecutionMode
    connected_providers: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    recommendation: str
    missing_requirements: list[str] = Field(default_factory=list)
    email_ready: bool = False
    whatsapp_ready: bool = False
    tracking_ready: bool = False
    followup_ready: bool = False
    communication_ready: bool = False
    reason: str = ""
    scoring_version: str = VERSION


class ExecutionReadinessResponse(BaseModel):
    execution_mode: ExecutionMode
    reason: str
    providers: list[ProviderSnapshot] = Field(default_factory=list)
    checks: list[ReadinessCheck] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    recommendation: str
    messages_sent: int = 0
    deliveries: int = 0
    open_tracking: str = "Disabled"
    reply_tracking: str = "Disabled"
    learning_mode: str = "Offline"
    scoring_version: str = VERSION


class ValidateResponse(BaseModel):
    execution_mode: ExecutionMode
    passed: bool
    checks: list[ReadinessCheck] = Field(default_factory=list)
    recommendation: str
    scoring_version: str = VERSION


class PlanningTargetCard(BaseModel):
    """Truthful next-action card when no delivery has occurred."""

    company: str
    status: str = "READY TO SEND"
    reason: str = "No communication provider connected."
    next_action: str = "Connect Gmail or Meta WhatsApp Business."
    tracking: str = "Disabled until first successful delivery."
    email: str | None = None
    why_now: str | None = None
