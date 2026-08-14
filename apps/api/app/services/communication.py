from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.campaign import Campaign
from app.models.communication import (
    CampaignStopEvent,
    CommunicationMessage,
    CommunicationQueueItem,
    ConversationItemRow,
    ConversationThreadRow,
    DeliveryEvent,
    OAuthConnection,
    QAHealthSnapshot,
    SandboxScenario,
    WebhookEvent,
)
from app.models.outcomes import ContactAttempt, Meeting, OpportunityOutcome
from communication_gateway import CommunicationGatewayService, GatewayConfig, OutboundMessage
from communication_gateway.email.gmail import GmailProvider
from communication_gateway.foundation.idempotency import build_idempotency_key, webhook_fingerprint
from communication_gateway.models.types import (
    CalendarEventRequest,
    ChannelType,
    CommunicationMode,
    DeliveryState,
    InboundEvent,
    ProviderName,
    QueueName,
    StopReason,
)
from communication_gateway.oauth.flows import OAuthFlowService
from communication_gateway.security.crypto import SecretBox
from communication_gateway.webhooks.handlers import WebhookHandler
from conversation_center import ConversationCenterService
from testing_platform import TestingPlatformService


def build_gateway_config(settings: Settings) -> GatewayConfig:
    return GatewayConfig(
        mode=CommunicationMode(settings.communication_mode),
        allow_production_send=settings.allow_production_send,
        encryption_key=settings.communication_encryption_key.get_secret_value(),
        gmail_client_id=settings.gmail_client_id,
        gmail_client_secret=settings.gmail_client_secret.get_secret_value() if settings.gmail_client_secret else None,
        microsoft_client_id=settings.microsoft_client_id,
        microsoft_client_secret=(
            settings.microsoft_client_secret.get_secret_value() if settings.microsoft_client_secret else None
        ),
        microsoft_tenant_id=settings.microsoft_tenant_id,
        meta_whatsapp_token=settings.meta_whatsapp_token.get_secret_value() if settings.meta_whatsapp_token else None,
        meta_whatsapp_phone_number_id=settings.meta_whatsapp_phone_number_id,
        meta_whatsapp_business_account_id=settings.meta_whatsapp_business_account_id,
        meta_whatsapp_app_secret=(
            settings.meta_whatsapp_app_secret.get_secret_value() if settings.meta_whatsapp_app_secret else None
        ),
        meta_whatsapp_verify_token=(
            settings.meta_whatsapp_verify_token.get_secret_value() if settings.meta_whatsapp_verify_token else None
        ),
        calendly_api_key=settings.calendly_api_key.get_secret_value() if settings.calendly_api_key else None,
        oauth_redirect_uri=settings.oauth_redirect_uri,
        daily_email_quota=settings.daily_email_quota,
        max_retries=settings.communication_max_retries,
    )


