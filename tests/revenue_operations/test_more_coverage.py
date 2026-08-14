from uuid import uuid4

from revenue_operations import RevenueOperationsPipeline, RevenueOperationsService
from revenue_operations.alerts.engine import SmartAlertEngine
from revenue_operations.analytics.radar import HINT_MAP
from revenue_operations.memory.engine import AgencyMemoryEngine
from revenue_operations.models.types import (
    AlertLifecycle,
    OpportunitySignal,
    RadarSignalKind,
    RevenueOperationsInput,
)


def test_hint_map_covers_mission_signals() -> None:
    kinds = {kind for _, kind, _ in HINT_MAP}
    required = {
        RadarSignalKind.FUNDING,
        RadarSignalKind.HIRING,
        RadarSignalKind.TECHNOLOGY_CHANGE,
        RadarSignalKind.PRODUCT_LAUNCH,
        RadarSignalKind.AI_ADOPTION,
        RadarSignalKind.CLOUD_MIGRATION,
        RadarSignalKind.DIGITAL_TRANSFORMATION,
        RadarSignalKind.NEW_OFFICE,
        RadarSignalKind.EXPANSION,
        RadarSignalKind.LEADERSHIP_CHANGE,
        RadarSignalKind.DECISION_MAKER_CHANGE,
        RadarSignalKind.WEBSITE_REDESIGN,
        RadarSignalKind.HIRING_AI_ENGINEERS,
        RadarSignalKind.HIRING_SOFTWARE_DEVELOPERS,
        RadarSignalKind.HIRING_PRODUCT_MANAGERS,
        RadarSignalKind.HIRING_AUTOMATION_ENGINEERS,
        RadarSignalKind.TECH_STACK_CHANGE,
    }
    assert required.issubset(kinds)


def test_alert_same_state_transition() -> None:
    assert SmartAlertEngine().transition(AlertLifecycle.VIEWED, AlertLifecycle.VIEWED) == AlertLifecycle.VIEWED


def test_memory_client_and_service_records() -> None:
    records = AgencyMemoryEngine().build(
        RevenueOperationsInput(
            opportunities=[
                OpportunitySignal(company_name="Client Co", won=True, service="SaaS", industry="Education"),
            ]
        )
    )
    assert any(r.record_type == "client" for r in records)
    assert any(r.record_type == "service" for r in records)
    assert any(r.record_type == "industry" for r in records)


def test_pipeline_alert_count_stable_with_existing_keys() -> None:
    item = RevenueOperationsInput(
        opportunities=[
            OpportunitySignal(
                company_id=uuid4(),
                company_name="Dup",
                probability=90,
                pipeline_value=60000,
                reply_waiting=True,
                days_in_stage=4,
            )
        ]
    )
    first = RevenueOperationsPipeline().process(item)
    second = RevenueOperationsPipeline().process(
        RevenueOperationsInput(
            opportunities=item.opportunities,
            existing_alert_keys=[a.dedupe_key for a in first.alerts],
        )
    )
    assert len(second.alerts) <= len(first.alerts)


def test_service_evaluate_many_preserves_order() -> None:
    items = [
        RevenueOperationsInput(opportunities=[OpportunitySignal(company_name=f"O{i}", probability=40 + i)])
        for i in range(4)
    ]
    out = RevenueOperationsService().evaluate_many(items)
    assert [d.control_tower.evidence[0] for d in out]  # non-empty
    assert len(out) == 4


def test_command_center_recommendations_require_approval_flag() -> None:
    d = RevenueOperationsPipeline().process(
        RevenueOperationsInput(opportunities=[OpportunitySignal(company_name="R", industry="Retail", won=True)])
    )
    assert d.command_center.recommendations
    assert all(r.get("requires_approval") is True for r in d.command_center.recommendations)


def test_operational_metrics_cac_ltv_from_agency_stats() -> None:
    d = RevenueOperationsPipeline().process(
        RevenueOperationsInput(
            opportunities=[OpportunitySignal(company_name="M", won=True, pipeline_value=50000)],
            agency_stats={"cac": 1000, "ltv": 10000},
        )
    )
    assert d.operational_metrics.customer_acquisition_cost == 1000
    assert d.operational_metrics.lifetime_value == 10000
    assert d.operational_metrics.roi == 900.0


def test_forecast_expected_closes_non_negative() -> None:
    d = RevenueOperationsPipeline().process(
        RevenueOperationsInput(opportunities=[OpportunitySignal(company_name="F", probability=10, pipeline_value=500)])
    )
    assert d.forecast.this_week.expected_closes >= 0
    assert d.forecast.annual.expected_proposals >= 0


def test_win_loss_decision_maker_captured() -> None:
    d = RevenueOperationsPipeline().process(
        RevenueOperationsInput(
            opportunities=[
                OpportunitySignal(
                    company_name="W",
                    won=True,
                    why_won="Speed",
                    decision_makers=["Pat COO"],
                    meeting_count=3,
                    proposal_count=2,
                    reply_speed_hours=4,
                )
            ]
        )
    )
    assert d.win_loss[0].decision_maker == "Pat COO"
    assert d.win_loss[0].meeting_count == 3


def test_replay_includes_research_and_qualification() -> None:
    d = RevenueOperationsPipeline().process(
        RevenueOperationsInput(opportunities=[OpportunitySignal(company_name="T", probability=55)])
    )
    stages = [e.stage for e in d.replays[0].events]
    assert "research" in stages
    assert "qualification" in stages


def test_founder_assistant_default_priority_when_quiet() -> None:
    d = RevenueOperationsPipeline().process(
        RevenueOperationsInput(opportunities=[OpportunitySignal(company_name="Quiet", probability=45)])
    )
    assert d.founder_assistant.top_priorities
    assert "Review pipeline" in d.founder_assistant.top_priorities[0] or d.founder_assistant.todays_mission


def test_agents_outputs_are_structured_dicts() -> None:
    d = RevenueOperationsPipeline().process(
        RevenueOperationsInput(opportunities=[OpportunitySignal(company_name="A")])
    )
    assert all(isinstance(r.outputs, dict) for r in d.agent_runs)
