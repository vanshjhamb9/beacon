from __future__ import annotations

import uuid
from datetime import UTC, datetime

from communication_gateway.models.types import (
    DeliveryResult,
    DeliveryState,
    OutboundMessage,
    ProviderName,
)


class SandboxEmailProvider:
    name = ProviderName.SANDBOX_EMAIL

    def __init__(self) -> None:
        self.sent: list[dict] = []
        self.drafts: list[dict] = []

    def send(self, message: OutboundMessage) -> DeliveryResult:
        message_id = f"sandbox-email-{uuid.uuid4()}"
        thread_id = message.thread_id or f"sandbox-thread-{uuid.uuid4()}"
        record = {
            "id": message_id,
            "thread_id": thread_id,
            "to": message.to_address,
            "subject": message.subject,
            "body_text": message.body_text,
            "body_html": message.body_html,
            "sent_at": datetime.now(UTC).isoformat(),
            "campaign_id": str(message.campaign_id) if message.campaign_id else None,
        }
        self.sent.append(record)
        return DeliveryResult(
            state=DeliveryState.SENT,
            provider=self.name,
            provider_message_id=message_id,
            thread_id=thread_id,
            conversation_id=thread_id,
            sandbox=True,
            raw=record,
        )

    def create_draft(self, message: OutboundMessage) -> DeliveryResult:
        draft_id = f"sandbox-draft-{uuid.uuid4()}"
        record = {
            "id": draft_id,
            "to": message.to_address,
            "subject": message.subject,
            "body_text": message.body_text,
        }
        self.drafts.append(record)
        return DeliveryResult(
            state=DeliveryState.DRAFT,
            provider=self.name,
            provider_message_id=draft_id,
            thread_id=message.thread_id,
            sandbox=True,
            raw=record,
        )