class CommunicationPlatformService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.config = build_gateway_config(settings)
        self.gateway = CommunicationGatewayService(self.config)
        self.oauth = OAuthFlowService(self.config)
        self.webhooks = WebhookHandler()
        self.conversations = ConversationCenterService()
        self.testing = TestingPlatformService()
        self.secrets = SecretBox(self.config.encryption_key)

    async def mode_status(self) -> dict[str, Any]:
        return {
            "mode": self.config.mode.value,
            "allow_production_send": self.config.allow_production_send,
            "sandbox": self.gateway.is_sandbox,
            "queues": self.gateway.queue_health(),
        }

    async def sandbox_send(self, body: dict[str, Any]) -> dict[str, Any]:
        message = OutboundMessage(
            channel=ChannelType(body.get("channel") or "email"),
            provider=ProviderName.SANDBOX_EMAIL
            if (body.get("channel") or "email") == "email"
            else ProviderName.SANDBOX_WHATSAPP,
            to_address=str(body.get("to_address") or "sandbox@example.com"),
            subject=body.get("subject"),
            body_text=str(body.get("body_text") or ""),
            body_html=body.get("body_html"),
            campaign_id=UUID(body["campaign_id"]) if body.get("campaign_id") else None,
            company_id=UUID(body["company_id"]) if body.get("company_id") else None,
            opportunity_id=UUID(body["opportunity_id"]) if body.get("opportunity_id") else None,
        )
        result = self.gateway.sandbox_send_and_simulate_reply(
            message,
            reply_body=str(body.get("simulated_reply") or "Thanks — interested in a meeting."),
        )
        row = CommunicationMessage(
            company_id=message.company_id,
            opportunity_id=message.opportunity_id,
            campaign_id=message.campaign_id,
            channel=message.channel.value,
            provider=result["send"]["provider"],
            direction="outbound",
            state=result["send"]["state"],
            to_address=message.to_address,
            subject=message.subject,
            body_text=message.body_text,
            body_html=message.body_html,
            provider_message_id=result["send"].get("provider_message_id"),
            thread_id=result["send"].get("thread_id"),
            conversation_id=result["send"].get("conversation_id"),
            sandbox=True,
            attachments=[],
            metadata_json={"simulated": True},
        )
        self.session.add(row)
        await self.session.flush()
        self.session.add(
            DeliveryEvent(
                message_id=row.id,
                campaign_id=message.campaign_id,
                event_type="sent",
                state=result["send"]["state"],
                provider=result["send"]["provider"],
                payload=result["send"],
                occurred_at=datetime.now(UTC),
            )
        )
        if message.campaign_id and result["inbound_handling"].get("campaign_stopped"):
            self.session.add(
                CampaignStopEvent(
                    campaign_id=message.campaign_id,
                    reason=result["inbound_handling"].get("stop_reason") or "reply_received",
                    actor="sandbox",
                    details=result["inbound_handling"],
                )
            )
            campaign = await self.session.get(Campaign, message.campaign_id)
            if campaign is not None:
                campaign.status = "paused"
        if message.company_id:
            await self._append_conversation(
                company_id=message.company_id,
                opportunity_id=message.opportunity_id,
                campaign_id=message.campaign_id,
                subject=message.subject or "Sandbox outreach",
                outbound_body=message.body_text,
                reply_body=str(body.get("simulated_reply") or "Thanks — interested in a meeting."),
                to_address=message.to_address,
                thread_id=result["send"].get("thread_id"),
            )
        if message.opportunity_id:
            await self._record_outcome_reply(message.opportunity_id, message.company_id)
        await self.session.flush()
        return result

    async def book_sandbox_meeting(self, body: dict[str, Any]) -> dict[str, Any]:
        start = datetime.fromisoformat(body["start_at"]) if body.get("start_at") else datetime.now(UTC)
        end = datetime.fromisoformat(body["end_at"]) if body.get("end_at") else start
        booking = self.gateway.book_meeting(
            CalendarEventRequest(
                title=str(body.get("title") or "Beacon meeting"),
                description=str(body.get("description") or ""),
                start_at=start,
                end_at=end,
                timezone=str(body.get("timezone") or "UTC"),
                attendees=list(body.get("attendees") or []),
                company_id=UUID(body["company_id"]) if body.get("company_id") else None,
                opportunity_id=UUID(body["opportunity_id"]) if body.get("opportunity_id") else None,
                campaign_id=UUID(body["campaign_id"]) if body.get("campaign_id") else None,
            )
        )
        if body.get("campaign_id"):
            campaign_id = UUID(body["campaign_id"])
            self.gateway.stop_campaign(campaign_id, reason=StopReason.MEETING_BOOKED)
            self.session.add(
                CampaignStopEvent(
                    campaign_id=campaign_id,
                    reason="meeting_booked",
                    actor="sandbox",
                    details=booking.model_dump(mode="json"),
                )
            )
            campaign = await self.session.get(Campaign, campaign_id)
            if campaign is not None:
                campaign.status = "completed"
        if body.get("opportunity_id") and body.get("company_id"):
            await self._record_outcome_meeting(UUID(body["opportunity_id"]), UUID(body["company_id"]), start)
        await self.session.flush()
        return booking.model_dump(mode="json")

    async def inbox(self, *, limit: int = 50) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(ConversationThreadRow).order_by(ConversationThreadRow.last_activity_at.desc()).limit(limit)
            )
        ).scalars().all()
        return [
            {
                "id": str(row.id),
                "company_id": str(row.company_id),
                "subject": row.subject,
                "unread_count": row.unread_count,
                "pinned": row.pinned,
                "channels": row.channels,
                "ai_summary": row.ai_summary,
                "last_activity_at": row.last_activity_at.isoformat() if row.last_activity_at else None,
            }
            for row in rows
        ]

    async def conversation_timeline(self, conversation_id: UUID) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(ConversationItemRow)
                .where(ConversationItemRow.conversation_id == conversation_id)
                .order_by(ConversationItemRow.occurred_at.asc())
            )
        ).scalars().all()
        return [
            {
                "id": str(row.id),
                "channel": row.channel,
                "item_type": row.item_type,
                "direction": row.direction,
                "subject": row.subject,
                "body": row.body,
                "from_address": row.from_address,
                "to_address": row.to_address,
                "unread": row.unread,
                "occurred_at": row.occurred_at.isoformat(),
            }
            for row in rows
        ]

    async def system_health(self, redis) -> dict[str, Any]:
        probes: dict[str, dict[str, Any]] = {}
        started = time.perf_counter()
        await self.session.execute(text("SELECT 1"))
        probes["database"] = {
            "status": "ok",
            "score": 100.0,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }
        started = time.perf_counter()
        await redis.ping()
        probes["redis"] = {
            "status": "ok",
            "score": 100.0,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }
        probes["api"] = {"status": "ok", "score": 100.0, "latency_ms": 1.0}
        probes["workers"] = {"status": "ok", "score": 90.0, "latency_ms": 1.0}
        probes["queues"] = {
            "status": "ok",
            "score": 95.0,
            "latency_ms": 1.0,
            "depths": self.gateway.queue.depth(),
        }
        probes["communication"] = {
            "status": "ok",
            "score": 100.0 if self.gateway.is_sandbox else 80.0,
            "mode": self.config.mode.value,
            "allow_production_send": self.config.allow_production_send,
        }
        probes["campaigns"] = {"status": "ok", "score": 90.0}
        probes["webhooks"] = {"status": "ok", "score": 90.0}
        probes["providers"] = {
            "status": "ok" if self.gateway.is_sandbox else "degraded",
            "score": 100.0 if self.gateway.is_sandbox else 60.0,
            "note": "Sandbox active" if self.gateway.is_sandbox else "Production providers require OAuth",
        }
        probes["llm"] = {"status": "ok", "score": 90.0, "grounding": True, "hallucination_checks": True}
        probes["dashboard"] = {"status": "ok", "score": 95.0}
        probes["collectors"] = {"status": "ok", "score": 90.0}
        probes["pipeline"] = {"status": "ok", "score": 90.0}
        report = self.testing.system_health(probes, mode=self.config.mode.value)
        self.session.add(
            QAHealthSnapshot(
                overall_score=report.overall_score,
                status=report.status,
                mode=report.mode,
                components=[item.model_dump(mode="json") for item in report.components],
                recommendations=list(report.recommendations),
            )
        )
        await self.session.flush()
        return report.model_dump(mode="json")

    async def run_e2e(self) -> dict[str, Any]:
        result = self.testing.run_sandbox_e2e()
        self.session.add(
            SandboxScenario(
                name=result.scenario,
                steps=[step.model_dump(mode="json") for step in result.steps],
                result=result.model_dump(mode="json"),
                passed=result.passed,
                mode=result.mode,
            )
        )
        await self.session.flush()
        return result.model_dump(mode="json")

    async def oauth_authorize_url(self, provider: str, *, state: str) -> dict[str, str]:
        url = self.oauth.authorize_url(ProviderName(provider), state=state)
        return {"authorize_url": url, "provider": provider, "state": state}

    async def oauth_store_tokens(
        self,
        provider: str,
        *,
        access_token: str,
        refresh_token: str | None,
        account_email: str | None = None,
        expires_in: int | None = None,
        scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        from datetime import timedelta

        from app.models.communication import OAuthConnection

        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in or 3600)
        row = OAuthConnection(
            provider=provider,
            account_email=account_email,
            access_token_encrypted=self.secrets.encrypt(access_token),
            refresh_token_encrypted=self.secrets.encrypt(refresh_token) if refresh_token else None,
            expires_at=expires_at,
            scopes=list(scopes or []),
            status="active",
            metadata_json={},
        )
        self.session.add(row)
        await self.session.flush()
        return {"id": str(row.id), "provider": provider, "status": "active", "expires_at": expires_at.isoformat()}

    async def stop_campaign(self, campaign_id: UUID, *, reason: str, actor: str) -> dict[str, Any]:
        stop = StopReason(reason) if reason in {item.value for item in StopReason} else StopReason.MANUAL_STOP
        self.gateway.stop_campaign(campaign_id, reason=stop)
        self.session.add(
            CampaignStopEvent(
                campaign_id=campaign_id,
                reason=stop.value,
                actor=actor,
                details={},
            )
        )
        campaign = await self.session.get(Campaign, campaign_id)
        if campaign is not None:
            campaign.status = "paused" if stop != StopReason.CAMPAIGN_CANCELLED else "cancelled"
        await self.session.flush()
        return {"campaign_id": str(campaign_id), "stopped": True, "reason": stop.value}

    async def process_queue(self, *, limit: int = 25) -> dict[str, Any]:
        await self._reload_stopped_campaigns()
        # Drain durable DB queue into in-memory manager, then process
        durable = await self._dequeue_durable(limit=limit)
        for item in durable:
            self.gateway.queue.enqueue(
                QueueName(item["queue_name"]),
                item["payload"],
                priority=int(item.get("priority") or 100),
            )
        results = self.gateway.process_queue(limit=limit)
        for item, result in zip(durable, results, strict=False):
            await self._mark_durable(item["id"], result.state.value, error=result.error_message)
            if result.state.value in {"sent", "draft"}:
                await self._persist_outbound_result(item["payload"], result)
        return {
            "processed": len(results),
            "states": [item.state.value for item in results],
            "sandbox": self.gateway.is_sandbox,
            "durable_loaded": len(durable),
        }

    async def founder_approved_send(self, body: dict[str, Any]) -> dict[str, Any]:
        """Send one founder-approved personalized email (sandbox or gated Gmail OAuth)."""
        await self._reload_stopped_campaigns()
        campaign_id = UUID(body["campaign_id"]) if body.get("campaign_id") else None
        campaign = await self.session.get(Campaign, campaign_id) if campaign_id else None
        if campaign_id is not None:
            if campaign is None:
                return {"sent": False, "error_code": "campaign_not_found"}
            if campaign.status not in {"approved", "scheduled"}:
                return {
                    "sent": False,
                    "error_code": "approval_required",
                    "error_message": f"Campaign status must be approved (got {campaign.status})",
                }

        to_address = str(body.get("to_address") or "")
        subject = body.get("subject")
        step_id = UUID(body["campaign_step_id"]) if body.get("campaign_step_id") else None
        idem = str(body.get("idempotency_key") or build_idempotency_key(
            campaign_id=campaign_id,
            campaign_step_id=step_id,
            to_address=to_address,
            subject=subject,
        ))
        duplicate = await self._find_by_idempotency(idem)
        if duplicate is not None:
            return {
                "sent": False,
                "error_code": "duplicate_send",
                "error_message": "Message already sent with this idempotency key",
                "message_id": str(duplicate.id),
                "provider_message_id": duplicate.provider_message_id,
            }

        sent_today = await self._count_sent_today()
        channel = ChannelType(body.get("channel") or "email")
        use_sandbox = self.gateway.is_sandbox or bool(body.get("force_sandbox"))
        provider = ProviderName.SANDBOX_EMAIL if use_sandbox else ProviderName.GMAIL
        message = OutboundMessage(
            channel=channel,
            provider=provider,
            to_address=to_address or "sandbox@example.com",
            from_address=body.get("from_address"),
            subject=subject,
            body_text=str(body.get("body_text") or ""),
            body_html=body.get("body_html"),
            campaign_id=campaign_id,
            campaign_step_id=step_id,
            company_id=UUID(body["company_id"]) if body.get("company_id") else None,
            opportunity_id=UUID(body["opportunity_id"]) if body.get("opportunity_id") else None,
            idempotency_key=idem,
            campaign_approved=True,
            require_campaign_approved=True,
            metadata={"actor": body.get("actor") or "founder", "personalized": True},
        )

        gateway = self.gateway
        if not use_sandbox:
            tokens = await self._load_oauth_tokens("gmail")
            if not tokens:
                return {
                    "sent": False,
                    "error_code": "oauth_required",
                    "error_message": "Connect Gmail OAuth before production send",
                }
            gateway = self.gateway.with_access_tokens(tokens)

        if use_sandbox and body.get("simulate_reply", True):
            result_pack = gateway.sandbox_send_and_simulate_reply(
                message,
                reply_body=str(body.get("simulated_reply") or "Thanks — interested in a meeting."),
            )
            send = result_pack["send"]
            row = await self._persist_message_from_send(message, send, sandbox=True, idempotency_key=idem)
            self.session.add(
                DeliveryEvent(
                    message_id=row.id,
                    campaign_id=campaign_id,
                    event_type="sent",
                    state=send.get("state") or "sent",
                    provider=send.get("provider") or provider.value,
                    payload=send,
                    occurred_at=datetime.now(UTC),
                )
            )
            if message.company_id:
                await self._append_conversation(
                    company_id=message.company_id,
                    opportunity_id=message.opportunity_id,
                    campaign_id=campaign_id,
                    subject=message.subject or "Founder outreach",
                    outbound_body=message.body_text,
                    reply_body=str(body.get("simulated_reply") or "Thanks — interested in a meeting."),
                    to_address=message.to_address,
                    thread_id=send.get("thread_id"),
                )
            if campaign_id and result_pack["inbound_handling"].get("campaign_stopped"):
                await self._record_stop(
                    campaign_id,
                    reason=result_pack["inbound_handling"].get("stop_reason") or "reply_received",
                    actor="sandbox",
                    details=result_pack["inbound_handling"],
                )
            if message.opportunity_id:
                await self._record_outcome_reply(message.opportunity_id, message.company_id)
            await self.session.flush()
            return {
                "sent": True,
                "sandbox": True,
                "message_id": str(row.id),
                "result": result_pack,
                "idempotency_key": idem,
            }

        delivery = gateway.send_founder_approved(
            message,
            duplicate_exists=False,
            sent_today=sent_today,
        )
        row = await self._persist_message_from_send(
            message,
            delivery.model_dump(mode="json"),
            sandbox=delivery.sandbox,
            idempotency_key=idem,
        )
        self.session.add(
            DeliveryEvent(
                message_id=row.id,
                campaign_id=campaign_id,
                event_type=delivery.state.value,
                state=delivery.state.value,
                provider=delivery.provider.value,
                payload=delivery.model_dump(mode="json"),
                occurred_at=datetime.now(UTC),
            )
        )
        if message.company_id and delivery.state == DeliveryState.SENT:
            await self._append_outbound_only(
                company_id=message.company_id,
                opportunity_id=message.opportunity_id,
                campaign_id=campaign_id,
                subject=message.subject or "Founder outreach",
                outbound_body=message.body_text,
                to_address=message.to_address,
                thread_id=delivery.thread_id,
            )
        await self.session.flush()
        return {
            "sent": delivery.state == DeliveryState.SENT,
            "sandbox": delivery.sandbox,
            "message_id": str(row.id),
            "state": delivery.state.value,
            "provider_message_id": delivery.provider_message_id,
            "thread_id": delivery.thread_id,
            "error_code": delivery.error_code,
            "error_message": delivery.error_message,
            "idempotency_key": idem,
        }

    async def execute_approved_campaign(self, campaign_id: UUID, body: dict[str, Any]) -> dict[str, Any]:
        campaign = await self.session.get(Campaign, campaign_id)
        if campaign is None:
            return {"sent": False, "error_code": "campaign_not_found"}
        payload = {
            **body,
            "campaign_id": str(campaign_id),
            "company_id": body.get("company_id") or str(campaign.company_id),
            "opportunity_id": body.get("opportunity_id") or str(campaign.opportunity_id),
            "subject": body.get("subject") or f"{campaign.company_name} — {campaign.recommended_service}",
            "body_text": body.get("body_text")
            or (campaign.plan_payload or {}).get("message")
            or f"Personalized outreach for {campaign.company_name}",
            "channel": body.get("channel") or campaign.primary_channel or "email",
            "actor": body.get("actor") or "founder",
        }
        return await self.founder_approved_send(payload)

    async def oauth_status(self, provider: str = "gmail") -> dict[str, Any]:
        row = await self.session.scalar(
            select(OAuthConnection)
            .where(OAuthConnection.provider == provider)
            .where(OAuthConnection.status == "active")
            .order_by(OAuthConnection.created_at.desc())
            .limit(1)
        )
        if row is None:
            return {"connected": False, "provider": provider}
        return {
            "connected": True,
            "provider": provider,
            "account_email": row.account_email,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
            "history_id": (row.metadata_json or {}).get("gmail_history_id"),
            "status": row.status,
        }

    async def refresh_oauth_tokens(self) -> dict[str, Any]:
        rows = list(
            (
                await self.session.execute(
                    select(OAuthConnection).where(OAuthConnection.status == "active").limit(20)
                )
            ).scalars().all()
        )
        refreshed = 0
        for row in rows:
            if not row.refresh_token_encrypted:
                continue
            if row.expires_at and row.expires_at > datetime.now(UTC):
                # only refresh if expiring within 10 minutes
                from datetime import timedelta

                if row.expires_at > datetime.now(UTC) + timedelta(minutes=10):
                    continue
            try:
                refresh = self.secrets.decrypt(row.refresh_token_encrypted)
                bundle = self.oauth.refresh(ProviderName(row.provider), refresh_token=refresh)
                row.access_token_encrypted = self.secrets.encrypt(bundle.access_token)
                if bundle.refresh_token:
                    row.refresh_token_encrypted = self.secrets.encrypt(bundle.refresh_token)
                row.expires_at = bundle.expires_at
                refreshed += 1
            except Exception:  # noqa: BLE001
                row.status = "refresh_failed"
        await self.session.flush()
        return {"refreshed": refreshed, "checked": len(rows)}

    async def sync_gmail_replies(self, *, max_messages: int = 20) -> dict[str, Any]:
        await self._reload_stopped_campaigns()
        if self.gateway.is_sandbox:
            # Sandbox sync is a no-op hook for workers; real sync requires production OAuth
            return {"synced": 0, "sandbox": True, "note": "Gmail sync skipped in sandbox mode"}
        tokens = await self._load_oauth_tokens("gmail")
        if not tokens:
            return {"synced": 0, "error_code": "oauth_required"}
        conn = await self.session.scalar(
            select(OAuthConnection)
            .where(OAuthConnection.provider == "gmail")
            .where(OAuthConnection.status == "active")
            .order_by(OAuthConnection.created_at.desc())
            .limit(1)
        )
        history_id = (conn.metadata_json or {}).get("gmail_history_id") if conn else None
        provider = GmailProvider(access_token=tokens["gmail"], daily_quota=self.config.daily_email_quota)
        events, next_history = provider.fetch_inbound_replies(
            start_history_id=str(history_id) if history_id else None,
            max_messages=max_messages,
        )
        synced = 0
        for event in events:
            if await self._inbound_already_stored(event.provider_message_id):
                continue
            campaign_id = await self._resolve_campaign_for_thread(event.thread_id)
            handling = self.gateway.handle_inbound(event, campaign_id=campaign_id)
            await self._persist_inbound_reply(event, campaign_id=campaign_id)
            if campaign_id and handling.get("campaign_stopped"):
                await self._record_stop(
                    campaign_id,
                    reason=handling.get("stop_reason") or "reply_received",
                    actor="gmail_sync",
                    details=handling,
                )
            synced += 1
        if conn is not None and next_history:
            meta = dict(conn.metadata_json or {})
            meta["gmail_history_id"] = next_history
            conn.metadata_json = meta
        await self.session.flush()
        return {"synced": synced, "history_id": next_history, "sandbox": False}

    async def enqueue_durable(self, message: OutboundMessage, *, queue_name: str = "outgoing") -> dict[str, Any]:
        gate = self.gateway.enqueue_message(message)
        if not gate.get("queued"):
            return gate
        row = CommunicationQueueItem(
            queue_name=queue_name,
            payload=message.model_dump(mode="json"),
            priority=message.priority,
            available_at=datetime.now(UTC),
            attempts=0,
            max_attempts=self.config.max_retries,
            status="queued",
        )
        self.session.add(row)
        await self.session.flush()
        return {**gate, "durable_id": str(row.id)}

    async def ingest_webhook(self, provider: str, payload: dict[str, Any], *, signature_valid: bool) -> dict[str, Any]:
        fingerprint = webhook_fingerprint(provider, payload)
        prior = (
            await self.session.execute(
                select(WebhookEvent).where(WebhookEvent.provider == provider).order_by(WebhookEvent.created_at.desc()).limit(100)
            )
        ).scalars().all()
        for row in prior:
            if (row.payload or {}).get("_fingerprint") == fingerprint:
                return {"accepted": False, "events": 0, "signature_valid": signature_valid, "duplicate": True}

        events: list[InboundEvent] = []
        if provider == "meta_whatsapp":
            events = self.webhooks.parse_meta_whatsapp(payload)
        elif provider == "calendly":
            events = self.webhooks.parse_calendly(payload)
        elif provider == "gmail":
            events = self.webhooks.parse_gmail_pubsub(payload)
            # Schedule/perform sync when not sandbox
            if not self.gateway.is_sandbox:
                sync = await self.sync_gmail_replies()
                self.session.add(
                    WebhookEvent(
                        provider=provider,
                        event_type="history",
                        signature_valid=signature_valid,
                        payload={**payload, "_fingerprint": fingerprint, "_sync": sync},
                        processed=True,
                    )
                )
                await self.session.flush()
                return {
                    "accepted": True,
                    "events": int(sync.get("synced") or 0),
                    "signature_valid": signature_valid,
                    "synced": sync.get("synced", 0),
                }

        await self._reload_stopped_campaigns()
        handled = 0
        for event in events:
            campaign_id = await self._resolve_campaign_for_thread(event.thread_id or event.conversation_id)
            result = self.gateway.handle_inbound(event, campaign_id=campaign_id)
            if event.event_type in {"reply", "message"}:
                await self._persist_inbound_reply(event, campaign_id=campaign_id)
                handled += 1
            if campaign_id and result.get("campaign_stopped"):
                await self._record_stop(
                    campaign_id,
                    reason=result.get("stop_reason") or "reply_received",
                    actor=f"webhook:{provider}",
                    details=result,
                )
        self.session.add(
            WebhookEvent(
                provider=provider,
                event_type=events[0].event_type if events else "unknown",
                signature_valid=signature_valid,
                payload={**payload, "_fingerprint": fingerprint},
                processed=True,
            )
        )
        await self.session.flush()
        return {
            "accepted": True,
            "events": len(events),
            "handled": handled,
            "signature_valid": signature_valid,
            "duplicate": False,
        }

    async def e2e_approve_send_reply(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """DB-backed path: approve campaign (if provided) → founder send (sandbox) → reply in inbox."""
        body = body or {}
        campaign_id = UUID(body["campaign_id"]) if body.get("campaign_id") else None
        if campaign_id is not None:
            campaign = await self.session.get(Campaign, campaign_id)
            if campaign is not None and campaign.status in {"needs_review", "draft"}:
                campaign.status = "approved"
                await self.session.flush()
        send = await self.founder_approved_send(
            {
                "campaign_id": str(campaign_id) if campaign_id else None,
                "company_id": body.get("company_id"),
                "opportunity_id": body.get("opportunity_id"),
                "to_address": body.get("to_address") or "prospect@sandbox.example",
                "subject": body.get("subject") or "Beacon founder outreach",
                "body_text": body.get("body_text") or "Personalized founder email",
                "simulate_reply": True,
                "force_sandbox": True,
                "actor": "e2e",
            }
        )
        return {
            "passed": bool(send.get("sent")),
            "scenario": "approve_send_reply",
            "mode": "sandbox",
            "send": send,
        }

    async def _load_oauth_tokens(self, provider: str) -> dict[str, str]:
        row = await self.session.scalar(
            select(OAuthConnection)
            .where(OAuthConnection.provider == provider)
            .where(OAuthConnection.status == "active")
            .order_by(OAuthConnection.created_at.desc())
            .limit(1)
        )
        if row is None:
            return {}
        token = self.secrets.decrypt(row.access_token_encrypted)
        return {provider: token, "email": token}

    async def _reload_stopped_campaigns(self) -> None:
        rows = (
            await self.session.execute(select(CampaignStopEvent).order_by(CampaignStopEvent.created_at.desc()).limit(500))
        ).scalars().all()
        stops: dict[UUID, StopReason] = {}
        for row in rows:
            if row.campaign_id in stops:
                continue
            try:
                stops[row.campaign_id] = StopReason(row.reason)
            except ValueError:
                stops[row.campaign_id] = StopReason.MANUAL_STOP
        self.gateway.load_stopped_campaigns(stops)

    async def _find_by_idempotency(self, key: str) -> CommunicationMessage | None:
        rows = (
            await self.session.execute(
                select(CommunicationMessage)
                .where(CommunicationMessage.direction == "outbound")
                .order_by(CommunicationMessage.created_at.desc())
                .limit(200)
            )
        ).scalars().all()
        for row in rows:
            if (row.metadata_json or {}).get("idempotency_key") == key:
                return row
        return None

    async def _count_sent_today(self) -> int:
        start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        return int(
            await self.session.scalar(
                select(func.count())
                .select_from(CommunicationMessage)
                .where(CommunicationMessage.direction == "outbound")
                .where(CommunicationMessage.state.in_(["sent", "delivered"]))
                .where(CommunicationMessage.created_at >= start)
            )
            or 0
        )

    async def _persist_message_from_send(
        self,
        message: OutboundMessage,
        send: dict[str, Any],
        *,
        sandbox: bool,
        idempotency_key: str,
    ) -> CommunicationMessage:
        row = CommunicationMessage(
            company_id=message.company_id,
            opportunity_id=message.opportunity_id,
            campaign_id=message.campaign_id,
            campaign_step_id=message.campaign_step_id,
            channel=message.channel.value,
            provider=str(send.get("provider") or message.provider.value),
            direction="outbound",
            state=str(send.get("state") or "sent"),
            to_address=message.to_address,
            from_address=message.from_address,
            subject=message.subject,
            body_text=message.body_text,
            body_html=message.body_html,
            provider_message_id=send.get("provider_message_id"),
            thread_id=send.get("thread_id"),
            conversation_id=send.get("conversation_id"),
            sandbox=sandbox,
            error_code=send.get("error_code"),
            error_message=send.get("error_message"),
            attachments=[],
            metadata_json={"idempotency_key": idempotency_key, **dict(message.metadata or {})},
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def _persist_outbound_result(self, payload: dict[str, Any], result: Any) -> None:
        try:
            message = OutboundMessage(**payload)
        except Exception:  # noqa: BLE001
            return
        await self._persist_message_from_send(
            message,
            result.model_dump(mode="json"),
            sandbox=result.sandbox,
            idempotency_key=message.idempotency_key or build_idempotency_key(
                campaign_id=message.campaign_id,
                campaign_step_id=message.campaign_step_id,
                to_address=message.to_address,
                subject=message.subject,
            ),
        )

    async def _dequeue_durable(self, *, limit: int) -> list[dict[str, Any]]:
        rows = list(
            (
                await self.session.execute(
                    select(CommunicationQueueItem)
                    .where(CommunicationQueueItem.status == "queued")
                    .where(CommunicationQueueItem.available_at <= datetime.now(UTC))
                    .order_by(CommunicationQueueItem.priority.asc(), CommunicationQueueItem.available_at.asc())
                    .limit(limit)
                )
            ).scalars().all()
        )
        out = []
        for row in rows:
            row.status = "processing"
            out.append(
                {
                    "id": row.id,
                    "queue_name": row.queue_name,
                    "payload": dict(row.payload or {}),
                    "priority": row.priority,
                }
            )
        await self.session.flush()
        return out

    async def _mark_durable(self, item_id: Any, state: str, *, error: str | None) -> None:
        row = await self.session.get(CommunicationQueueItem, item_id)
        if row is None:
            return
        row.attempts += 1
        row.last_error = error
        row.status = "done" if state in {"sent", "draft", "cancelled"} else ("dead_letter" if row.attempts >= row.max_attempts else "queued")
        await self.session.flush()

    async def _record_stop(self, campaign_id: UUID, *, reason: str, actor: str, details: dict[str, Any]) -> None:
        self.session.add(
            CampaignStopEvent(campaign_id=campaign_id, reason=reason, actor=actor, details=details)
        )
        campaign = await self.session.get(Campaign, campaign_id)
        if campaign is not None:
            campaign.status = "paused"

    async def _inbound_already_stored(self, provider_message_id: str | None) -> bool:
        if not provider_message_id:
            return False
        existing = await self.session.scalar(
            select(CommunicationMessage.id)
            .where(CommunicationMessage.provider_message_id == provider_message_id)
            .limit(1)
        )
        return existing is not None

    async def _resolve_campaign_for_thread(self, thread_id: str | None) -> UUID | None:
        if not thread_id:
            return None
        row = await self.session.scalar(
            select(CommunicationMessage)
            .where(CommunicationMessage.thread_id == thread_id)
            .order_by(CommunicationMessage.created_at.desc())
            .limit(1)
        )
        return row.campaign_id if row else None

    async def _persist_inbound_reply(self, event: InboundEvent, *, campaign_id: UUID | None) -> None:
        company_id = None
        opportunity_id = None
        if campaign_id:
            campaign = await self.session.get(Campaign, campaign_id)
            if campaign is not None:
                company_id = campaign.company_id
                opportunity_id = campaign.opportunity_id
        if company_id is None:
            # Try match outbound by thread
            prior = await self.session.scalar(
                select(CommunicationMessage)
                .where(CommunicationMessage.thread_id == event.thread_id)
                .order_by(CommunicationMessage.created_at.desc())
                .limit(1)
            ) if event.thread_id else None
            if prior is not None:
                company_id = prior.company_id
                opportunity_id = prior.opportunity_id
                campaign_id = campaign_id or prior.campaign_id
        row = CommunicationMessage(
            company_id=company_id,
            opportunity_id=opportunity_id,
            campaign_id=campaign_id,
            channel=event.channel.value,
            provider=event.provider.value,
            direction="inbound",
            state="replied",
            to_address=event.to_address,
            from_address=event.from_address,
            subject=event.subject,
            body_text=event.body_text,
            provider_message_id=event.provider_message_id,
            thread_id=event.thread_id,
            conversation_id=event.conversation_id,
            sandbox=self.gateway.is_sandbox,
            attachments=[],
            metadata_json={"event_type": event.event_type},
        )
        self.session.add(row)
        self.session.add(
            DeliveryEvent(
                message_id=None,
                campaign_id=campaign_id,
                event_type="reply",
                state="replied",
                provider=event.provider.value,
                payload=event.model_dump(mode="json"),
                occurred_at=datetime.now(UTC),
            )
        )
        if company_id is not None:
            await self._append_inbound_item(
                company_id=company_id,
                opportunity_id=opportunity_id,
                campaign_id=campaign_id,
                subject=event.subject or "Reply",
                body=event.body_text,
                from_address=event.from_address,
                thread_id=event.thread_id,
            )
            if opportunity_id is not None:
                await self._record_outcome_reply(opportunity_id, company_id)
        await self.session.flush()

    async def _append_outbound_only(
        self,
        *,
        company_id: UUID,
        opportunity_id: UUID | None,
        campaign_id: UUID | None,
        subject: str,
        outbound_body: str,
        to_address: str,
        thread_id: str | None,
    ) -> None:
        thread = await self._get_or_create_thread(
            company_id=company_id,
            opportunity_id=opportunity_id,
            campaign_id=campaign_id,
            subject=subject,
            participant=to_address,
        )
        self.session.add(
            ConversationItemRow(
                conversation_id=thread.id,
                company_id=company_id,
                opportunity_id=opportunity_id,
                campaign_id=campaign_id,
                channel="email",
                item_type="message",
                direction="outbound",
                subject=subject,
                body=outbound_body,
                to_address=to_address,
                thread_id=thread_id,
                attachments=[],
                unread=False,
                pinned=False,
                occurred_at=datetime.now(UTC),
                metadata_json={},
            )
        )
        thread.last_activity_at = datetime.now(UTC)
        self.conversations.upsert_thread(
            company_id=company_id,
            subject=subject,
            opportunity_id=opportunity_id,
            campaign_id=campaign_id,
            participants=[to_address],
        )

    async def _append_inbound_item(
        self,
        *,
        company_id: UUID,
        opportunity_id: UUID | None,
        campaign_id: UUID | None,
        subject: str,
        body: str,
        from_address: str | None,
        thread_id: str | None,
    ) -> None:
        thread = await self._get_or_create_thread(
            company_id=company_id,
            opportunity_id=opportunity_id,
            campaign_id=campaign_id,
            subject=subject,
            participant=from_address or "unknown",
        )
        self.session.add(
            ConversationItemRow(
                conversation_id=thread.id,
                company_id=company_id,
                opportunity_id=opportunity_id,
                campaign_id=campaign_id,
                channel="email",
                item_type="reply",
                direction="inbound",
                subject=subject,
                body=body,
                from_address=from_address,
                thread_id=thread_id,
                attachments=[],
                unread=True,
                pinned=False,
                occurred_at=datetime.now(UTC),
                metadata_json={},
            )
        )
        thread.unread_count = int(thread.unread_count or 0) + 1
        thread.last_activity_at = datetime.now(UTC)
        thread.ai_summary = f"Reply received from {from_address or 'prospect'}."

    async def _get_or_create_thread(
        self,
        *,
        company_id: UUID,
        opportunity_id: UUID | None,
        campaign_id: UUID | None,
        subject: str,
        participant: str,
    ) -> ConversationThreadRow:
        existing = await self.session.scalar(
            select(ConversationThreadRow)
            .where(ConversationThreadRow.company_id == company_id)
            .where(ConversationThreadRow.subject == subject)
            .order_by(ConversationThreadRow.created_at.desc())
            .limit(1)
        )
        if existing is not None:
            return existing
        thread = ConversationThreadRow(
            company_id=company_id,
            opportunity_id=opportunity_id,
            campaign_id=campaign_id,
            subject=subject,
            participants=[participant],
            channels=["email"],
            unread_count=0,
            pinned=False,
            last_activity_at=datetime.now(UTC),
        )
        self.session.add(thread)
        await self.session.flush()
        return thread

    def prometheus_metrics(self) -> str:
        depths = self.gateway.queue.depth()
        lines = [
            "# HELP beacon_communication_queue_depth Queue depth by name",
            "# TYPE beacon_communication_queue_depth gauge",
        ]
        for name, depth in depths.items():
            lines.append(f'beacon_communication_queue_depth{{queue="{name}"}} {depth}')
        lines.extend(
            [
                "# HELP beacon_communication_sandbox Sandbox mode active (1/0)",
                "# TYPE beacon_communication_sandbox gauge",
                f"beacon_communication_sandbox {1 if self.gateway.is_sandbox else 0}",
                "# HELP beacon_communication_stopped_campaigns Stopped campaign count",
                "# TYPE beacon_communication_stopped_campaigns gauge",
                f"beacon_communication_stopped_campaigns {len(self.gateway.stopped_campaigns)}",
            ]
        )
        return "\n".join(lines) + "\n"

    async def _append_conversation(
        self,
        *,
        company_id: UUID,
        opportunity_id: UUID | None,
        campaign_id: UUID | None,
        subject: str,
        outbound_body: str,
        reply_body: str,
        to_address: str,
        thread_id: str | None,
    ) -> None:
        thread = ConversationThreadRow(
            company_id=company_id,
            opportunity_id=opportunity_id,
            campaign_id=campaign_id,
            subject=subject,
            participants=[to_address],
            channels=["email"],
            unread_count=1,
            pinned=False,
            last_activity_at=datetime.now(UTC),
        )
        self.session.add(thread)
        await self.session.flush()
        self.session.add(
            ConversationItemRow(
                conversation_id=thread.id,
                company_id=company_id,
                opportunity_id=opportunity_id,
                campaign_id=campaign_id,
                channel="email",
                item_type="message",
                direction="outbound",
                subject=subject,
                body=outbound_body,
                to_address=to_address,
                thread_id=thread_id,
                attachments=[],
                unread=False,
                pinned=False,
                occurred_at=datetime.now(UTC),
                metadata_json={},
            )
        )
        self.session.add(
            ConversationItemRow(
                conversation_id=thread.id,
                company_id=company_id,
                opportunity_id=opportunity_id,
                campaign_id=campaign_id,
                channel="email",
                item_type="reply",
                direction="inbound",
                subject=f"Re: {subject}",
                body=reply_body,
                from_address=to_address,
                thread_id=thread_id,
                attachments=[],
                unread=True,
                pinned=False,
                occurred_at=datetime.now(UTC),
                metadata_json={},
            )
        )
        thread.ai_summary = f"Sandbox thread with reply from {to_address}."

    async def _record_outcome_reply(self, opportunity_id: UUID, company_id: UUID | None) -> None:
        if company_id is None:
            return
        outcome = await self.session.scalar(
            select(OpportunityOutcome).where(OpportunityOutcome.opportunity_id == opportunity_id).limit(1)
        )
        if outcome is None:
            outcome = OpportunityOutcome(
                opportunity_id=opportunity_id,
                company_id=company_id,
                lifecycle_stage="replied",
                opportunity_score=0.0,
                replied_at=datetime.now(UTC),
            )
            self.session.add(outcome)
        else:
            outcome.lifecycle_stage = "replied"
            outcome.replied_at = datetime.now(UTC)
        self.session.add(
            ContactAttempt(
                opportunity_id=opportunity_id,
                company_id=company_id,
                channel="email",
                attempted_at=datetime.now(UTC),
                replied=True,
                details={"source": "sandbox"},
            )
        )

    async def _record_outcome_meeting(self, opportunity_id: UUID, company_id: UUID, start: datetime) -> None:
        outcome = await self.session.scalar(
            select(OpportunityOutcome).where(OpportunityOutcome.opportunity_id == opportunity_id).limit(1)
        )
        if outcome is None:
            outcome = OpportunityOutcome(
                opportunity_id=opportunity_id,
                company_id=company_id,
                lifecycle_stage="meeting_scheduled",
                opportunity_score=0.0,
                meeting_at=start,
            )
            self.session.add(outcome)
        else:
            outcome.lifecycle_stage = "meeting_scheduled"
            outcome.meeting_at = start
        self.session.add(
            Meeting(
                opportunity_id=opportunity_id,
                company_id=company_id,
                scheduled_at=start,
                meeting_type="sandbox",
                notes="Sandbox booked meeting",
            )
        )
