"""Typed domain models for Beacon Intelligence Center."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class DiscoveryEventType(StrEnum):
    SIGNAL_COLLECTED = "Signal Collected"
    DUPLICATE_REMOVED = "Duplicate Removed"
    WEBSITE_VERIFIED = "Website Verified"
    EMAIL_FOUND = "Email Found"
    DECISION_MAKER_FOUND = "Decision Maker Found"
    REVENUE_READY = "Revenue Ready"
    OUTREACH_STARTED = "Outreach Started"
    REPLY_RECEIVED = "Reply Received"
    MEETING_BOOKED = "Meeting Booked"
    LOST = "Lost"
    WON = "Won"
    SALES_READY = "Sales Ready"
    IDENTITY_VERIFIED = "Identity Verified"


JOURNEY_STAGES: tuple[str, ...] = (
    "signal",
    "identity",
    "website",
    "email",
    "decision_maker",
    "sales_ready",
    "revenue_ready",
    "outreach",
    "reply",
    "meeting",
    "proposal",
    "won",
    "lost",
)

STAGE_LABELS: dict[str, str] = {
    "signal": "Collected",
    "identity": "Identity",
    "website": "Website",
    "email": "Email",
    "decision_maker": "Decision Maker",
    "sales_ready": "Sales Ready",
    "revenue_ready": "Revenue Ready",
    "outreach": "Outreach",
    "reply": "Reply",
    "meeting": "Meeting",
    "proposal": "Proposal",
    "won": "Won",
    "lost": "Lost",
}


@dataclass(slots=True)
class DiscoveryCard:
    id: str
    event_type: str
    timestamp: datetime
    collector: str | None = None
    connector: str | None = None
    company_id: str | None = None
    company_name: str | None = None
    industry: str | None = None
    status: str | None = None
    headline: str = ""
    detail: str = ""
    score: float | None = None
    is_error: bool = False
    is_revenue_ready: bool = False
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JourneyStage:
    stage: str
    label: str
    status: str  # completed | pending | failed | skipped
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    connector: str | None = None
    worker: str | None = None
    evidence: list[str] = field(default_factory=list)
    retry_count: int = 0
    failures: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass(slots=True)
class CompanyJourney:
    company_id: str
    company_name: str
    industry: str | None
    stages: list[JourneyStage]
    current_stage: str
    pipeline_health: list[dict[str, Any]]
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class ConnectorRoiRow:
    connector: str
    healthy: bool
    signals: int = 0
    companies: int = 0
    emails: int = 0
    decision_makers: int = 0
    revenue_ready: int = 0
    meetings: int = 0
    wins: int = 0
    win_pct: float = 0.0
    latency_ms: float = 0.0
    api_cost: float = 0.0
    quota_used_pct: float = 0.0
    success_pct: float = 0.0
    detail: str = ""


@dataclass(slots=True)
class DatasetStatistics:
    signals_collected: int = 0
    duplicates: int = 0
    spam: int = 0
    dead_websites: int = 0
    working_websites: int = 0
    emails_found: int = 0
    verified_emails: int = 0
    generic_emails: int = 0
    founder_emails: int = 0
    decision_makers: int = 0
    revenue_ready: int = 0
    outreach_ready: int = 0
    duplicate_rate: float = 0.0
    spam_rate: float = 0.0
    verification_rate: float = 0.0
    enrichment_coverage: float = 0.0


@dataclass(slots=True)
class ReplayFrame:
    hour: str
    timestamp: datetime
    signals: int = 0
    companies: int = 0
    websites: int = 0
    emails: int = 0
    decision_makers: int = 0
    sales_ready: int = 0
    revenue_ready: int = 0
    contacted: int = 0
    movements: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class HeatmapCell:
    stage: str
    tone: str  # green | yellow | red
    count: int = 0
    success_pct: float = 0.0
    avg_duration: float = 0.0
    failures: int = 0


# Deterministic estimated API cost per successful record (USD). Free connectors = 0.
CONNECTOR_UNIT_COST: dict[str, float] = {
    "github_trending": 0.0,
    "product_hunt": 0.0,
    "hacker_news": 0.0,
    "reddit": 0.0,
    "rss": 0.0,
    "indie_hackers": 0.0,
    "devto": 0.0,
    "sec_edgar": 0.0,
    "yc": 0.0,
    "app_store": 0.0,
    "google_play": 0.0,
    "hunter": 0.025,
    "apollo": 0.045,
    "linkedin": 0.08,
    "people_data_labs": 0.05,
    "clearbit": 0.06,
    "crunchbase": 0.03,
    "builtwith": 0.02,
    "wappalyzer": 0.015,
    "google_maps": 0.01,
}
