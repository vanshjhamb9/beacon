from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from communication_gateway.models.types import ChannelType, InboundEvent, ProviderName
from communication_gateway.whatsapp.meta import MetaWhatsAppProvider


class WebhookHandler:
    def parse_meta_whatsapp(self, payload: dict[str, Any]) -> list[InboundEvent]:
        events: list[InboundEvent] = []
        for entry in payload.get("entry") or []:
            for change in entry.get("changes") or []:
                value = change.get("value") or {}
                for message in value.get("messages") or []:
                    events.append(
                        InboundEvent(
                            channel=ChannelType.WHATSAPP,
                            provider=ProviderName.META_WHATSAPP,
                            event_type="reply" if message.get("type") == "text" else str(message.get("type")),
                            provider_message_id=message.get("id"),
                            conversation_id=(message.get("context") or {}).get("id"),
                            from_address=message.get("from"),
                            body_text=((message.get("text") or {}).get("body") or ""),
                            occurred_at=datetime.now(UTC),
                            payload=message,
                        )
                    )
                for status in value.get("statuses") or []:
                    events.append(
                        InboundEvent(
                            channel=ChannelType.WHATSAPP,
                            provider=ProviderName.META_WHATSAPP,
                            event_type=str(status.get("status") or "status"),
                            provider_message_id=status.get("id"),
                            conversation_id=status.get("conversation", {}).get("id")
                            if isinstance(status.get("conversation"), dict)
                            else None,
                            occurred_at=datetime.now(UTC),
                            payload=status,
                        )
                    )
        return events

    def parse_gmail_pubsub(self, payload: dict[str, Any]) -> list[InboundEvent]:
        # Gmail push notifications are history hints; full fetch is done by worker.
        return [
            InboundEvent(
                channel=ChannelType.EMAIL,
                provider=ProviderName.GMAIL,
                event_type="history",
                payload=payload,
                occurred_at=datetime.now(UTC),
            )
        ]

    def parse_calendly(self, payload: dict[str, Any]) -> list[InboundEvent]:
        event = payload.get("event")
        body = payload.get("payload") or {}
        if event == "invitee.created":
            return [
                InboundEvent(
                    channel=ChannelType.CALENDAR,
                    provider=ProviderName.CALENDLY,
                    event_type="meeting_booked",
                    provider_message_id=str(body.get("uri") or body.get("email") or ""),
                    from_address=body.get("email"),
                    subject=(body.get("scheduled_event") or {}).get("name"),
                    body_text="Calendly invitee created",
                    occurred_at=datetime.now(UTC),
                    payload=payload,
                )
            ]
        return []

    def verify_meta(self, provider: MetaWhatsAppProvider, *, signature: str, body: bytes) -> bool:
        return provider.validate_signature(signature_header=signature, payload=body)
