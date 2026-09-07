"""Shared types for COMAI partner outreach."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


PIPELINE_STAGES = (
    "uploaded",
    "drafted",
    "queued",
    "sent",
    "replied",
    "interested",
    "meeting",
    "partner_onboarded",
    "nurture",
    "lost",
    "bounced",
    "unsubscribed",
    "failed",
    "skipped",
)

SEQUENCE_STEPS = ("intro", "fu1", "fu2", "final", "manual")

CAMPAIGN_STATUSES = (
    "validating",
    "drafting",
    "sending",
    "paused",
    "completed",
    "killed",
)


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def new_id() -> str:
    return str(uuid4())


@dataclass
class PartnerLead:
    id: str
    campaign_id: str
    email: str
    first_name: str = ""
    last_name: str = ""
    agency_name: str = ""
    agency_type: str = ""
    website: str = ""
    domain: str = ""
    city: str = ""
    phone: str = ""
    services: str = ""
    notes: str = ""
    linkedin_url: str = ""
    client_examples: str = ""
    stage: str = "uploaded"
    sequence_step: str = ""
    next_followup_at: str | None = None
    stop_reason: str | None = None
    subject: str = ""
    body_text: str = ""
    body_html: str = ""
    last_sent_at: str | None = None
    reply_class: str | None = None
    reply_snippet: str = ""
    send_attempts: int = 0
    error: str = ""
    row_index: int = 0
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PartnerLead:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class PartnerMessage:
    id: str
    campaign_id: str
    lead_id: str
    direction: str  # outbound | inbound
    step: str
    subject: str = ""
    body_text: str = ""
    body_html: str = ""
    delivery_state: str = "draft"
    provider_message_id: str = ""
    thread_id: str = ""
    reply_class: str = ""
    created_at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PartnerMessage:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class PartnerEvent:
    id: str
    campaign_id: str
    lead_id: str | None
    event_type: str
    detail: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PartnerEvent:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class PartnerCampaign:
    id: str
    name: str
    status: str = "validating"
    kill_flag: bool = False
    config_snapshot: dict[str, Any] = field(default_factory=dict)
    video_url: str = ""
    total_rows: int = 0
    valid_rows: int = 0
    skipped_rows: int = 0
    drafted: int = 0
    queued: int = 0
    sent: int = 0
    failed: int = 0
    replied: int = 0
    row_errors: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PartnerCampaign:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})
