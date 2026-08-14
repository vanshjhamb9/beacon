from __future__ import annotations

from typing import Any

import httpx

from communication_gateway.models.types import (
    CalendarBookingResult,
    CalendarEventRequest,
    ProviderName,
)


class OutlookCalendarProvider:
    name = ProviderName.OUTLOOK_CALENDAR
    API_BASE = "https://graph.microsoft.com/v1.0"

    def __init__(self, *, access_token: str) -> None:
        if not access_token:
            raise ValueError("Outlook Calendar access token is required")
        self.access_token = access_token

    def book(self, request: CalendarEventRequest) -> CalendarBookingResult:
        payload = {
            "subject": request.title,
            "body": {"contentType": "Text", "content": request.description},
            "start": {"dateTime": request.start_at.replace(tzinfo=None).isoformat(), "timeZone": request.timezone},
            "end": {"dateTime": request.end_at.replace(tzinfo=None).isoformat(), "timeZone": request.timezone},
            "attendees": [
                {"emailAddress": {"address": email}, "type": "required"} for email in request.attendees
            ],
            "location": {"displayName": request.location or ""},
        }
        data = self._request("POST", "/me/events", json=payload)
        return CalendarBookingResult(
            provider=self.name,
            event_id=str(data.get("id")),
            meeting_url=(data.get("onlineMeeting") or {}).get("joinUrl") or data.get("webLink"),
            status="booked",
            sandbox=False,
            raw=data,
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        with httpx.Client(timeout=45.0) as client:
            response = client.request(method, f"{self.API_BASE}{path}", headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
