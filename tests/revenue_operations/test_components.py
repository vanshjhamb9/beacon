from datetime import UTC, datetime
from uuid import uuid4

import pytest

from revenue_operations import SCORING_VERSION, RevenueOperationsPipeline, RevenueOperationsService
from revenue_operations.agents.orchestrator import MultiAgentOrchestrator
from revenue_operations.alerts.engine import SmartAlertEngine
from revenue_operations.analytics.control_tower import RevenueControlTowerEngine
from revenue_operations.analytics.learning import LearningLabEngine
from revenue_operations.analytics.metrics import OperationalMetricsEngine
from revenue_operations.analytics.radar import RevenueRadarEngine
from revenue_operations.analytics.replay import RevenueReplayEngine
from revenue_operations.dashboard.assistant import FounderAssistantV2Engine
from revenue_operations.dashboard.command_center import CommandCenterEngine
from revenue_operations.forecasting.engine import RevenueForecastEngine
from revenue_operations.forecasting.win_loss import WinLossAnalyticsEngine
from revenue_operations.memory.engine import AgencyMemoryEngine
from revenue_operations.models.types import (
    AgentRole,
    AlertKind,
    AlertLifecycle,
    OpportunitySignal,
    RecommendationStatus,
    RevenueOperationsInput,
)
from revenue_operations.scheduler.hints import default_schedule


def _opp(**overrides: object) -> OpportunitySignal:
    payload: dict[str, object] = {
        "opportunity_id": uuid4(),
        "company_id": uuid4(),
        "company_name": "Acme",
        "industry": "SaaS",
        "service": "AI Automation",
        "stage": "open",
        "probability": 70,
        "pipeline_value": 40000,
        "days_in_stage": 2,
        "decision_makers": ["Alex CEO"],
        "lead_source": "Revenue Hunter",
        "campaign_name": "Q3 Outreach",
        "country": "US",
        "company_size": "51-200",
        "technologies": ["Python"],
    }
    payload.update(overrides)
    return OpportunitySignal.model_validate(payload)


def _input(*opps: OpportunitySignal, **overrides: object) -> RevenueOperationsInput:
    payload: dict[str, object] = {
        "opportunities": list(opps) or [_opp()],
        "campaigns_running": 3,
        "revenue_today": 1200,
        "revenue_closed": 90000,
        "revenue_target_week": 50000,
        "top_industries": ["SaaS", "Healthcare"],
        "top_services": ["AI Automation"],
        "top_campaign": "Q3 Outreach",
        "top_lead_source": "Revenue Hunter",
        "founder_name": "Operator",
        "now": datetime(2026, 7, 24, 9, 0, tzinfo=UTC),
    }
    payload.update(overrides)
    return RevenueOperationsInput.model_validate(payload)


def test_scoring_version() -> None:
    assert SCORING_VERSION == "roc-v1"


def test_control_tower_fields() -> None:
    tower = RevenueControlTowerEngine().build(
        _input(
            _opp(meeting_today=True, reply_waiting=True, proposal_pending=True, negotiation=True, at_risk=True),
            _opp(company_name="Beta", probability=40, pipeline_value=20000),
        )
    )
    assert tower.meetings_today == 1
    assert tower.replies_waiting == 1
    assert tower.proposals_pending == 1
    assert tower.negotiations == 1
    assert tower.deals_at_risk == 1
    assert tower.pipeline_value > 0
    assert tower.expected_revenue > 0
    assert tower.top_industries
    assert tower.top_services
    assert tower.top_campaign
    assert tower.top_lead_source
    assert "discovered" in tower.conversion_funnel


def test_radar_detects_funding_and_hiring() -> None:
    signals = RevenueRadarEngine().scan(
        _input(_opp(radar_hints=["Series A funding", "hiring AI engineers", "cloud migration to aws"]))
    )
    kinds = {s.kind.value for s in signals}
    assert "funding" in kinds
    assert "hiring_ai_engineers" in kinds
    assert "cloud_migration" in kinds
    updates = RevenueRadarEngine().hunter_score_updates(signals)
    assert updates
    assert all(v > 0 for v in updates.values())


def test_radar_all_signal_families() -> None:
    hints = [
        "product launch",
        "ai adoption llm",
        "digital transformation",
        "new office opened",
        "expansion into eu",
        "new ceo appointed",
        "decision maker head of ops",
        "website redesign",
        "hiring software developers",
        "hiring product managers",
        "hiring automation engineers",
        "tech stack adopted rust",
    ]
    signals = RevenueRadarEngine().scan(_input(_opp(radar_hints=hints)))
    assert len(signals) >= 8


