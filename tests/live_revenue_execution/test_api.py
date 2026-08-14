from app.main import app


def test_live_revenue_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/live-revenue/company/{company_id}" in paths
    assert "/api/v1/live-revenue/refresh/{company_id}" in paths
    assert "/api/v1/live-revenue/approval-center" in paths
    assert "/api/v1/live-revenue/proposals" in paths
    assert "/api/v1/live-revenue/dashboard" in paths
    assert "/api/v1/live-revenue/command-center" in paths
    assert "/api/v1/live-revenue/track" in paths


def test_campaign_reject_and_bulk_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/campaigns/reject/{campaign_id}" in paths
    assert "/api/v1/campaigns/bulk-approve" in paths
    assert "/api/v1/campaigns/bulk-reject" in paths
