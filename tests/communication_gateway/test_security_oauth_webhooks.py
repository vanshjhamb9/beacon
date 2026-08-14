from communication_gateway.models.types import GatewayConfig, ProviderName
from communication_gateway.oauth.flows import OAuthFlowService
from communication_gateway.security.crypto import SecretBox, hmac_sha256_hex
from communication_gateway.webhooks.handlers import WebhookHandler


def test_secret_box_roundtrip_and_redaction() -> None:
    box = SecretBox("unit-test-key")
    token = "refresh-token-super-secret"
    encrypted = box.encrypt(token)
    assert encrypted != token
    assert box.decrypt(encrypted) == token
    assert "super-secret" not in box.redact(token)


def test_oauth_authorize_urls_do_not_hardcode_secrets() -> None:
    oauth = OAuthFlowService(
        GatewayConfig(
            gmail_client_id="google-client",
            microsoft_client_id="ms-client",
            microsoft_tenant_id="common",
            oauth_redirect_uri="http://localhost:8000/callback",
        )
    )
    google = oauth.authorize_url(ProviderName.GMAIL, state="abc")
    microsoft = oauth.authorize_url(ProviderName.MICROSOFT_GRAPH, state="xyz")
    assert "accounts.google.com" in google
    assert "google-client" in google
    assert "login.microsoftonline.com" in microsoft
    assert "ms-client" in microsoft
    assert "client_secret" not in google
    assert "client_secret" not in microsoft


def test_meta_and_calendly_webhook_parsers() -> None:
    handler = WebhookHandler()
    wa = handler.parse_meta_whatsapp(
        {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "id": "wamid.1",
                                        "from": "15551234567",
                                        "type": "text",
                                        "text": {"body": "Interested"},
                                        "context": {"id": "conv-1"},
                                    }
                                ],
                                "statuses": [{"id": "wamid.0", "status": "delivered", "conversation": {"id": "conv-1"}}],
                            }
                        }
                    ]
                }
            ]
        }
    )
    assert any(event.event_type == "reply" for event in wa)
    assert any(event.event_type == "delivered" for event in wa)

    calendly = handler.parse_calendly(
        {
            "event": "invitee.created",
            "payload": {
                "email": "buyer@example.com",
                "uri": "https://calendly.com/events/1",
                "scheduled_event": {"name": "Discovery"},
            },
        }
    )
    assert calendly[0].event_type == "meeting_booked"


def test_hmac_signature_format() -> None:
    digest = hmac_sha256_hex("app-secret", b'{"ok":true}')
    assert len(digest) == 64
