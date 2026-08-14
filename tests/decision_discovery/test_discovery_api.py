from app.main import app


def test_decision_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/decision/company/{company_id}" in paths
    assert "/api/v1/decision/opportunity/{opportunity_id}" in paths
    assert "/api/v1/decision/refresh/{entity_id}" in paths
    assert "/api/v1/decision/search" in paths
