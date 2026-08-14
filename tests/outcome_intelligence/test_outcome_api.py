from app.main import app


def test_outcome_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/outcomes/dashboard" in paths
    assert "/api/v1/outcomes/company/{company_id}" in paths
    assert "/api/v1/outcomes/update" in paths
    assert "/api/v1/outcomes/analytics" in paths
