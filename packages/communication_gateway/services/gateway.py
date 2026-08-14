from __future__ import annotations

from typing import Any
from uuid import UUID

from communication_gateway.models.types import (
    CalendarBookingResult,
    CalendarEventRequest,
    ChannelType,
    CommunicationMode,
    DeliveryResult,
    DeliveryState,
    GatewayConfig,
    InboundEvent,
    OutboundMessage,
    ProviderName,
    QueueName,
    StopReason,
)
from communication_gateway.providers.factory import ProviderFactory
from communication_gateway.queue.manager import InMemoryQueueManager
from communication_gateway.safety.controls import SafetyControls, SafetyDecision
from communication_gateway.sandbox.simulator import SandboxSimulator
from communication_gateway.tracking.events import DeliveryTracker


class CommunicationGatewayService:
    """Sandbox-first communication gateway. Production send requires explicit enablement."""

    def __init__(
        self,
        config: GatewayConfig | None = None,
        *,
        factory: ProviderFactory | None = None,
        queue: InMemoryQueueManager | None = None,
        tracker: DeliveryTracker | None = None,
        simulator: SandboxSimulator | None = None,
        safety: SafetyControls | None = None,
        stopped_campaigns: set[UUID] | None = None,
    ) -> None:
        self.config = config or GatewayConfig()
        self.factory = factory or ProviderFactory(self.config)
        self.queue = queue or InMemoryQueueManager()
        self.tracker = tracker or DeliveryTracker()
        self.simulator = simulator or SandboxSimulator()
        self.safety = safety or SafetyControls(daily_email_quota=self.config.daily_email_quota)
        self.stopped_campaigns = stopped_campaigns if stopped_campaigns is not None else set()
        self.stop_reasons: dict[UUID, StopReason] = {}

    @property
    def is_sandbox(self) -> bool:
        return self.config.mode == CommunicationMode.SANDBOX or not self.config.allow_production_send

    def with_access_tokens(self, access_tokens: dict[str, str]) -> CommunicationGatewayService:
        """Return a gateway using the same config/queues with OAuth tokens injected."""
        return CommunicationGatewayService(
            self.config,
            factory=ProviderFactory(self.config, access_tokens=access_tokens),
            queue=self.queue,
            tracker=self.tracker,
            simulator=self.simulator,
            safety=self.safety,
            stopped_campaigns=self.stopped_campaigns,
        )

    def enqueue_message(self, message: OutboundMessage, *, priority: int | None = None) -> dict[str, Any]:
        gate = self._preflight(message)
        if not gate.allowed:
            return {
                "queued": False,
                "state": DeliveryState.CANCELLED.value,
                "reason": gate.reason,
                "code": gate.code,
                "evidence": gate.evidence,
            }
        queue_name = QueueName.PRIORITY if (priority or message.priority) < 50 else QueueName.OUTGOING
        delay = 0.0
        if message.scheduled_at is not None:
            queue_name = QueueName.DELAYED
            delay = max(0.0, message.scheduled_at.timestamp() - __import__("time").time())
        item = self.queue.enqueue(
            queue_name,
            message.model_dump(mode="json"),
            priority=priority if priority is not None else message.priority,
            delay_seconds=delay,
            max_attempts=self.config.max_retries,
        )
        return {"queued": True, "queue": queue_name.value, "item_id": item.id, "state": DeliveryState.QUEUED.value}

    def send_now(
        self,
        message: OutboundMessage,
        *,
        duplicate_exists: bool = False,
        sent_today: int = 0,
    ) -> DeliveryResult:
        gate = self._preflight(message, duplicate_exists=duplicate_exists, sent_today=sent_today)
        if not gate.allowed:
            return DeliveryResult(
                state=DeliveryState.CANCELLED,
                provider=ProviderName.SANDBOX_EMAIL
                if message.channel == ChannelType.EMAIL
                else ProviderName.SANDBOX_WHATSAPP,
                sandbox=self.is_sandbox,
                error_code=gate.code or "blocked",
                error_message=gate.reason or "Send blocked by safety controls",
                raw={"evidence": gate.evidence},
            )
        if message.channel == ChannelType.EMAIL:
            provider = self.factory.email_provider(message.provider if message.provider else None)
            if message.is_draft:
                return provider.create_draft(message)
            result = provider.send(message)
            if result.state == DeliveryState.SENT:
                self.safety.record_send(idempotency_key=message.idempotency_key)
            return result
        if message.channel == ChannelType.WHATSAPP:
            provider = self.factory.whatsapp_provider()
            return provider.send(message)
        raise ValueError("Use book_meeting for calendar channel")

    def send_founder_approved(
        self,
        message: OutboundMessage,
        *,
        duplicate_exists: bool = False,
        sent_today: int = 0,
    ) -> DeliveryResult:
        """Send path for founder-approved personalized email (sandbox or gated production)."""
        approved = message.model_copy(
            update={
                "require_campaign_approved": True,
                "campaign_approved": True if message.campaign_approved else message.campaign_approved,
            }
        )
        # Explicit founder approval must be set by platform layer
        if not message.campaign_approved and message.campaign_id is not None:
            return DeliveryResult(
                state=DeliveryState.CANCELLED,
                provider=message.provider,
                sandbox=self.is_sandbox,
                error_code="approval_required",
                error_message="Campaign must be founder-approved before send",
            )
        return self.send_now(approved, duplicate_exists=duplicate_exists, sent_today=sent_today)

    def process_queue(self, *, limit: int = 25) -> list[DeliveryResult]:
        results: list[DeliveryResult] = []
        for queue_name in (QueueName.PRIORITY, QueueName.OUTGOING, QueueName.RETRY, QueueName.DELAYED, QueueName.WORKER):
            while len(results) < limit:
                item = self.queue.dequeue(queue_name)
                if item is None:
                    break
                try:
                    message = OutboundMessage(**item.payload)
                    result = self.send_now(message)
                    if result.state == DeliveryState.FAILED:
                        self.queue.retry(item, error=result.error_message or "send_failed")
                    results.append(result)
                except Exception as exc:  # noqa: BLE001 - queue must isolate failures
                    self.queue.retry(item, error=str(exc))
                    results.append(
                        DeliveryResult(
                            state=DeliveryState.FAILED,
                            provider=ProviderName.SANDBOX_EMAIL,
                            sandbox=self.is_sandbox,
                            error_code="exception",
                            error_message=str(exc),
                        )
                    )
        return results

    def book_meeting(self, request: CalendarEventRequest, *, provider: ProviderName | None = None) -> CalendarBookingResult:
        calendar = self.factory.calendar_provider(provider)
        return calendar.book(request)

    def handle_inbound(self, event: InboundEvent, *, campaign_id: UUID | None = None) -> dict[str, Any]:
        state = self.tracker.map_state(event)
        stop = self.tracker.should_stop_campaign(event)
        stopped = False
        if stop and campaign_id is not None:
            self.stop_campaign(campaign_id, reason=stop)
            stopped = True
        return {
            "state": state.value,
            "stop_reason": stop.value if stop else None,
            "campaign_stopped": stopped,
            "event_type": event.event_type,
        }

    def stop_campaign(self, campaign_id: UUID, *, reason: StopReason = StopReason.MANUAL_STOP) -> None:
        self.stopped_campaigns.add(campaign_id)
        self.stop_reasons[campaign_id] = reason

    def load_stopped_campaigns(self, stops: dict[UUID, StopReason]) -> None:
        for campaign_id, reason in stops.items():
            self.stopped_campaigns.add(campaign_id)
            self.stop_reasons[campaign_id] = reason

    def sandbox_send_and_simulate_reply(
        self,
        message: OutboundMessage,
        *,
        reply_body: str = "Thanks — let's meet next week.",
    ) -> dict[str, Any]:
        if not self.is_sandbox:
            raise RuntimeError("sandbox_send_and_simulate_reply requires sandbox mode")
        send_result = self.send_now(message)
        delivery = self.simulator.simulate_delivery(
            provider_message_id=send_result.provider_message_id or "",
            channel=message.channel,
        )
        reply = self.simulator.simulate_reply(
            channel=message.channel,
            from_address=message.to_address,
            body_text=reply_body,
            thread_id=send_result.thread_id,
            subject=f"Re: {message.subject or 'Beacon'}",
        )
        inbound = self.handle_inbound(reply, campaign_id=message.campaign_id)
        return {
            "send": send_result.model_dump(mode="json"),
            "delivery": delivery.model_dump(mode="json"),
            "reply": reply.model_dump(mode="json"),
            "inbound_handling": inbound,
            "mode": "sandbox",
        }

    def queue_health(self) -> dict[str, Any]:
        return {
            "mode": self.config.mode.value,
            "allow_production_send": self.config.allow_production_send,
            "sandbox": self.is_sandbox,
            "depths": self.queue.depth(),
            "stopped_campaigns": len(self.stopped_campaigns),
        }

    def _preflight(
        self,
        message: OutboundMessage,
        *,
        duplicate_exists: bool = False,
        sent_today: int = 0,
    ) -> SafetyDecision:
        if message.require_campaign_approved and not message.campaign_approved:
            return SafetyDecision(
                allowed=False,
                reason="Campaign must be founder-approved before send",
                code="approval_required",
                evidence=["require_campaign_approved:true"],
            )
        stopped = bool(message.campaign_id and message.campaign_id in self.stopped_campaigns)
        reason = None
        if stopped and message.campaign_id:
            stop = self.stop_reasons.get(message.campaign_id)
            reason = stop.value if stop else "stopped"
        return self.safety.check_send(
            idempotency_key=message.idempotency_key,
            campaign_stopped=stopped,
            stop_reason=reason,
            sent_today=sent_today,
            duplicate_exists=duplicate_exists,
        )
