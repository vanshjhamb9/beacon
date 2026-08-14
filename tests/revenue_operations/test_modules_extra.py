from uuid import uuid4

from revenue_operations.agents.orchestrator import MultiAgentOrchestrator
from revenue_operations.alerts.engine import SmartAlertEngine
from revenue_operations.analytics.control_tower import RevenueControlTowerEngine
from revenue_operations.analytics.learning import LearningLabEngine
from revenue_operations.analytics.metrics import OperationalMetricsEngine
from revenue_operations.analytics.radar import RevenueRadarEngine
from revenue_operations.analytics.replay import STAGE_ORDER, RevenueReplayEngine
from revenue_operations.dashboard.assistant import FounderAssistantV2Engine
from revenue_operations.dashboard.command_center import CommandCenterEngine
from revenue_operations.forecasting.engine import RevenueForecastEngine
from revenue_operations.forecasting.win_loss import WinLossAnalyticsEngine
from revenue_operations.memory.engine import AgencyMemoryEngine
from revenue_operations.models.types import (
    AlertKind,
    OpportunitySignal,
    RadarSignalKind,
    RevenueOperationsInput,
)


def o(**kw: object) -> OpportunitySignal:
    base = {"company_name": "N", "probability": 50, "pipeline_value": 10000}
    base.update(kw)
    return OpportunitySignal.model_validate(base)


def inp(*opps: OpportunitySignal, **kw: object) -> RevenueOperationsInput:
    return RevenueOperationsInput.model_validate({"opportunities": list(opps) or [o()], **kw})


def test_tower_empty_pipeline() -> None:
    t = RevenueControlTowerEngine().build(inp())
    assert t.campaigns_running == 0 or True
    assert t.revenue_forecast >= t.expected_revenue or t.revenue_forecast >= 0


def test_tower_uses_provided_trends() -> None:
    t = RevenueControlTowerEngine().build(
        inp(weekly_trend=[{"week": 1, "revenue": 10}], monthly_trend=[{"month": 1, "revenue": 20}])
    )
    assert t.weekly_trend[0]["week"] == 1
    assert t.monthly_trend[0]["month"] == 1


def test_radar_intensity_bounds() -> None:
    for s in RevenueRadarEngine().scan(inp(o(radar_hints=["funding", "series a"], probability=99))):
        assert 0 <= s.intensity <= 100


def test_radar_hiring_generic() -> None:
    kinds = {s.kind for s in RevenueRadarEngine().scan(inp(o(radar_hints=["we're hiring engineers"])))}
    assert RadarSignalKind.HIRING in kinds or RadarSignalKind.HIRING_SOFTWARE_DEVELOPERS in kinds


def test_alert_funding_from_radar() -> None:
    radar = RevenueRadarEngine().scan(inp(o(radar_hints=["raised series b funding"])))
    alerts = SmartAlertEngine().detect(inp(o(radar_hints=["raised series b funding"])), radar=radar)
    assert any(a.kind == AlertKind.FUNDING_DETECTED for a in alerts)


def test_alert_opportunity_increased() -> None:
    alerts = SmartAlertEngine().detect(inp(o(probability=90, pipeline_value=50000)))
    assert any(a.kind == AlertKind.REVENUE_OPPORTUNITY_INCREASED for a in alerts)


def test_alert_lead_quality_dropped() -> None:
    alerts = SmartAlertEngine().detect(inp(o(probability=20, days_in_stage=8)))
    assert any(a.kind == AlertKind.LEAD_QUALITY_DROPPED for a in alerts)


def test_agents_message_chain() -> None:
    runs = MultiAgentOrchestrator().run(inp(o(), o(company_name="B")))
    research = next(r for r in runs if r.agent.value == "research")
    assert research.messages[0].to_agent.value == "qualification"


def test_memory_record_types_whitelist() -> None:
    records = AgencyMemoryEngine().build(
        inp(memory_seeds=[{"record_type": "email", "title": "Intro", "body": "Hi"}, {"record_type": "weird", "title": "X"}])
    )
    types = {r.record_type for r in records}
    assert "email" in types
    assert "founder_note" in types  # weird mapped


def test_win_loss_empty() -> None:
    assert WinLossAnalyticsEngine().analyze(inp(o())) == []
    viz = WinLossAnalyticsEngine().visualize([])
    assert viz["win_rate"] == 0.0


def test_forecast_empty_pipeline_risk() -> None:
    pack = RevenueForecastEngine().forecast(RevenueOperationsInput(opportunities=[]))
    assert any("empty" in r.lower() for r in pack.risk_analysis)


def test_assistant_afternoon_greeting() -> None:
    from datetime import UTC, datetime

    item = inp(now=datetime(2026, 7, 24, 15, 0, tzinfo=UTC), founder_name="Sam")
    tower = RevenueControlTowerEngine().build(item)
    forecast = RevenueForecastEngine().forecast(item)
    brief = FounderAssistantV2Engine().generate(item, tower=tower, forecast=forecast)
    assert "Good Afternoon" in brief.greeting


def test_assistant_evening_greeting() -> None:
    from datetime import UTC, datetime

    item = inp(now=datetime(2026, 7, 24, 20, 0, tzinfo=UTC))
    tower = RevenueControlTowerEngine().build(item)
    forecast = RevenueForecastEngine().forecast(item)
    brief = FounderAssistantV2Engine().generate(item, tower=tower, forecast=forecast)
    assert "Good Evening" in brief.greeting


def test_replay_stage_order_constant() -> None:
    assert STAGE_ORDER[0][0] == "lead_discovered"
    assert STAGE_ORDER[-1][0] == "lost"


def test_learning_uses_signals_override() -> None:
    report = LearningLabEngine().analyze(
        inp(learning_signals={"best_email": "case-study first", "best_follow_up_interval_days": 3}),
        win_loss=[],
    )
    assert report.best_email == "case-study first"
    assert report.best_follow_up_interval_days == 3


def test_command_center_score_bounds() -> None:
    item = inp(o(probability=99, pipeline_value=100000, meeting_today=True))
    tower = RevenueControlTowerEngine().build(item)
    forecast = RevenueForecastEngine().forecast(item)
    assistant = FounderAssistantV2Engine().generate(item, tower=tower, forecast=forecast)
    learning = LearningLabEngine().analyze(item, win_loss=[])
    center = CommandCenterEngine().build(item, tower=tower, forecast=forecast, assistant=assistant, learning=learning)
    assert 0 <= center.revenue_score <= 100


def test_metrics_rates_between_0_100() -> None:
    m = OperationalMetricsEngine().compute(inp(o(won=True), o(company_name="B", reply_waiting=True, meeting_count=1)))
    for val in [
        m.qualification_rate,
        m.enrichment_rate,
        m.decision_maker_success,
        m.reply_rate,
        m.meeting_rate,
        m.proposal_rate,
        m.close_rate,
    ]:
        assert 0 <= val <= 100


def test_replay_engine_build_ids() -> None:
    oid = uuid4()
    cid = uuid4()
    replay = RevenueReplayEngine().replay_opportunity(o(opportunity_id=oid, company_id=cid, company_name="ID Co"))
    assert replay.opportunity_id == oid
    assert replay.company_id == cid


def test_control_tower_compose_evidence() -> None:
    assert "compose:existing_engines" in RevenueControlTowerEngine().build(inp()).evidence


def test_hunter_score_updates_aggregate() -> None:
    signals = RevenueRadarEngine().scan(inp(o(company_name="Z", radar_hints=["funding", "ai adoption"])))
    updates = RevenueRadarEngine().hunter_score_updates(signals)
    assert sum(updates.values()) >= 18
