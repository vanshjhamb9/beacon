from app.main import app


def test_campaign_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/campaigns" in paths
    assert "/api/v1/campaigns/{campaign_id}" in paths
    assert "/api/v1/campaigns/create/{company_id}" in paths
    assert "/api/v1/campaigns/approve/{campaign_id}" in paths
    assert "/api/v1/campaigns/pause/{campaign_id}" in paths
    assert "/api/v1/campaigns/cancel/{campaign_id}" in paths
    assert "/api/v1/campaigns/dashboard" in paths
