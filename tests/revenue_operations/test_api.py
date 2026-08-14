from app.main import app


def test_roc_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/revenue-operations/dashboard" in paths
    assert "/api/v1/revenue-operations/forecast" in paths
    assert "/api/v1/revenue-operations/alerts" in paths
    assert "/api/v1/revenue-operations/memory" in paths
    assert "/api/v1/revenue-operations/replay/{replay_id}" in paths
    assert "/api/v1/revenue-operations/learning" in paths
    assert "/api/v1/revenue-operations/metrics" in paths
    assert "/api/v1/revenue-operations/refresh" in paths
    assert "/api/v1/revenue-operations/alerts/{alert_id}/transition" in paths
    assert "/api/v1/revenue-operations/learning/{recommendation_id}/approve" in paths
