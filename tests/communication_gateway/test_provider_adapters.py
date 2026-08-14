from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from communication_gateway.calendar.calendly import CalendlyHooks
from communication_gateway.calendar.google_calendar import GoogleCalendarProvider
from communication_gateway.calendar.outlook import OutlookCalendarProvider
from communication_gateway.email.gmail import GmailProvider
from communication_gateway.email.microsoft_graph import MicrosoftGraphEmailProvider
from communication_gateway.models.types import (
    CalendarEventRequest,
    ChannelType,
    DeliveryState,
    OutboundMessage,
    ProviderName,
)
from communication_gateway.providers.factory import ProviderFactory
from communication_gateway.models.types import CommunicationMode, GatewayConfig
from communication_gateway.sandbox.email import SandboxEmailProvider
from communication_gateway.whatsapp.meta import MetaWhatsAppProvider


def _email_message(**overrides: object) -> OutboundMessage:
    payload = {
        "channel": ChannelType.EMAIL,
        "provider": ProviderName.GMAIL,
        "to_address": "buyer@example.com",
        "subject": "Hello",
        "body_text": "Plain",
        "body_html": "<p>Plain</p>",
        "thread_id": "thread-1",
    }
    payload.update(overrides)
    return OutboundMessage(**payload)  # type: ignore[arg-type]


def test_gmail_send_and_draft_with_mock() -> None:
    provider = GmailProvider(access_token="token", daily_quota=2)
    with patch.object(provider, "_request", return_value={"id": "m1", "threadId": "t1"}) as mocked:
        sent = provider.send(_email_message())
        draft = provider.create_draft(_email_message(is_draft=True))
    assert sent.state == DeliveryState.SENT
    assert draft.state == DeliveryState.DRAFT
    assert mocked.call_count == 2
    provider._sent_today = 2
    blocked = provider.send(_email_message())
    assert blocked.error_code == "quota_exceeded"


def test_microsoft_graph_send_mock() -> None:
    provider = MicrosoftGraphEmailProvider(access_token="token")
    with patch.object(provider, "_request", return_value={"id": "graph-1", "conversationId": "c1"}):
        result = provider.send(_email_message(provider=ProviderName.MICROSOFT_GRAPH))
    assert result.state == DeliveryState.SENT
    assert result.provider == ProviderName.MICROSOFT_GRAPH


def test_meta_whatsapp_template_and_signature() -> None:
    provider = MetaWhatsAppProvider(
        access_token="token",
        phone_number_id="123",
        app_secret="secret",
        verify_token="verify",
    )
    with patch.object(provider, "_request", return_value={"messages": [{"id": "wamid.1"}]}):
        text = provider.send(
            OutboundMessage(
                channel=ChannelType.WHATSAPP,
                provider=ProviderName.META_WHATSAPP,
                to_address="15551234567",
                body_text="hi",
            )
        )
        templated = provider.send(
            OutboundMessage(
                channel=ChannelType.WHATSAPP,
                provider=ProviderName.META_WHATSAPP,
                to_address="15551234567",
                body_text="",
                metadata={"template_name": "hello_world", "template_language": "en_US"},
            )
        )
    assert text.state == DeliveryState.SENT
    assert templated.state == DeliveryState.SENT
    assert provider.verify_webhook(mode="subscribe", token="verify", challenge="123") == "123"
    assert provider.validate_signature(signature_header="sha256=deadbeef", payload=b"{}") is False


def test_calendar_providers_mock() -> None:
    request = CalendarEventRequest(
        title="Meet",
        start_at=datetime.now(UTC),
        end_at=datetime.now(UTC) + timedelta(hours=1),
        attendees=["a@example.com"],
    )
    google = GoogleCalendarProvider(access_token="token")
    outlook = OutlookCalendarProvider(access_token="token")
    calendly = CalendlyHooks(api_key="key")
    with patch.object(google, "_request", return_value={"id": "g1", "hangoutLink": "https://meet"}):
        g = google.book(request)
    with patch.object(outlook, "_request", return_value={"id": "o1", "onlineMeeting": {"joinUrl": "https://teams"}}):
        o = outlook.book(request)
    c = calendly.book(request)
    assert g.event_id == "g1"
    assert o.event_id == "o1"
    assert c.status == "intent_recorded"


def test_factory_production_requires_tokens() -> None:
    factory = ProviderFactory(
        GatewayConfig(mode=CommunicationMode.PRODUCTION, allow_production_send=True),
        access_tokens={"gmail": "tok", "google_calendar": "tok", "email": "tok", "calendar": "tok"},
    )
    assert factory.email_provider(ProviderName.GMAIL).name == ProviderName.GMAIL
    assert factory.calendar_provider(ProviderName.GOOGLE_CALENDAR).name == ProviderName.GOOGLE_CALENDAR


def test_sandbox_draft() -> None:
    draft = SandboxEmailProvider().create_draft(_email_message(is_draft=True))
    assert draft.state == DeliveryState.DRAFT
