from app.main import app


def test_aep_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/client-execution/dashboard" in paths
    assert "/api/v1/client-execution/client/{company_id}" in paths
    assert "/api/v1/client-execution/health" in paths
    assert "/api/v1/client-execution/handoff" in paths
    assert "/api/v1/client-execution/upsells" in paths
    assert "/api/v1/client-execution/projects" in paths
    assert "/api/v1/client-execution/refresh" in paths
    assert "/api/v1/client-execution/upsells/{recommendation_id}/approve" in paths
    assert "/api/v1/client-execution/refresh/{company_id}" in paths


def test_aep_router_tags() -> None:
    tagged = [r for r in app.routes if getattr(r, "tags", None) and "client-execution" in r.tags]
    assert len(tagged) >= 7
