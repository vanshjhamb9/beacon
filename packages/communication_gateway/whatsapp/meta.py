from __future__ import annotations

from typing import Any

import httpx

from communication_gateway.models.types import (
    DeliveryResult,
    DeliveryState,
    OutboundMessage,
    ProviderName,
)
from communication_gateway.security.crypto import constant_time_compare, hmac_sha256_hex


class MetaWhatsAppProvider:
    """Official Meta WhatsApp Business Cloud API provider."""

    name = ProviderName.META_WHATSAPP
    API_BASE = "https://graph.facebook.com/v19.0"

    def __init__(
        self,
        *,
        access_token: str,
        phone_number_id: str,
        app_secret: str | None = None,
        verify_token: str | None = None,
    ) -> None:
        if not access_token or not phone_number_id:
            raise ValueError("Meta WhatsApp access token and phone_number_id are required")
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.app_secret = app_secret
        self.verify_token = verify_token

    def send(self, message: OutboundMessage) -> DeliveryResult:
        meta = message.metadata or {}
        template = meta.get("template_name")
        media = meta.get("media") or {}
        interactive = meta.get("interactive") or {}
        if template:
            payload: dict[str, Any] = {
                "messaging_product": "whatsapp",
                "to": message.to_address,
                "type": "template",
                "template": {
                    "name": template,
                    "language": {"code": meta.get("template_language", "en_US")},
                },
            }
            components = meta.get("template_components")
            if components:
                payload["template"]["components"] = components
        elif media.get("type") in {"image", "document"} and media.get("link"):
            mtype = str(media["type"])
            payload = {
                "messaging_product": "whatsapp",
                "to": message.to_address,
                "type": mtype,
                mtype: {"link": media["link"]},
            }
            if media.get("caption"):
                payload[mtype]["caption"] = media["caption"]
            if media.get("filename") and mtype == "document":
                payload[mtype]["filename"] = media["filename"]
        elif interactive.get("type") == "button" and interactive.get("buttons"):
            payload = {
                "messaging_product": "whatsapp",
                "to": message.to_address,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": message.body_text},
                    "action": {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {"id": b.get("id") or f"btn_{i}", "title": b.get("text") or b.get("title") or "OK"},
                            }
                            for i, b in enumerate(interactive.get("buttons") or [])
                        ][:3]
                    },
                },
            }
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": message.to_address,
                "type": "text",
                "text": {"body": message.body_text},
            }
        data = self._request("POST", f"/{self.phone_number_id}/messages", json=payload)
        messages = data.get("messages") or [{}]
        return DeliveryResult(
            state=DeliveryState.SENT,
            provider=self.name,
            provider_message_id=(messages[0] or {}).get("id"),
            conversation_id=message.conversation_id,
            sandbox=False,
            raw=data,
        )

    def verify_webhook(self, *, mode: str, token: str, challenge: str) -> str | None:
        if mode == "subscribe" and self.verify_token and constant_time_compare(token, self.verify_token):
            return challenge
        return None

    def validate_signature(self, *, signature_header: str, payload: bytes) -> bool:
        if not self.app_secret:
            return False
        expected = "sha256=" + hmac_sha256_hex(self.app_secret, payload)
        return constant_time_compare(signature_header, expected)

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with httpx.Client(timeout=45.0) as client:
            response = client.request(method, f"{self.API_BASE}{path}", headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
