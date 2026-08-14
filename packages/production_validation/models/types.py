from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


SCORING_VERSION = "prrv-v1"
READINESS_GATE = 90.0


class HealthStatus(StrEnum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class AlertSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComponentHealth(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    status: HealthStatus
    latency_ms: float = 0.0
    throughput: float = 0.0
    failure_rate: float = 0.0
    success_rate: float = 100.0
    retry_count: int = 0
    queue_depth: int = 0
    accuracy: float | None = None
    evidence: list[str] = Field(default_factory=list)
    recommendation: str | None = None


class EngineHealthReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    components: list[ComponentHealth] = Field(default_factory=list)
    overall_status: HealthStatus = HealthStatus.UNKNOWN
    overall_score: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class CampaignFunnelSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    campaign_id: UUID | None = None
    company_id: UUID | None = None
    company_name: str = ""
    emails_sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    replies: int = 0
    meetings: int = 0
    proposals: int = 0
    won: int = 0
    revenue: float = 0.0
    stage: str = "unknown"
    evidence: list[str] = Field(default_factory=list)


class LeadReadinessChecklist(BaseModel):
    model_config = ConfigDict(frozen=True)

    website: bool = False
    business_email: bool = False
    decision_maker: bool = False
    linkedin: bool = False
    technology: bool = False
    industry: bool = False
    buying_trigger: bool = False
    pain_point: bool = False
    revenue_estimate: bool = False
    service_match: bool = False
    confidence: bool = False
    freshness: bool = False
    verification: bool = False


class LeadReadinessResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    score: float = Field(ge=0.0, le=100.0)
    checklist: LeadReadinessChecklist
    outreach_allowed: bool
    evidence: list[str] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)


class FreshnessSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal: str
    detected: bool
    detail: str
    reenrich_queued: bool = False


class FreshnessReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    stale: bool
    signals: list[FreshnessSignal] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ProductionAlert(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    title: str
    severity: AlertSeverity
    recommendation: str
    owner: str = "founder"
    evidence: list[str] = Field(default_factory=list)


class RevenueHealthSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    revenue_today: float = 0.0
    pipeline_value: float = 0.0
    qualified_companies: int = 0
    sales_ready: int = 0
    campaigns: int = 0
    replies: int = 0
    meetings: int = 0
    proposals: int = 0
    revenue_closed: float = 0.0
    win_rate: float = 0.0
    average_deal_size: float = 0.0
    average_sales_cycle_days: float = 0.0
    forecast: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class OutcomeLearningSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    reply_rate: float = 0.0
    meeting_rate: float = 0.0
    proposal_rate: float = 0.0
    win_rate: float = 0.0
    industry_success: dict[str, float] = Field(default_factory=dict)
    service_success: dict[str, float] = Field(default_factory=dict)
    persona_success: dict[str, float] = Field(default_factory=dict)
    subject_line_success: dict[str, float] = Field(default_factory=dict)
    cta_success: dict[str, float] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    requires_human_approval: bool = True
    evidence: list[str] = Field(default_factory=list)


class PlaybookPack(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    pain_points: list[str] = Field(default_factory=list)
    business_triggers: list[str] = Field(default_factory=list)
    roi: str
    discovery_questions: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    pricing_guidance: str
    proposal_structure: list[str] = Field(default_factory=list)
    case_studies: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class WeeklyRevenueReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    companies_found: int = 0
    qualified: int = 0
    sales_ready: int = 0
    campaigns: int = 0
    emails: int = 0
    replies: int = 0
    meetings: int = 0
    proposals: int = 0
    revenue: float = 0.0
    lost_deals: int = 0
    reasons_lost: list[str] = Field(default_factory=list)
    top_industries: list[str] = Field(default_factory=list)
    top_services: list[str] = Field(default_factory=list)
    best_campaign: str | None = None
    worst_campaign: str | None = None
    improvement_suggestions: list[str] = Field(default_factory=list)
    csv_text: str = ""
    pdf_text: str = ""
    evidence: list[str] = Field(default_factory=list)


class SecurityAuditFinding(BaseModel):
    model_config = ConfigDict(frozen=True)

    control: str
    status: HealthStatus
    detail: str
    recommendation: str


class SecurityAuditReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    findings: list[SecurityAuditFinding] = Field(default_factory=list)
    overall_status: HealthStatus = HealthStatus.UNKNOWN
    score: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class ModuleReadiness(BaseModel):
    model_config = ConfigDict(frozen=True)

    module: str
    status: HealthStatus
    score: float = 0.0
    recommendation: str = ""
    evidence: list[str] = Field(default_factory=list)


class ProductionReadinessReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    overall_score: float = 0.0
    overall_status: HealthStatus = HealthStatus.UNKNOWN
    modules: list[ModuleReadiness] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    scoring_version: str = SCORING_VERSION
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    evidence: list[str] = Field(default_factory=list)


class FounderActionBoard(BaseModel):
    model_config = ConfigDict(frozen=True)

    contact_now: list[dict[str, Any]] = Field(default_factory=list)
    replied: list[dict[str, Any]] = Field(default_factory=list)
    booked: list[dict[str, Any]] = Field(default_factory=list)
    needs_proposal: list[dict[str, Any]] = Field(default_factory=list)
    needs_follow_up: list[dict[str, Any]] = Field(default_factory=list)
    revenue_stuck: list[dict[str, Any]] = Field(default_factory=list)
    do_now: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ProductionValidationInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID | None = None
    company_name: str = "Beacon"
    website: str | None = None
    business_email: str | None = None
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    linkedin_url: str | None = None
    technologies: list[str] = Field(default_factory=list)
    industry: str | None = None
    buying_triggers: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    revenue_estimate: str | None = None
    service_match: str | None = None
    confidence: float = 0.0
    freshness_days: int = 0
    verification_score: float = 0.0
    component_signals: dict[str, dict[str, Any]] = Field(default_factory=dict)
    funnel: dict[str, Any] = Field(default_factory=dict)
    campaigns: list[dict[str, Any]] = Field(default_factory=list)
    oauth_ok: bool = True
    workers_online: bool = True
    queue_depth: int = 0
    bounce_rate: float = 0.0
    reply_rate: float = 0.0
    duplicate_send_detected: bool = False
    webhook_failures: int = 0
    api_failures: int = 0
    migration_drift: bool = False
    security_flags: dict[str, bool] = Field(default_factory=dict)
    revenue_metrics: dict[str, Any] = Field(default_factory=dict)
    outcome_rates: dict[str, float] = Field(default_factory=dict)
    founder_queues: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    stale_signals: list[str] = Field(default_factory=list)
    now: datetime | None = None


class ProductionValidationDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    health: EngineHealthReport
    campaign_funnels: list[CampaignFunnelSnapshot] = Field(default_factory=list)
    lead_readiness: LeadReadinessResult | None = None
    freshness: FreshnessReport | None = None
    alerts: list[ProductionAlert] = Field(default_factory=list)
    revenue: RevenueHealthSnapshot
    outcome_learning: OutcomeLearningSnapshot
    playbooks: list[PlaybookPack] = Field(default_factory=list)
    weekly_report: WeeklyRevenueReport
    security_audit: SecurityAuditReport
    readiness_report: ProductionReadinessReport
    founder_board: FounderActionBoard
    scoring_version: str = SCORING_VERSION
    evidence_chain: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
