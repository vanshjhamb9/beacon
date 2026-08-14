from __future__ import annotations

from typing import Any

import httpx

from communication_gateway.models.types import (
    CalendarBookingResult,
    CalendarEventRequest,
    ProviderName,
)


class GoogleCalendarProvider:
    name = ProviderName.GOOGLE_CALENDAR
    API_BASE = "https://www.googleapis.com/calendar/v3"

    def __init__(self, *, access_token: str) -> None:
        if not access_token:
            raise ValueError("Google Calendar access token is required")
        self.access_token = access_token

    def book(self, request: CalendarEventRequest) -> CalendarBookingResult:
        payload = {
            "summary": request.title,
            "description": request.description,
            "location": request.location,
            "start": {"dateTime": request.start_at.isoformat(), "timeZone": request.timezone},
            "end": {"dateTime": request.end_at.isoformat(), "timeZone": request.timezone},
            "attendees": [{"email": email} for email in request.attendees],
        }
        data = self._request("POST", "/calendars/primary/events", json=payload)
        return CalendarBookingResult(
            provider=self.name,
            event_id=str(data.get("id")),
            meeting_url=data.get("hangoutLink") or data.get("htmlLink"),
            status=str(data.get("status") or "confirmed"),
            sandbox=False,
            raw=data,
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with httpx.Client(timeout=45.0) as client:
            response = client.request(method, f"{self.API_BASE}{path}", headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
