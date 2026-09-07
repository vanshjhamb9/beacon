"""Outbound send adapter — Communication Gateway with dry-run fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from comai_partner_outreach.config import PartnerOutreachConfig

logger = logging.getLogger(__name__)


@dataclass
class SendResult:
    ok: bool
    dry_run: bool = False
    provider_message_id: str = ""
    thread_id: str = ""
    state: str = ""
    error: str = ""
    detail: dict[str, Any] | None = None


def send_partner_email(
    *,
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str,
    config: PartnerOutreachConfig,
    campaign_id: str | None = None,
) -> SendResult:
    if config.dry_run or not config.enabled:
        logger.info(
            "COMAI partner outreach dry-run send to=%s subject=%s",
            to_email,
            subject[:80],
        )
        return SendResult(
            ok=True,
            dry_run=True,
            provider_message_id=f"dryrun-{to_email}",
            thread_id=f"dryrun-thread-{to_email}",
            state="sent",
            detail={"dry_run": True},
        )

    try:
        from communication_gateway import CommunicationGatewayService, GatewayConfig, OutboundMessage
        from communication_gateway.models.types import ChannelType, CommunicationMode, ProviderName

        gw_config = GatewayConfig(
            mode=CommunicationMode.PRODUCTION,
            allow_production_send=True,
        )
        gateway = CommunicationGatewayService(gw_config)
        message = OutboundMessage(
            channel=ChannelType.EMAIL,
            provider=ProviderName.GMAIL,
            to_address=to_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            metadata={"program": "comai_partner_outreach", "campaign_id": campaign_id or ""},
        )
        result = gateway.send_now(message)
        state = getattr(result.state, "value", str(result.state))
        ok = state in ("sent", "delivered", "queued")
        return SendResult(
            ok=ok,
            dry_run=False,
            provider_message_id=str(getattr(result, "provider_message_id", "") or ""),
            thread_id=str(getattr(result, "thread_id", "") or ""),
            state=state,
            error="" if ok else str(getattr(result, "error", "") or state),
            detail={"provider": str(getattr(result, "provider", ""))},
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Partner outreach send failed: %s", exc)
        return SendResult(ok=False, error=str(exc), state="failed")
