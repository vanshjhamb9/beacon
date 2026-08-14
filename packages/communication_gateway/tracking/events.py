from __future__ import annotations

from communication_gateway.models.types import DeliveryState, InboundEvent, StopReason


STATE_FROM_EVENT: dict[str, DeliveryState] = {
    "delivered": DeliveryState.DELIVERED,
    "read": DeliveryState.READ,
    "clicked": DeliveryState.CLICKED,
    "reply": DeliveryState.REPLIED,
    "replied": DeliveryState.REPLIED,
    "meeting_booked": DeliveryState.MEETING,
    "failed": DeliveryState.FAILED,
    "bounce": DeliveryState.FAILED,
}


class DeliveryTracker:
    def map_state(self, event: InboundEvent) -> DeliveryState:
        return STATE_FROM_EVENT.get(event.event_type, DeliveryState.SENT)

    def should_stop_campaign(self, event: InboundEvent) -> StopReason | None:
        if event.event_type in {"reply", "replied"}:
            return StopReason.REPLY_RECEIVED
        if event.event_type == "meeting_booked":
            return StopReason.MEETING_BOOKED
        return None
