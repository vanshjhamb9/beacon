from app.main import app


def test_production_validation_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/production-validation/report" in paths
    assert "/api/v1/production-validation/refresh" in paths
    assert "/api/v1/production-validation/health" in paths
    assert "/api/v1/production-validation/revenue" in paths
    assert "/api/v1/production-validation/alerts" in paths
    assert "/api/v1/production-validation/playbooks" in paths
    assert "/api/v1/production-validation/campaigns/monitoring" in paths
    assert "/api/v1/production-validation/lead-readiness/{company_id}" in paths
