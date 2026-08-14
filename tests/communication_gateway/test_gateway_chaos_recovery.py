from communication_gateway import CommunicationGatewayService, OutboundMessage
from communication_gateway.models.types import ChannelType, DeliveryState, ProviderName, QueueName
from communication_gateway.queue.manager import InMemoryQueueManager


def test_retry_then_dead_letter_recovery() -> None:
    queue = InMemoryQueueManager()
    item = queue.enqueue(QueueName.OUTGOING, {"broken": True}, max_attempts=2)
    queue.retry(item, error="transient", delay_seconds=0)
    assert queue.depth()[QueueName.RETRY.value] == 1
    retried = queue.dequeue(QueueName.RETRY)
    assert retried is not None
    dead = queue.retry(retried, error="still broken", delay_seconds=0)
    assert dead.queue == QueueName.DEAD_LETTER
    assert queue.depth()[QueueName.DEAD_LETTER.value] == 1


def test_gateway_isolates_bad_queue_payload() -> None:
    gateway = CommunicationGatewayService()
    gateway.queue.enqueue(QueueName.OUTGOING, {"not": "a message"}, max_attempts=1)
    results = gateway.process_queue(limit=5)
    assert results
    assert results[0].state == DeliveryState.FAILED
    assert gateway.queue.depth()[QueueName.DEAD_LETTER.value] >= 1


def test_manual_stop_cancels_enqueue() -> None:
    from uuid import uuid4

    from communication_gateway.models.types import StopReason

    gateway = CommunicationGatewayService()
    campaign_id = uuid4()
    gateway.stop_campaign(campaign_id, reason=StopReason.MANUAL_STOP)
    outcome = gateway.enqueue_message(
        OutboundMessage(
            channel=ChannelType.EMAIL,
            provider=ProviderName.SANDBOX_EMAIL,
            to_address="a@example.com",
            body_text="nope",
            campaign_id=campaign_id,
        )
    )
    assert outcome["state"] == DeliveryState.CANCELLED.value
