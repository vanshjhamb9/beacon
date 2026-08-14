from __future__ import annotations

from typing import Any

import httpx

from communication_gateway.models.types import (
    CalendarBookingResult,
    CalendarEventRequest,
    ProviderName,
)


class CalendlyHooks:
    """Calendly integration hooks (scheduled event tracking via API/webhooks)."""

    name = ProviderName.CALENDLY
    API_BASE = "https://api.calendly.com"

    def __init__(self, *, api_key: str | None = None) -> None:
        self.api_key = api_key

    def book(self, request: CalendarEventRequest) -> CalendarBookingResult:
        # Calendly bookings are invitee-driven; this records a booking intent/hook.
        if not self.api_key:
            raise ValueError("Calendly API key is required for production hooks")
        return CalendarBookingResult(
            provider=self.name,
            event_id=f"calendly-intent-{request.title[:24]}",
            meeting_url=None,
            status="intent_recorded",
            sandbox=False,
            raw={
                "title": request.title,
                "attendees": list(request.attendees),
                "timezone": request.timezone,
                "note": "Use Calendly webhook invitee.created for confirmed bookings",
            },
        )

    def list_scheduled_events(self, *, count: int = 20) -> list[dict[str, Any]]:
        if not self.api_key:
            raise ValueError("Calendly API key is required")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=45.0) as client:
            response = client.get(f"{self.API_BASE}/scheduled_events", headers=headers, params={"count": count})
            response.raise_for_status()
            data = response.json()
        return list(data.get("collection") or [])
