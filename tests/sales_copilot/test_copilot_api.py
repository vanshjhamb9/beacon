from app.main import app


def test_copilot_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/copilot/company/{company_id}" in paths
    assert "/api/v1/copilot/opportunity/{opportunity_id}" in paths
    assert "/api/v1/copilot/generate/{entity_id}" in paths
    assert "/api/v1/copilot/regenerate/{entity_id}" in paths
    assert "/api/v1/copilot/review/{package_id}" in paths
    assert "/api/v1/copilot/history/{entity_id}" in paths
