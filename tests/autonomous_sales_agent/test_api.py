from app.main import app


def test_asa_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/autonomous-sales-agent/company/{company_id}" in paths
    assert "/api/v1/autonomous-sales-agent/refresh/{company_id}" in paths
    assert "/api/v1/autonomous-sales-agent/work-queue" in paths
    assert "/api/v1/autonomous-sales-agent/morning-brief" in paths
    assert "/api/v1/autonomous-sales-agent/morning-brief/refresh" in paths
    assert "/api/v1/autonomous-sales-agent/timeline/{company_id}" in paths
    assert "/api/v1/autonomous-sales-agent/dashboard" in paths
    assert "/api/v1/autonomous-sales-agent/refresh-batch" in paths
