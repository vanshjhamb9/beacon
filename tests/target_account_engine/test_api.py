from app.main import app


def test_target_account_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/targets" in paths
    assert "/api/v1/targets/{target_id}" in paths
    assert "/api/v1/targets/dashboard" in paths
    assert "/api/v1/icp" in paths
    assert "/api/v1/icp/{icp_id}" in paths
    assert "/api/v1/hunter/start" in paths
    assert "/api/v1/hunter/status" in paths