def test_alert_dedupe() -> None:
    opp = _opp(reply_waiting=True, probability=80, days_in_stage=3)
    eng = SmartAlertEngine()
    first = eng.detect(_input(opp))
    second = eng.detect(_input(opp, existing_alert_keys=[first[0].dedupe_key]))
    assert first
    assert all(a.dedupe_key != first[0].dedupe_key for a in second) or len(second) < len(first)


def test_alert_kinds_cover_examples() -> None:
    alerts = SmartAlertEngine().detect(
        _input(
            _opp(reply_waiting=True, probability=80, days_in_stage=3, meeting_today=True, proposal_pending=True, at_risk=True, stage="stopped"),
        )
    )
    kinds = {a.kind for a in alerts}
    assert AlertKind.HIGH_INTENT_REPLY in kinds
    assert AlertKind.MEETING_BOOKED in kinds
    assert AlertKind.PROPOSAL_OVERDUE in kinds or AlertKind.REPLY_OVERDUE in kinds
    assert AlertKind.LOST_DEAL_RISK in kinds


def test_alert_lifecycle() -> None:
    eng = SmartAlertEngine()
    assert eng.transition(AlertLifecycle.NEW, AlertLifecycle.VIEWED) == AlertLifecycle.VIEWED
    assert eng.transition(AlertLifecycle.VIEWED, AlertLifecycle.RESOLVED) == AlertLifecycle.RESOLVED
    assert eng.transition(AlertLifecycle.RESOLVED, AlertLifecycle.ARCHIVED) == AlertLifecycle.ARCHIVED
    with pytest.raises(ValueError):
        eng.transition(AlertLifecycle.ARCHIVED, AlertLifecycle.NEW)


def test_multi_agent_nine_roles() -> None:
    runs = MultiAgentOrchestrator().run(_input())
    roles = {r.agent for r in runs}
    assert roles == set(AgentRole)
    assert all(r.messages or r.agent == AgentRole.FOUNDER for r in runs)
    assert any("no_gpt:true" in r.evidence for r in runs if r.agent == AgentRole.FOUNDER)


def test_agency_memory_searchable_append_only() -> None:
    mem = AgencyMemoryEngine()
    records = mem.build(
        _input(
            _opp(meeting_today=True, reply_waiting=True, proposal_pending=True, negotiation=True, objections=["Budget"], budget="$40k", won=True, founder_notes=["Great call"]),
            memory_seeds=[{"record_type": "case_study", "title": "Retail AI", "body": "40% savings", "tags": ["retail"]}],
        )
    )
    types = {r.record_type for r in records}
    assert "meeting" in types
    assert "reply" in types
    assert "proposal" in types
    assert "case_study" in types
    assert "founder_note" in types
    hits = mem.search(records, "budget")
    assert hits


def test_win_loss_analytics() -> None:
    records = WinLossAnalyticsEngine().analyze(
        _input(
            _opp(won=True, why_won="Clear ROI", sales_cycle_days=21, meeting_count=2, proposal_count=1),
            _opp(company_name="LostCo", lost=True, why_lost="Timing", competitor="Incumbent", sales_cycle_days=40),
        )
    )
    assert len(records) == 2
    viz = WinLossAnalyticsEngine().visualize(records)
    assert viz["won"] == 1
    assert viz["lost"] == 1
    assert viz["win_rate"] == 50.0


def test_forecast_horizons() -> None:
    pack = RevenueForecastEngine().forecast(_input(_opp(), _opp(company_name="B", probability=55, pipeline_value=25000, at_risk=True)))
    assert pack.this_week.amount >= 0
    assert pack.this_month.amount >= pack.this_week.amount
    assert pack.quarter.amount >= pack.this_month.amount
    assert pack.annual.amount >= pack.quarter.amount
    assert 0 <= pack.confidence_score <= 100
    assert 0 <= pack.pipeline_health <= 100
    assert pack.this_week.expected_meetings >= 0


