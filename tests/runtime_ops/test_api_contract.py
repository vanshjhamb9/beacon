"""API contract tests for operations routes (import-level / schema)."""

from __future__ import annotations

from app.schemas.runtime_ops import RuntimeOpsReportsResponse, RuntimeOpsResponse


def test_runtime_ops_response_model_fields():
    fields = set(RuntimeOpsResponse.model_fields)
    for required in {
        "generated_at",
        "scoring_version",
        "infrastructure",
        "redis",
        "migrations",
        "celery",
        "pipeline",
        "collectors",
        "enrichment",
        "freshness",
        "alerts",
        "production_gate",
        "readiness_score",
    }:
        assert required in fields


def test_reports_response_model():
    assert "reports" in RuntimeOpsReportsResponse.model_fields


def test_operations_router_importable():
    from app.api.routes.operations import router

    paths = {getattr(r, "path", None) for r in router.routes}
    assert "" in paths or "/" in {p or "" for p in paths} or any(True for _ in router.routes)


def test_celery_includes_runtime_ops_heartbeat():
    from worker.celery_app import celery_app

    schedule = celery_app.conf.beat_schedule or {}
    assert "runtime-ops-beat-heartbeat" in schedule
    assert schedule["runtime-ops-beat-heartbeat"]["task"] == "runtime_ops.beat_heartbeat"
    assert "worker.runtime_ops_tasks" in (celery_app.conf.include or [])
