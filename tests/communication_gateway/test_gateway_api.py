from app.main import app


def test_communication_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/communication/mode" in paths
    assert "/api/v1/communication/queues" in paths
    assert "/api/v1/communication/sandbox/send" in paths
    assert "/api/v1/communication/send" in paths
    assert "/api/v1/communication/campaigns/{campaign_id}/execute" in paths
    assert "/api/v1/communication/oauth/status" in paths
    assert "/api/v1/communication/oauth/refresh" in paths
    assert "/api/v1/communication/sync/gmail-replies" in paths
    assert "/api/v1/communication/e2e/approve-send-reply" in paths
    assert "/api/v1/communication/sandbox/meeting" in paths
    assert "/api/v1/communication/oauth/authorize" in paths
    assert "/api/v1/communication/oauth/callback" in paths
    assert "/api/v1/communication/webhooks/meta" in paths
    assert "/api/v1/communication/webhooks/calendly" in paths
    assert "/api/v1/communication/metrics" in paths
    assert "/api/v1/inbox" in paths
    assert "/api/v1/qa/health" in paths
    assert "/api/v1/qa/e2e/sandbox" in paths
    assert "/api/v1/system-health" in paths
