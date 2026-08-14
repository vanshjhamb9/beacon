from uuid import uuid4

from communication_gateway.foundation.idempotency import build_idempotency_key
from communication_gateway.models.types import (
    ChannelType,
    CommunicationMode,
    GatewayConfig,
    OutboundMessage,
    ProviderName,
)
from communication_gateway.services.gateway import CommunicationGatewayService


def test_e2e_approve_send_reply_domain_path() -> None:
    """Campaign-approved personalized email → send → simulated reply stop (domain E2E)."""
    campaign_id = uuid4()
    gateway = CommunicationGatewayService(
        GatewayConfig(mode=CommunicationMode.SANDBOX, allow_production_send=False)
    )
    message = OutboundMessage(
        channel=ChannelType.EMAIL,
        provider=ProviderName.SANDBOX_EMAIL,
        to_address="prospect@sandbox.example",
        subject="Personalized founder email",
        body_text="Hi — saw your funding round.",
        campaign_id=campaign_id,
        company_id=uuid4(),
        campaign_approved=True,
        require_campaign_approved=True,
        idempotency_key=build_idempotency_key(
            campaign_id=campaign_id,
            campaign_step_id=None,
            to_address="prospect@sandbox.example",
            subject="Personalized founder email",
        ),
    )
    # Reject without approval
    blocked = gateway.send_founder_approved(message.model_copy(update={"campaign_approved": False}))
    assert blocked.error_code == "approval_required"

    pack = gateway.sandbox_send_and_simulate_reply(message)
    assert pack["send"]["state"] == "sent"
    assert pack["reply"]["event_type"] in {"reply", "message"} or pack["reply"].get("body_text")
    assert pack["inbound_handling"]["campaign_stopped"] is True
    assert campaign_id in gateway.stopped_campaigns

    # Duplicate prevention on a fresh campaign (stop rules already fired above)
    fresh = message.model_copy(
        update={
            "campaign_id": uuid4(),
            "idempotency_key": message.idempotency_key,
        }
    )
    gateway.safety.record_send(idempotency_key=fresh.idempotency_key)
    again = gateway.send_now(fresh, duplicate_exists=False, sent_today=0)
    assert again.state.value == "cancelled"
    assert again.error_code == "duplicate_send"
