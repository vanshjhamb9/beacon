from __future__ import annotations

import uuid
from datetime import UTC, datetime

from communication_gateway.models.types import (
    CalendarBookingResult,
    CalendarEventRequest,
    ProviderName,
)


class SandboxCalendarProvider:
    name = ProviderName.SANDBOX_CALENDAR

    def __init__(self) -> None:
        self.bookings: list[dict] = []

    def book(self, request: CalendarEventRequest) -> CalendarBookingResult:
        event_id = f"sandbox-cal-{uuid.uuid4()}"
        meeting_url = f"https://sandbox.beacon.local/meet/{event_id}"
        record = {
            "id": event_id,
            "title": request.title,
            "start_at": request.start_at.astimezone(UTC).isoformat(),
            "end_at": request.end_at.astimezone(UTC).isoformat(),
            "timezone": request.timezone,
            "attendees": list(request.attendees),
            "meeting_url": meeting_url,
        }
        self.bookings.append(record)
        return CalendarBookingResult(
            provider=self.name,
            event_id=event_id,
            meeting_url=meeting_url,
            status="booked",
            sandbox=True,
            raw=record,
        )
