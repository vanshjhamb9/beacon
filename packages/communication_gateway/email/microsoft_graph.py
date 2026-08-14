from __future__ import annotations

from typing import Any

import httpx

from communication_gateway.models.types import (
    DeliveryResult,
    DeliveryState,
    OutboundMessage,
    ProviderName,
)


class MicrosoftGraphEmailProvider:
    """Microsoft Graph mail send/draft provider."""

    name = ProviderName.MICROSOFT_GRAPH
    API_BASE = "https://graph.microsoft.com/v1.0"

    def __init__(self, *, access_token: str) -> None:
        if not access_token:
            raise ValueError("Microsoft Graph access token is required")
        self.access_token = access_token

    def send(self, message: OutboundMessage) -> DeliveryResult:
        payload = self._message_payload(message, save_to_sent=True)
        data = self._request("POST", "/me/sendMail", json=payload)
        # sendMail returns 202 with empty body
        return DeliveryResult(
            state=DeliveryState.SENT,
            provider=self.name,
            provider_message_id=None,
            thread_id=message.thread_id,
            conversation_id=message.conversation_id,
            sandbox=False,
            raw=data or {"accepted": True},
        )

    def create_draft(self, message: OutboundMessage) -> DeliveryResult:
        payload = self._message_body(message)
        data = self._request("POST", "/me/messages", json=payload)
        return DeliveryResult(
            state=DeliveryState.DRAFT,
            provider=self.name,
            provider_message_id=data.get("id"),
            thread_id=data.get("conversationId"),
            conversation_id=data.get("conversationId"),
            sandbox=False,
            raw=data,
        )

    def _message_body(self, message: OutboundMessage) -> dict[str, Any]:
        return {
            "subject": message.subject or "",
            "body": {
                "contentType": "HTML" if message.body_html else "Text",
                "content": message.body_html or message.body_text,
            },
            "toRecipients": [{"emailAddress": {"address": message.to_address}}],
        }

    def _message_payload(self, message: OutboundMessage, *, save_to_sent: bool) -> dict[str, Any]:
        return {"message": self._message_body(message), "saveToSentItems": save_to_sent}

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        with httpx.Client(timeout=45.0) as client:
            response = client.request(method, f"{self.API_BASE}{path}", headers=headers, **kwargs)
            response.raise_for_status()
            if response.content:
                return response.json()
            return {}
