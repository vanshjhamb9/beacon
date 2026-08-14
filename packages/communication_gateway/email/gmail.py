from __future__ import annotations

import base64
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx

from communication_gateway.models.types import (
    ChannelType,
    DeliveryResult,
    DeliveryState,
    InboundEvent,
    OutboundMessage,
    ProviderName,
)


class GmailProvider:
    """Official Gmail API provider (OAuth bearer token required)."""

    name = ProviderName.GMAIL
    API_BASE = "https://gmail.googleapis.com/gmail/v1"

    def __init__(self, *, access_token: str, daily_quota: int = 500) -> None:
        if not access_token:
            raise ValueError("Gmail access token is required")
        self.access_token = access_token
        self.daily_quota = daily_quota
        self._sent_today = 0

    def send(self, message: OutboundMessage) -> DeliveryResult:
        if self._sent_today >= self.daily_quota:
            return DeliveryResult(
                state=DeliveryState.FAILED,
                provider=self.name,
                sandbox=False,
                error_code="quota_exceeded",
                error_message="Gmail daily quota exceeded",
            )
        raw = self._build_raw(message)
        payload: dict[str, Any] = {"raw": raw}
        if message.thread_id:
            payload["threadId"] = message.thread_id
        data = self._request("POST", "/users/me/messages/send", json=payload)
        self._sent_today += 1
        return DeliveryResult(
            state=DeliveryState.SENT,
            provider=self.name,
            provider_message_id=data.get("id"),
            thread_id=data.get("threadId"),
            conversation_id=data.get("threadId"),
            sandbox=False,
            raw=data,
        )

    def create_draft(self, message: OutboundMessage) -> DeliveryResult:
        raw = self._build_raw(message)
        payload = {"message": {"raw": raw}}
        if message.thread_id:
            payload["message"]["threadId"] = message.thread_id
        data = self._request("POST", "/users/me/drafts", json=payload)
        msg = data.get("message") or {}
        return DeliveryResult(
            state=DeliveryState.DRAFT,
            provider=self.name,
            provider_message_id=msg.get("id") or data.get("id"),
            thread_id=msg.get("threadId"),
            sandbox=False,
            raw=data,
        )

    def get_profile_history_id(self) -> str | None:
        data = self._request("GET", "/users/me/profile")
        history_id = data.get("historyId")
        return str(history_id) if history_id is not None else None

    def list_history(self, *, start_history_id: str, max_results: int = 50) -> dict[str, Any]:
        return self._request(
            "GET",
            "/users/me/history",
            params={
                "startHistoryId": start_history_id,
                "historyTypes": "messageAdded",
                "maxResults": max_results,
            },
        )

    def get_message(self, message_id: str, *, format: str = "full") -> dict[str, Any]:
        return self._request("GET", f"/users/me/messages/{message_id}", params={"format": format})

    def fetch_inbound_replies(
        self,
        *,
        start_history_id: str | None,
        max_messages: int = 20,
    ) -> tuple[list[InboundEvent], str | None]:
        """Fetch new inbound messages since history id and map to InboundEvent replies."""
        history_id = start_history_id or self.get_profile_history_id()
        if not history_id:
            return [], None
        history = self.list_history(start_history_id=history_id, max_results=max_messages)
        message_ids: list[str] = []
        for row in history.get("history") or []:
            for added in row.get("messagesAdded") or []:
                msg = added.get("message") or {}
                mid = msg.get("id")
                if mid:
                    message_ids.append(str(mid))
        events: list[InboundEvent] = []
        for mid in message_ids[:max_messages]:
            raw = self.get_message(mid)
            label_ids = {str(x) for x in (raw.get("labelIds") or [])}
            if "SENT" in label_ids and "INBOX" not in label_ids:
                continue
            headers = {
                str(h.get("name", "")).lower(): str(h.get("value") or "")
                for h in ((raw.get("payload") or {}).get("headers") or [])
            }
            events.append(
                InboundEvent(
                    channel=ChannelType.EMAIL,
                    provider=ProviderName.GMAIL,
                    event_type="reply",
                    provider_message_id=str(raw.get("id") or mid),
                    thread_id=str(raw.get("threadId") or "") or None,
                    conversation_id=str(raw.get("threadId") or "") or None,
                    from_address=headers.get("from"),
                    subject=headers.get("subject"),
                    body_text=self._extract_body(raw) or str(raw.get("snippet") or ""),
                    payload=raw,
                )
            )
        next_history = str(history.get("historyId") or history_id)
        return events, next_history

    def _extract_body(self, raw: dict[str, Any]) -> str:
        payload = raw.get("payload") or {}
        if payload.get("body", {}).get("data"):
            return self._b64(payload["body"]["data"])
        for part in payload.get("parts") or []:
            mime = str(part.get("mimeType") or "")
            data = (part.get("body") or {}).get("data")
            if data and mime.startswith("text/plain"):
                return self._b64(data)
        return ""

    def _b64(self, value: str) -> str:
        padded = value + "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="replace")

    def _build_raw(self, message: OutboundMessage) -> str:
        meta = message.metadata or {}
        has_attachments = bool(message.attachments)
        root = MIMEMultipart("mixed" if has_attachments else "alternative")
        root["To"] = message.to_address
        if message.from_address:
            root["From"] = message.from_address
        root["Subject"] = message.subject or ""
        tracking_id = str(meta.get("tracking_id") or "")
        if tracking_id:
            root["X-Beacon-Tracking-Id"] = tracking_id
        if message.campaign_id:
            root["X-Beacon-Campaign-Id"] = str(message.campaign_id)
        unsubscribe = meta.get("unsubscribe_url")
        if unsubscribe:
            root["List-Unsubscribe"] = f"<{unsubscribe}>"
            root["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

        alt = MIMEMultipart("alternative") if has_attachments else root
        alt.attach(MIMEText(message.body_text or "", "plain", "utf-8"))
        if message.body_html:
            alt.attach(MIMEText(message.body_html, "html", "utf-8"))
        if has_attachments:
            root.attach(alt)
            for attachment in message.attachments:
                raw = b""
                if attachment.content_base64:
                    raw = base64.b64decode(attachment.content_base64)
                part = MIMEApplication(raw, Name=attachment.filename)
                part.add_header("Content-Disposition", "attachment", filename=attachment.filename)
                if attachment.content_type:
                    part.set_type(attachment.content_type)
                root.attach(part)
        return base64.urlsafe_b64encode(root.as_bytes()).decode("utf-8")

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with httpx.Client(timeout=45.0) as client:
            response = client.request(method, f"{self.API_BASE}{path}", headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
