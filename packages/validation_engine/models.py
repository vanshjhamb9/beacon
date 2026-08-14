"""Typed domain models for Beacon Validation & Continuous Learning Platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ValidationEvent:
    event_id: str
    company_id: str
    stage: str
    timestamp: datetime
    evidence: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    confidence: float = 1.0


@dataclass(slots=True)
class TimelineEntry:
    stage: str
    timestamp: datetime
    evidence: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    duration_seconds: float | None = None


@dataclass(slots=True)
class ReplyEvent:
    company_id: str
    reply_type: str
    timestamp: datetime
    evidence: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    confidence: float = 1.0
    reply_time_seconds: float | None = None


@dataclass(slots=True)
class MeetingEvent:
    company_id: str
    meeting_type: str
    timestamp: datetime
    duration_minutes: float | None = None
    calendar_link: str = ""
    notes: str = ""
    next_action: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProposalEvent:
    company_id: str
    status: str
    timestamp: datetime
    value: float | None = None
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DealEvent:
    company_id: str
    status: str
    revenue: float
    expected_revenue: float = 0.0
    close_date: datetime | None = None
    service_sold: str = ""
    reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ObjectionEvent:
    company_id: str
    category: str
    timestamp: datetime
    evidence: dict[str, Any] = field(default_factory=dict)
    industry: str = ""
    service: str = ""
    connector: str = ""
    persona: str = ""


@dataclass(slots=True)
class ConnectorRoi:
    connector: str
    signals: int = 0
    companies: int = 0
    revenue_ready: int = 0
    replies: int = 0
    meetings: int = 0
    deals: int = 0
    revenue: float = 0.0
    reply_rate: float = 0.0
    meeting_rate: float = 0.0
    win_rate: float = 0.0


@dataclass(slots=True)
class IndustryRoi:
    industry: str
    companies: int = 0
    revenue_ready: int = 0
    replies: int = 0
    meetings: int = 0
    deals: int = 0
    revenue: float = 0.0
    reply_rate: float = 0.0
    meeting_rate: float = 0.0
    win_rate: float = 0.0


@dataclass(slots=True)
class ServiceRoi:
    service: str
    companies: int = 0
    replies: int = 0
    meetings: int = 0
    deals: int = 0
    revenue: float = 0.0
    reply_rate: float = 0.0
    meeting_rate: float = 0.0
    proposal_rate: float = 0.0
    win_rate: float = 0.0


@dataclass(slots=True)
class PersonaRoi:
    persona: str
    contacted: int = 0
    replies: int = 0
    meetings: int = 0
    deals: int = 0
    revenue: float = 0.0
    reply_rate: float = 0.0
    meeting_rate: float = 0.0


@dataclass(slots=True)
class TriggerRoi:
    trigger: str
    companies: int = 0
    replies: int = 0
    meetings: int = 0
    deals: int = 0
    revenue: float = 0.0
    reply_rate: float = 0.0
    meeting_rate: float = 0.0
    revenue_rate: float = 0.0


@dataclass(slots=True)
class FunnelStage:
    stage: str
    count: int = 0
    conversion_from_previous: float = 0.0
    drop_off: float = 0.0


@dataclass(slots=True)
class ValidationDashboard:
    generated_at: datetime
    today_replies: int = 0
    today_meetings: int = 0
    today_proposals: int = 0
    today_wins: int = 0
    today_revenue: float = 0.0
    reply_rate: float = 0.0
    meeting_rate: float = 0.0
    proposal_rate: float = 0.0
    win_rate: float = 0.0
    avg_sales_cycle_days: float = 0.0
    funnel: list[FunnelStage] = field(default_factory=list)
    connector_roi: list[ConnectorRoi] = field(default_factory=list)
    scoring_version: str = "bvcl-v1"


@dataclass(slots=True)
class DailyReport:
    report_date: str
    signals: int = 0
    companies: int = 0
    revenue_ready: int = 0
    emails_sent: int = 0
    replies: int = 0
    meetings: int = 0
    proposals: int = 0
    won: int = 0
    lost: int = 0
    revenue: float = 0.0
    best_connector: str = ""
    worst_connector: str = ""
    best_industry: str = ""
    worst_industry: str = ""
    top_objections: list[str] = field(default_factory=list)
    biggest_bottleneck: str = ""


@dataclass(slots=True)
class WeeklyReport:
    week_start: str
    week_end: str
    revenue: float = 0.0
    meetings: int = 0
    deals: int = 0
    connector_ranking: list[ConnectorRoi] = field(default_factory=list)
    industry_ranking: list[IndustryRoi] = field(default_factory=list)
    service_ranking: list[ServiceRoi] = field(default_factory=list)
    persona_ranking: list[PersonaRoi] = field(default_factory=list)
    trigger_ranking: list[TriggerRoi] = field(default_factory=list)


@dataclass(slots=True)
class MonthlyReport:
    month: str
    revenue: float = 0.0
    avg_deal_size: float = 0.0
    avg_sales_cycle_days: float = 0.0
    reply_rate: float = 0.0
    meeting_rate: float = 0.0
    proposal_rate: float = 0.0
    win_rate: float = 0.0
    revenue_per_connector: dict[str, float] = field(default_factory=dict)
    revenue_per_industry: dict[str, float] = field(default_factory=dict)
    revenue_per_service: dict[str, float] = field(default_factory=dict)
