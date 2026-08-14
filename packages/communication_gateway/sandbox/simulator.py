from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from communication_gateway.models.types import (
    ChannelType,
    DeliveryState,
    InboundEvent,
    ProviderName,
)


class SandboxSimulator:
    """Simulate delivery, reads, replies, meetings, and failures without providers."""

    def simulate_delivery(self, *, provider_message_id: str, channel: ChannelType) -> InboundEvent:
        return InboundEvent(
            channel=channel,
            provider=self._provider_for(channel),
            event_type="delivered",
            provider_message_id=provider_message_id,
            occurred_at=datetime.now(UTC),
            payload={"state": DeliveryState.DELIVERED.value},
        )

    def simulate_read(self, *, provider_message_id: str, channel: ChannelType) -> InboundEvent:
        return InboundEvent(
            channel=channel,
            provider=self._provider_for(channel),
            event_type="read",
            provider_message_id=provider_message_id,
            occurred_at=datetime.now(UTC),
            payload={"state": DeliveryState.READ.value},
        )

    def simulate_reply(
        self,
        *,
        channel: ChannelType,
        from_address: str,
        body_text: str,
        thread_id: str | None = None,
        subject: str | None = None,
    ) -> InboundEvent:
        return InboundEvent(
            channel=channel,
            provider=self._provider_for(channel),
            event_type="reply",
            provider_message_id=f"sandbox-reply-{uuid.uuid4()}",
            thread_id=thread_id or f"sandbox-thread-{uuid.uuid4()}",
            conversation_id=thread_id,
            from_address=from_address,
            subject=subject or "Re: Beacon outreach",
            body_text=body_text,
            occurred_at=datetime.now(UTC),
            payload={"state": DeliveryState.REPLIED.value},
        )

    def simulate_meeting(
        self,
        *,
        title: str,
        attendee: str,
        start_at: datetime | None = None,
    ) -> InboundEvent:
        start = start_at or datetime.now(UTC)
        return InboundEvent(
            channel=ChannelType.CALENDAR,
            provider=ProviderName.SANDBOX_CALENDAR,
            event_type="meeting_booked",
            provider_message_id=f"sandbox-meeting-{uuid.uuid4()}",
            from_address=attendee,
            subject=title,
            body_text=f"Meeting booked with {attendee}",
            occurred_at=start,
            payload={"state": DeliveryState.MEETING.value, "title": title},
        )

    def simulate_failure(self, *, provider_message_id: str, channel: ChannelType, reason: str) -> InboundEvent:
        return InboundEvent(
            channel=channel,
            provider=self._provider_for(channel),
            event_type="failed",
            provider_message_id=provider_message_id,
            occurred_at=datetime.now(UTC),
            payload={"state": DeliveryState.FAILED.value, "reason": reason},
        )

    def build_scenario(self, name: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "id": str(uuid.uuid4()),
            "name": name,
            "steps": steps,
            "created_at": datetime.now(UTC).isoformat(),
            "mode": "sandbox",
        }

    def _provider_for(self, channel: ChannelType) -> ProviderName:
        if channel == ChannelType.EMAIL:
            return ProviderName.SANDBOX_EMAIL
        if channel == ChannelType.WHATSAPP:
            return ProviderName.SANDBOX_WHATSAPP
        return ProviderName.SANDBOX_CALENDAR
