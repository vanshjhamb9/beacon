from uuid import uuid4

from communication_gateway.foundation.idempotency import build_idempotency_key, webhook_fingerprint
from communication_gateway.models.types import (
    ChannelType,
    DeliveryState,
    GatewayConfig,
    OutboundMessage,
    ProviderName,
    CommunicationMode,
)
from communication_gateway.safety.controls import SafetyControls
from communication_gateway.services.gateway import CommunicationGatewayService


def test_safety_blocks_quota_and_duplicates() -> None:
    safety = SafetyControls(daily_email_quota=1)
    ok = safety.check_send(idempotency_key="a", campaign_stopped=False, sent_today=0)
    assert ok.allowed
    safety.record_send(idempotency_key="a")
    dup = safety.check_send(idempotency_key="a", campaign_stopped=False, sent_today=1)
    assert dup.allowed is False
    assert dup.code == "duplicate_send"
    quota = safety.check_send(idempotency_key="b", campaign_stopped=False, sent_today=1)
    assert quota.code == "quota_exceeded"
    stopped = safety.check_send(idempotency_key="c", campaign_stopped=True, stop_reason="reply_received")
    assert stopped.code == "campaign_stopped"


def test_idempotency_key_deterministic() -> None:
    cid = uuid4()
    a = build_idempotency_key(campaign_id=cid, campaign_step_id=None, to_address="A@X.com", subject="Hi")
    b = build_idempotency_key(campaign_id=cid, campaign_step_id=None, to_address="a@x.com", subject="Hi")
    assert a == b
    assert webhook_fingerprint("gmail", {"historyId": "99"}).startswith("gmail:")


def test_founder_approved_send_requires_approval() -> None:
    gateway = CommunicationGatewayService(
        GatewayConfig(mode=CommunicationMode.SANDBOX, allow_production_send=False)
    )
    message = OutboundMessage(
        channel=ChannelType.EMAIL,
        provider=ProviderName.SANDBOX_EMAIL,
        to_address="a@example.com",
        body_text="hello",
        campaign_id=uuid4(),
        campaign_approved=False,
        require_campaign_approved=True,
    )
    result = gateway.send_founder_approved(message)
    assert result.state == DeliveryState.CANCELLED
    assert result.error_code == "approval_required"


def test_sandbox_send_still_works() -> None:
    gateway = CommunicationGatewayService(
        GatewayConfig(mode=CommunicationMode.SANDBOX, allow_production_send=False)
    )
    message = OutboundMessage(
        channel=ChannelType.EMAIL,
        provider=ProviderName.SANDBOX_EMAIL,
        to_address="a@example.com",
        subject="Hi",
        body_text="hello",
        campaign_id=uuid4(),
        campaign_approved=True,
        idempotency_key="k1",
    )
    pack = gateway.sandbox_send_and_simulate_reply(message)
    assert pack["send"]["state"] == "sent"
    assert pack["inbound_handling"]["campaign_stopped"] is True
