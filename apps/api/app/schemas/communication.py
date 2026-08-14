from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CommunicationModeResponse(BaseModel):
    mode: str
    allow_production_send: bool
    sandbox: bool
    queues: dict[str, Any]


class SandboxSendRequest(BaseModel):
    channel: str = "email"
    to_address: str = "sandbox@example.com"
    subject: str | None = "Beacon sandbox outreach"
    body_text: str = "Hello from Beacon sandbox."
    body_html: str | None = None
    simulated_reply: str = "Thanks — interested in a meeting."
    campaign_id: UUID | None = None
    company_id: UUID | None = None
    opportunity_id: UUID | None = None


class FounderSendRequest(BaseModel):
    channel: str = "email"
    to_address: str
    subject: str | None = "Beacon outreach"
    body_text: str
    body_html: str | None = None
    campaign_id: UUID | None = None
    campaign_step_id: UUID | None = None
    company_id: UUID | None = None
    opportunity_id: UUID | None = None
    from_address: str | None = None
    idempotency_key: str | None = None
    simulate_reply: bool = True
    force_sandbox: bool | None = None
    simulated_reply: str = "Thanks — interested in a meeting."
    actor: str = "founder"


class CampaignExecuteRequest(BaseModel):
    to_address: str
    subject: str | None = None
    body_text: str | None = None
    body_html: str | None = None
    channel: str | None = None
    company_id: UUID | None = None
    opportunity_id: UUID | None = None
    simulate_reply: bool = True
    force_sandbox: bool | None = None
    actor: str = "founder"


class E2EApproveSendReplyRequest(BaseModel):
    campaign_id: UUID | None = None
    company_id: UUID | None = None
    opportunity_id: UUID | None = None
    to_address: str = "prospect@sandbox.example"
    subject: str = "Beacon founder outreach"
    body_text: str = "Personalized founder email"



class SandboxMeetingRequest(BaseModel):
    title: str = "Beacon meeting"
    description: str = ""
    start_at: datetime | None = None
    end_at: datetime | None = None
    timezone: str = "UTC"
    attendees: list[str] = Field(default_factory=list)
    campaign_id: UUID | None = None
    company_id: UUID | None = None
    opportunity_id: UUID | None = None


class OAuthAuthorizeRequest(BaseModel):
    provider: str
    state: str = "beacon"


class OAuthAuthorizeResponse(BaseModel):
    authorize_url: str
    provider: str
    state: str


class InboxThreadResponse(BaseModel):
    id: str
    company_id: str
    subject: str
    unread_count: int
    pinned: bool
    channels: list[Any]
    ai_summary: str | None = None
    last_activity_at: str | None = None


class ConversationItemResponse(BaseModel):
    id: str
    channel: str
    item_type: str
    direction: str
    subject: str | None = None
    body: str
    from_address: str | None = None
    to_address: str | None = None
    unread: bool
    occurred_at: str


class SystemHealthResponse(BaseModel):
    overall_score: float
    status: str
    mode: str
    components: list[dict[str, Any]]
    recommendations: list[str]


class E2ERunResponse(BaseModel):
    scenario: str
    passed: bool
    mode: str
    steps: list[dict[str, Any]]
    duration_ms: float | None = None


class WebhookIngestResponse(BaseModel):
    accepted: bool
    events: int
    signature_valid: bool


class QueueHealthResponse(BaseModel):
    mode: str
    allow_production_send: bool
    sandbox: bool
    depths: dict[str, int]
    stopped_campaigns: int


class CampaignStopRequest(BaseModel):
    reason: str = "manual_stop"
    actor: str = "operator"
