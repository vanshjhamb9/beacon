from app.main import app


def test_founder_os_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/founder-os/command-center" in paths
    assert "/api/v1/founder-os/refresh" in paths
    assert "/api/v1/founder-os/brief" in paths
    assert "/api/v1/founder-os/assistant" in paths
    assert "/api/v1/founder-os/tasks" in paths
    assert "/api/v1/founder-os/tasks/{task_id}/complete" in paths
    assert "/api/v1/founder-os/kpis" in paths
    assert "/api/v1/founder-os/recommendations" in paths
    assert "/api/v1/founder-os/proposals" in paths
    assert "/api/v1/founder-os/meetings" in paths
    assert "/api/v1/founder-os/timeline/{company_id}" in paths
    assert "/api/v1/founder-os/analytics/track" in paths
