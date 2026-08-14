"""Standard evidence event emitted by every opportunity connector.

No connector-specific schemas. Every connector emits exactly one schema.
No connector may fabricate companies, people, emails, or domains.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


SUPPORTED_EVENT_TYPES: tuple[str, ...] = (
    "Hiring",
    "Funding",
    "Expansion",
    "New Office",
    "Technology Adoption",
    "Migration",
    "Product Launch",
    "Compliance",
    "Procurement",
    "Executive Hire",
    "Partnership",
    "Customer Win",
    "Pricing Change",
    "Acquisition",
    "Security Incident",
    "Infrastructure Upgrade",
    "Hiring Freeze",
    "Layoffs",
    "API Release",
    "SDK Release",
    "Marketplace Listing",
    "Press Release",
    "Conference",
    "Award",
    "Patent",
    "Government Tender",
    "Developer Activity",
    "Community Growth",
)

SUPPORTED_CATEGORIES: tuple[str, ...] = (
    "Identity",
    "Conversation",
    "Intent",
    "Technology",
    "Enrichment",
)


class EvidenceEvent(BaseModel):
    """Connector-agnostic attribution payload; no company/opportunity creation."""

    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    connector_id: str = Field(min_length=1)
    connector_version: str = Field(min_length=1)
    company_name: str | None = None
    headline: str = Field(min_length=1)
    summary: str = ""
    event_type: str = Field(min_length=1)
    event_category: str = Field(min_length=1)
    url: str | None = None
    published_at: datetime
    captured_at: datetime
    country: str | None = None
    language: str = "unknown"
    confidence: float = Field(default=0.0, ge=0, le=100)
    evidence: str = Field(min_length=1)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)
    collector: str = Field(min_length=1)


class RoutedEvidenceEvent(BaseModel):
    """Event after routing — accepted or rejected with reason."""

    model_config = ConfigDict(frozen=True)

    event: EvidenceEvent
    accepted: bool
    rejection_reason: str | None = None
    route: str = "live_opportunity_discovery"
    routed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EventBatch(BaseModel):
    """Batch of events from a single connector run."""

    model_config = ConfigDict(frozen=True)

    connector_id: str
    connector_version: str
    events: tuple[EvidenceEvent, ...] = ()
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    total_collected: int = 0
    total_accepted: int = 0
    total_rejected: int = 0
