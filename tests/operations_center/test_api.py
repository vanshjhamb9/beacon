from app.main import app

from operations_center.connector_monitor import ensure_known_connectors, score_connector
from operations_center.dashboard_service import DashboardService
from operations_center.health_engine import evaluate_health
from operations_center.pipeline_monitor import biggest_bottleneck, build_stage_metrics, conversion_chain


def test_operations_center_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/operations/live" in paths
    assert "/api/v1/operations/connectors" in paths
    assert "/api/v1/operations/workers" in paths
    assert "/api/v1/operations/pipeline" in paths
    assert "/api/v1/operations/feed" in paths
    assert "/api/v1/operations/queues" in paths
    assert "/api/v1/operations/health" in paths
    assert "/api/v1/operations/daily" in paths
    # ODU moved under /odu to avoid collisions with BOC
    assert "/api/v1/operations/odu/dashboard" in paths
    assert "/api/v1/operations/odu/connectors" in paths


def test_pipeline_conversion_identifies_bottleneck() -> None:
    stages = build_stage_metrics(
        current={
            "signals": 1280,
            "identity_candidates": 600,
            "verified_websites": 194,
            "companies": 180,
            "emails": 55,
            "decision_makers": 24,
            "sales_ready": 13,
            "revenue_ready": 10,
            "contacted": 4,
            "meetings": 2,
            "won": 1,
        },
        today={"signals": 1280},
        yesterday={"signals": 1100},
        hour={"signals": 80},
    )
    steps = conversion_chain(stages)
    assert steps[0].from_stage == "signals"
    assert steps[0].conversion_pct > 0
    bottleneck = biggest_bottleneck(steps)
    assert bottleneck is not None
    assert "->" in bottleneck


def test_known_connectors_reserved_for_future_providers() -> None:
    rows = ensure_known_connectors(
        [
            score_connector(
                connector="github_trending",
                enabled=True,
                records_today=412,
                success_rate=99.0,
                avg_runtime=2.1,
            )
        ]
    )
    names = {r.connector for r in rows}
    assert "hunter" in names
    assert "linkedin" in names
    assert "apollo" in names
    assert "people_data_labs" in names
    hunter = next(r for r in rows if r.connector == "hunter")
    assert hunter.enabled is False


def test_dashboard_service_assembles_payload() -> None:
    service = DashboardService()
    dash = service.build(
        current={
            "signals": 100,
            "identity_candidates": 40,
            "verified_websites": 20,
            "companies": 18,
            "emails": 10,
            "decision_makers": 5,
            "sales_ready": 3,
            "revenue_ready": 2,
            "contacted": 1,
            "meetings": 0,
            "won": 0,
        },
        today={"signals": 12, "revenue_ready": 1},
        yesterday={"signals": 10},
        hour={"signals": 2},
        connectors=[
            score_connector(connector="reddit", enabled=True, records_today=12, success_rate=100.0)
        ],
        workers_inspect={"ping": {"worker@host": {"ok": "pong"}}, "active": {}},
        queue_sizes={"identity": 3, "email": 1},
        failures=[("Website Missing", 10), ("Cloudflare", 4)],
        started_revenue_ready=1,
        pipeline_value=15000.0,
        meetings=0,
        won=0,
    )
    payload = service.to_dict(dash)
    assert payload["scoring_version"] == "boc-v1"
    assert payload["cards"]["signals"]["today"] == 12
    assert payload["health"]["collecting"] is True
    assert payload["progress"]["difference"] == 1
    assert len(payload["connectors"]) >= 10


def test_health_engine_red_when_not_collecting() -> None:
    health = evaluate_health(
        signals_today=0,
        connectors=[score_connector(connector="reddit", enabled=True)],
        workers=[],
        conversions=[],
    )
    assert health.tone == "RED"
    assert health.collecting is False
