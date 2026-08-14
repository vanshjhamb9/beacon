import time
from uuid import uuid4

from communication_gateway import CommunicationGatewayService, OutboundMessage
from communication_gateway.foundation.idempotency import build_idempotency_key
from communication_gateway.models.types import ChannelType, ProviderName
from communication_gateway.safety.controls import SafetyControls


def test_sandbox_send_throughput_budget() -> None:
    gateway = CommunicationGatewayService()
    started = time.perf_counter()
    for idx in range(100):
        gateway.send_now(
            OutboundMessage(
                channel=ChannelType.EMAIL,
                provider=ProviderName.SANDBOX_EMAIL,
                to_address=f"user{idx}@example.com",
                body_text="perf",
                campaign_id=uuid4(),
                idempotency_key=f"perf-{idx}",
            )
        )
    elapsed = time.perf_counter() - started
    assert elapsed < 2.0


def test_queue_process_budget() -> None:
    gateway = CommunicationGatewayService()
    for idx in range(50):
        gateway.enqueue_message(
            OutboundMessage(
                channel=ChannelType.EMAIL,
                provider=ProviderName.SANDBOX_EMAIL,
                to_address=f"q{idx}@example.com",
                body_text="queued",
                idempotency_key=f"q-{idx}",
            )
        )
    started = time.perf_counter()
    results = gateway.process_queue(limit=50)
    assert len(results) == 50
    assert (time.perf_counter() - started) < 2.0


def test_safety_controls_budget() -> None:
    safety = SafetyControls(daily_email_quota=10_000)
    started = time.perf_counter()
    for idx in range(5_000):
        key = build_idempotency_key(
            campaign_id=uuid4(),
            campaign_step_id=None,
            to_address=f"u{idx}@x.com",
            subject="s",
        )
        decision = safety.check_send(idempotency_key=key, campaign_stopped=False, sent_today=idx)
        if decision.allowed:
            safety.record_send(idempotency_key=key)
    assert (time.perf_counter() - started) < 1.5
