from app.main import app


def test_goi_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/account-journey/company/{company_id}" in paths
    assert "/api/v1/account-journey/dashboard" in paths
    assert "/api/v1/account-journey/followups" in paths
    assert "/api/v1/account-journey/analytics" in paths
    assert "/api/v1/account-journey/replies" in paths
    assert "/api/v1/account-journey/health" in paths
    assert "/api/v1/account-journey/refresh" in paths
