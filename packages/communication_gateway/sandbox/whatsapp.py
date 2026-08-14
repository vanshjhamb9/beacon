from __future__ import annotations

import uuid
from datetime import UTC, datetime

from communication_gateway.models.types import (
    DeliveryResult,
    DeliveryState,
    OutboundMessage,
    ProviderName,
)


class SandboxWhatsAppProvider:
    name = ProviderName.SANDBOX_WHATSAPP

    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send(self, message: OutboundMessage) -> DeliveryResult:
        message_id = f"sandbox-wa-{uuid.uuid4()}"
        conversation_id = message.conversation_id or f"sandbox-wa-conv-{uuid.uuid4()}"
        record = {
            "id": message_id,
            "conversation_id": conversation_id,
            "to": message.to_address,
            "body": message.body_text,
            "sent_at": datetime.now(UTC).isoformat(),
        }
        self.sent.append(record)
        return DeliveryResult(
            state=DeliveryState.SENT,
            provider=self.name,
            provider_message_id=message_id,
            conversation_id=conversation_id,
            sandbox=True,
            raw=record,
        )