def test_founder_assistant_no_chat_shape() -> None:
    item = _input(_opp(meeting_today=True, reply_waiting=True, probability=85))
    tower = RevenueControlTowerEngine().build(item)
    forecast = RevenueForecastEngine().forecast(item)
    brief = FounderAssistantV2Engine().generate(item, tower=tower, forecast=forecast)
    assert brief.greeting.startswith("Good Morning")
    assert brief.executive_summary
    assert brief.todays_mission
    assert brief.top_priorities
    assert brief.revenue_target == 50000
    assert "no_chat:true" in brief.evidence


def test_replay_stages() -> None:
    replay = RevenueReplayEngine().replay_opportunity(
        _opp(reply_waiting=True, meeting_count=1, proposal_count=1, negotiation=True, won=True, why_won="Fit")
    )
    stages = [e.stage for e in replay.events]
    assert stages[0] == "lead_discovered"
    assert "email" in stages
    assert "reply" in stages
    assert "meeting" in stages
    assert "proposal" in stages
    assert "negotiation" in stages
    assert "won" in stages
    assert replay.outcome == "won"


def test_learning_lab_never_modifies_production() -> None:
    item = _input(_opp(won=True), _opp(company_name="L", lost=True, why_lost="Budget"))
    win_loss = WinLossAnalyticsEngine().analyze(item)
    report = LearningLabEngine().analyze(item, win_loss=win_loss)
    assert report.best_industries
    assert report.best_services
    assert report.best_email
    assert report.best_whatsapp
    assert report.best_meeting_time
    assert report.recommendations
    assert all(r.status == RecommendationStatus.PENDING_APPROVAL for r in report.recommendations)
    assert all(r.modifies_production is False for r in report.recommendations)
    assert "founder_approval_required:true" in report.evidence


def test_command_center_above_fold() -> None:
    item = _input(_opp(meeting_today=True, reply_waiting=True))
    tower = RevenueControlTowerEngine().build(item)
    forecast = RevenueForecastEngine().forecast(item)
    assistant = FounderAssistantV2Engine().generate(item, tower=tower, forecast=forecast)
    learning = LearningLabEngine().analyze(item, win_loss=[])
    center = CommandCenterEngine().build(item, tower=tower, forecast=forecast, assistant=assistant, learning=learning)
    assert center.greeting
    assert center.todays_mission
    assert center.revenue_score >= 0
    assert "value" in center.pipeline
    assert "this_week" in center.forecast
    assert center.campaign_health
    assert "above_the_fold:true" in center.evidence


def test_operational_metrics() -> None:
    metrics = OperationalMetricsEngine().compute(
        _input(
            _opp(won=True, sales_cycle_days=20, meeting_count=2, proposal_count=1),
            _opp(company_name="B", probability=50, reply_waiting=True),
        )
    )
    assert metrics.discovery_rate == 100
    assert metrics.qualification_rate > 0
    assert metrics.close_rate > 0
    assert metrics.average_deal_size > 0
    assert metrics.roi != 0


def test_pipeline_full_decision() -> None:
    decision = RevenueOperationsPipeline().process(
        _input(
            _opp(radar_hints=["funding round"], reply_waiting=True, probability=82, meeting_today=True),
            _opp(company_name="Risk", at_risk=True, days_in_stage=12, probability=30),
        )
    )
    assert decision.scoring_version == "roc-v1"
    assert decision.control_tower
    assert decision.radar_signals
    assert decision.alerts
    assert len(decision.agent_runs) == 9
    assert decision.memory_records
    assert decision.forecast
    assert decision.founder_assistant
    assert decision.replays
    assert decision.learning
    assert decision.command_center
    assert decision.operational_metrics
    assert "compose_only:true" in decision.evidence_chain
    assert "no_gpt:true" in decision.evidence_chain


def test_service_wrappers() -> None:
    svc = RevenueOperationsService()
    d = svc.evaluate(_input())
    assert d.command_center.revenue_score >= 0
    assert svc.transition_alert(AlertLifecycle.NEW, AlertLifecycle.DISMISSED) == AlertLifecycle.DISMISSED
    mem = svc.search_memory(d.memory_records, d.memory_records[0].company_name or "Acme")
    assert isinstance(mem, list)


def test_schedule_hints() -> None:
    s = default_schedule()
    assert s.refresh_dashboard_seconds == 120
    assert s.refresh_forecast_seconds == 300
    assert s.refresh_alerts_seconds == 60
    assert s.daily_learning_seconds == 86_400


def test_evaluate_many() -> None:
    out = RevenueOperationsService().evaluate_many([_input(_opp(company_name=f"C{i}")) for i in range(3)])
    assert len(out) == 3
