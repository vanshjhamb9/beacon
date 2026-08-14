from uuid import uuid4

from communication_gateway import CommunicationGatewayService, GatewayConfig, OutboundMessage
from communication_gateway.models.types import (
    CalendarEventRequest,
    ChannelType,
    CommunicationMode,
    DeliveryState,
    ProviderName,
    QueueName,
    StopReason,
)
from datetime import UTC, datetime, timedelta


def test_sandbox_is_forced_when_production_send_disabled() -> None:
    gateway = CommunicationGatewayService(
        GatewayConfig(mode=CommunicationMode.PRODUCTION, allow_production_send=False)
    )
    assert gateway.is_sandbox is True
    result = gateway.send_now(
        OutboundMessage(
            channel=ChannelType.EMAIL,
            provider=ProviderName.GMAIL,
            to_address="a@example.com",
            body_text="hi",
        )
    )
    assert result.sandbox is True
    assert result.provider == ProviderName.SANDBOX_EMAIL


def test_queue_priority_and_dead_letter_paths() -> None:
    gateway = CommunicationGatewayService()
    gateway.enqueue_message(
        OutboundMessage(
            channel=ChannelType.EMAIL,
            provider=ProviderName.SANDBOX_EMAIL,
            to_address="a@example.com",
            body_text="priority",
            priority=1,
        ),
        priority=1,
    )
    depths = gateway.queue.depth()
    assert depths[QueueName.PRIORITY.value] >= 1
    results = gateway.process_queue(limit=5)
    assert results
    assert results[0].state == DeliveryState.SENT


def test_stop_on_reply_and_meeting() -> None:
    gateway = CommunicationGatewayService()
    campaign_id = uuid4()
    result = gateway.sandbox_send_and_simulate_reply(
        OutboundMessage(
            channel=ChannelType.EMAIL,
            provider=ProviderName.SANDBOX_EMAIL,
            to_address="buyer@example.com",
            subject="Hello",
            body_text="Offer",
            campaign_id=campaign_id,
        )
    )
    assert result["inbound_handling"]["campaign_stopped"] is True
    assert campaign_id in gateway.stopped_campaigns
    assert gateway.stop_reasons[campaign_id] == StopReason.REPLY_RECEIVED

    blocked = gateway.enqueue_message(
        OutboundMessage(
            channel=ChannelType.EMAIL,
            provider=ProviderName.SANDBOX_EMAIL,
            to_address="buyer@example.com",
            body_text="follow up",
            campaign_id=campaign_id,
        )
    )
    assert blocked["queued"] is False

    booking = gateway.book_meeting(
        CalendarEventRequest(
            title="Intro",
            start_at=datetime.now(UTC) + timedelta(days=1),
            end_at=datetime.now(UTC) + timedelta(days=1, hours=1),
            attendees=["buyer@example.com"],
            campaign_id=campaign_id,
        )
    )
    assert booking.sandbox is True


def test_whatsapp_sandbox_send() -> None:
    gateway = CommunicationGatewayService()
    result = gateway.send_now(
        OutboundMessage(
            channel=ChannelType.WHATSAPP,
            provider=ProviderName.SANDBOX_WHATSAPP,
            to_address="15551234567",
            body_text="Hello",
        )
    )
    assert result.state == DeliveryState.SENT
    assert result.provider == ProviderName.SANDBOX_WHATSAPP
