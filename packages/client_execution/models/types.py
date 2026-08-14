from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


SCORING_VERSION = "aep-v1"


class ClientLifecycleStage(StrEnum):
    WON = "won"
    CONTRACT_PENDING = "contract_pending"
    KICKOFF_SCHEDULED = "kickoff_scheduled"
    REQUIREMENTS_GATHERING = "requirements_gathering"
    PLANNING = "planning"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    REVIEW = "review"
    LAUNCH = "launch"
    SUPPORT = "support"
    UPSELL_OPPORTUNITY = "upsell_opportunity"
    RENEWAL = "renewal"
    REFERRAL = "referral"
    LOST_CLIENT = "lost_client"
    ARCHIVE = "archive"


class UpsellService(StrEnum):
    AI_AUTOMATION = "AI Automation"
    CUSTOM_SAAS = "Custom SaaS"
    MOBILE_APP = "Mobile App"
    WEBSITE_UPGRADE = "Website Upgrade"
    CRM = "CRM"
    ANALYTICS = "Analytics"
    INTERNAL_TOOLS = "Internal Tools"


class ClientWorkspace(BaseModel):
    model_config = ConfigDict(frozen=True)

    executive_summary: str
    company: str
    services_purchased: list[str] = Field(default_factory=list)
    contract_value: float = 0.0
    expected_delivery: str | None = None
    primary_contacts: list[dict[str, Any]] = Field(default_factory=list)
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    meeting_history: list[dict[str, Any]] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    invoices_status: str = "placeholder"
    support_requests: list[dict[str, Any]] = Field(default_factory=list)
    renewal_date: str | None = None
    evidence: list[str] = Field(default_factory=list)


class ProjectHandoff(BaseModel):
    model_config = ConfigDict(frozen=True)

    client_dossier: str
    meeting_summary: str
    business_goals: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    agreed_solution: str
    scope_summary: str
    timeline: list[str] = Field(default_factory=list)
    known_objections: list[str] = Field(default_factory=list)
    decision_history: list[str] = Field(default_factory=list)
    sales_notes: list[str] = Field(default_factory=list)
    founder_notes: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class KnowledgeRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    record_type: str
    title: str
    body: str = ""
    tags: list[str] = Field(default_factory=list)
    searchable_text: str = ""
    evidence: list[str] = Field(default_factory=list)


class UpsellRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    recommendation_id: str
    service: UpsellService
    title: str
    reason: str
    confidence: float = Field(ge=0.0, le=100.0)
    requires_founder_approval: bool = True
    modifies_production: bool = False
    evidence: list[str] = Field(default_factory=list)


class ClientHealth(BaseModel):
    model_config = ConfigDict(frozen=True)

    communication_score: float = Field(ge=0.0, le=100.0, default=0.0)
    delivery_score: float = Field(ge=0.0, le=100.0, default=0.0)
    risk_score: float = Field(ge=0.0, le=100.0, default=0.0)
    delay_score: float = Field(ge=0.0, le=100.0, default=0.0)
    satisfaction_score: float = Field(ge=0.0, le=100.0, default=0.0)
    meeting_frequency_score: float = Field(ge=0.0, le=100.0, default=0.0)
    open_issues: int = 0
    renewal_probability: float = Field(ge=0.0, le=100.0, default=0.0)
    upsell_probability: float = Field(ge=0.0, le=100.0, default=0.0)
    overall_health: float = Field(ge=0.0, le=100.0, default=0.0)
    status: str = "healthy"
    evidence: list[str] = Field(default_factory=list)


class DeliveryDashboard(BaseModel):
    model_config = ConfigDict(frozen=True)

    todays_deliveries: list[dict[str, Any]] = Field(default_factory=list)
    upcoming_milestones: list[dict[str, Any]] = Field(default_factory=list)
    blocked_projects: list[dict[str, Any]] = Field(default_factory=list)
    at_risk_projects: list[dict[str, Any]] = Field(default_factory=list)
    client_health: list[dict[str, Any]] = Field(default_factory=list)
    renewals: list[dict[str, Any]] = Field(default_factory=list)
    upsells: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class FounderExecutiveView(BaseModel):
    model_config = ConfigDict(frozen=True)

    revenue_closed: float = 0.0
    projects_running: int = 0
    revenue_delivered: float = 0.0
    pending_payments: str = "placeholder"
    renewals: int = 0
    upsells: int = 0
    client_risks: int = 0
    team_capacity: str = "placeholder"
    evidence: list[str] = Field(default_factory=list)


class ClientProjectSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    project_id: UUID | None = None
    name: str
    stage: str | None = None
    blocked: bool = False
    at_risk: bool = False
    milestone: str | None = None
    due_today: bool = False
    deliverable: str | None = None


class ClientExecutionInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    industry: str | None = None
    stage_hint: str | None = None
    won: bool = True
    contract_signed: bool = False
    kickoff_scheduled: bool = False
    requirements_complete: bool = False
    planning_complete: bool = False
    design_complete: bool = False
    development_active: bool = False
    testing_active: bool = False
    in_review: bool = False
    launched: bool = False
    in_support: bool = False
    upsell_signal: bool = False
    renewal_due: bool = False
    referral_made: bool = False
    lost_client: bool = False
    archived: bool = False
    services_purchased: list[str] = Field(default_factory=list)
    contract_value: float = 0.0
    revenue_delivered: float = 0.0
    expected_delivery: str | None = None
    renewal_date: str | None = None
    primary_contacts: list[dict[str, Any]] = Field(default_factory=list)
    decision_makers: list[dict[str, Any]] = Field(default_factory=list)
    meeting_history: list[dict[str, Any]] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    support_requests: list[dict[str, Any]] = Field(default_factory=list)
    business_goals: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    agreed_solution: str | None = None
    scope_summary: str | None = None
    known_objections: list[str] = Field(default_factory=list)
    decision_history: list[str] = Field(default_factory=list)
    sales_notes: list[str] = Field(default_factory=list)
    founder_notes: list[str] = Field(default_factory=list)
    architecture_notes: list[str] = Field(default_factory=list)
    documents: list[str] = Field(default_factory=list)
    revisions: list[str] = Field(default_factory=list)
    feedback: list[str] = Field(default_factory=list)
    approvals: list[str] = Field(default_factory=list)
    growth_signals: list[str] = Field(default_factory=list)
    hiring_signals: list[str] = Field(default_factory=list)
    funding_signals: list[str] = Field(default_factory=list)
    usage_signals: list[str] = Field(default_factory=list)
    expansion_signals: list[str] = Field(default_factory=list)
    projects: list[ClientProjectSignal] = Field(default_factory=list)
    communication_score: float = 70.0
    delivery_progress: float = 50.0
    delay_days: int = 0
    satisfaction: float = 70.0
    meetings_last_30d: int = 2
    open_issues: int = 0
    days_to_renewal: int | None = None
    now: datetime | None = None


class ClientExecutionDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    company_name: str
    stage: ClientLifecycleStage
    workspace: ClientWorkspace
    handoff: ProjectHandoff
    knowledge: list[KnowledgeRecord] = Field(default_factory=list)
    upsells: list[UpsellRecommendation] = Field(default_factory=list)
    health: ClientHealth
    delivery_dashboard: DeliveryDashboard
    founder_view: FounderExecutiveView
    scoring_version: str = SCORING_VERSION
    evidence_chain: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
