from app.main import app


def test_revenue_hunter_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/revenue-hunter/taxonomy" in paths
    assert "/api/v1/revenue-hunter/dossiers" in paths
    assert "/api/v1/revenue-hunter/dossiers/{dossier_id}" in paths
    assert "/api/v1/revenue-hunter/dashboard" in paths
    assert "/api/v1/revenue-hunter/work-queue" in paths
    assert "/api/v1/revenue-hunter/work-queue/{item_id}/action" in paths
    assert "/api/v1/revenue-hunter/process" in paths
