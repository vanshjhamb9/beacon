from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.communication import DeliveryEvent, OAuthConnection, WebhookEvent
from app.models.communication import CommunicationMessage
from app.models.execution_readiness import CommunicationProviderStatus, ExecutionStatusRow
from execution_readiness.enums import ExecutionMode, ProviderKind
from execution_readiness.models import DEFAULT_ORG_ID, ProviderSnapshot
from execution_readiness.service import ExecutionReadinessEngine


class ExecutionReadinessService:
    def __init__(self, session: AsyncSession, *, organization_id: str = DEFAULT_ORG_ID) -> None:
        self.session = session
        self.organization_id = organization_id
        self.engine = ExecutionReadinessEngine()

    async def refresh_and_evaluate(self) -> Any:
        providers = await self._probe_providers()
        deliveries = await self._count_verified_deliveries()
        messages_sent = await self._count_messages_sent()
        snap = self.engine.evaluate(
            providers=providers,
            verified_deliveries=deliveries,
            messages_sent=messages_sent,
            organization_id=self.organization_id,
        )
        await self._persist(snap, providers)
        return snap

    async def get_status(self) -> dict[str, Any]:
        snap = await self.refresh_and_evaluate()
        return self.engine.status_response(snap).model_dump(mode="json")

    async def get_readiness(self) -> dict[str, Any]:
        snap = await self.refresh_and_evaluate()
        return self.engine.readiness_response(snap).model_dump(mode="json")

    async def validate(self) -> dict[str, Any]:
        snap = await self.refresh_and_evaluate()
        return self.engine.validate_response(snap).model_dump(mode="json")

    async def dashboard_card(self) -> dict[str, Any]:
        snap = await self.refresh_and_evaluate()
        tone = {
            ExecutionMode.PLANNING: "RED",
            ExecutionMode.READY: "YELLOW",
            ExecutionMode.EXECUTING: "GREEN",
        }[snap.execution_mode]
        return {
            "title": "Communication Readiness",
            "execution_mode": snap.execution_mode.value,
            "tone": tone,
            "email": "Connected" if snap.email_ready else "Not Connected",
            "whatsapp": "Connected" if snap.whatsapp_ready else "Not Connected",
            "tracking": "Enabled" if snap.tracking_ready else "Disabled",
            "follow_ups": "Enabled" if snap.followup_ready else "Disabled",
            "recommendation": snap.recommendation,
            "reason": snap.reason,
            "scoring_version": snap.scoring_version,
        }

    async def snapshot(self) -> Any:
        return await self.refresh_and_evaluate()

    async def delivered_company_ids(self) -> set[str]:
        rows = (
            await self.session.execute(
                select(CommunicationMessage.company_id)
                .join(DeliveryEvent, DeliveryEvent.message_id == CommunicationMessage.id)
                .where(
                    DeliveryEvent.state.in_(["delivered", "DELIVERED"]),
                    CommunicationMessage.company_id.is_not(None),
                    CommunicationMessage.deleted_at.is_(None),
                )
            )
        ).all()
        return {str(r[0]) for r in rows if r[0]}

    async def _probe_providers(self) -> list[ProviderSnapshot]:
        settings = get_settings()
        out: list[ProviderSnapshot] = []

        for provider, kind in (
            ("gmail", ProviderKind.GMAIL),
            ("microsoft_graph", ProviderKind.GRAPH),
            ("outlook_calendar", ProviderKind.OUTLOOK),
        ):
            row = await self.session.scalar(
                select(OAuthConnection)
                .where(OAuthConnection.provider == provider, OAuthConnection.status == "active")
                .order_by(OAuthConnection.created_at.desc())
                .limit(1)
            )
            webhook_ok = await self._webhook_verified(provider)
            connected = row is not None
            oauth_valid = bool(row and row.status == "active" and row.access_token_encrypted)
            can_send = connected and oauth_valid
            out.append(
                ProviderSnapshot(
                    provider=kind if kind != ProviderKind.OUTLOOK else (
                        ProviderKind.GRAPH if provider == "microsoft_graph" else ProviderKind.OUTLOOK
                    ),
                    connected=connected,
                    oauth_valid=oauth_valid,
                    webhook_verified=webhook_ok,
                    can_send=can_send,
                    can_receive=can_send,
                    last_sync=row.updated_at.isoformat() if row and row.updated_at else None,
                    detail=row.account_email if row else f"{provider} not connected",
                )
            )

        # Meta WhatsApp — config tokens (not OAuth row)
        token = getattr(settings, "meta_whatsapp_token", None) or getattr(settings, "whatsapp_token", None)
        phone_id = getattr(settings, "meta_whatsapp_phone_number_id", None) or getattr(
            settings, "whatsapp_phone_number_id", None
        )
        wa_connected = bool(token and phone_id)
        out.append(
            ProviderSnapshot(
                provider=ProviderKind.META_WHATSAPP,
                connected=wa_connected,
                oauth_valid=wa_connected,
                webhook_verified=await self._webhook_verified("meta_whatsapp") or await self._webhook_verified("meta"),
                can_send=wa_connected,
                can_receive=wa_connected,
                detail="Meta WhatsApp configured" if wa_connected else "Meta WhatsApp not configured",
            )
        )

        # SendGrid / SMTP placeholders — only if secrets exist (never invent)
        out.append(
            ProviderSnapshot(
                provider=ProviderKind.SENDGRID,
                connected=False,
                detail="SendGrid not configured",
            )
        )
        out.append(
            ProviderSnapshot(
                provider=ProviderKind.SMTP,
                connected=False,
                detail="SMTP not configured",
            )
        )
        return out

    async def _webhook_verified(self, provider: str) -> bool:
        row = await self.session.scalar(
            select(WebhookEvent)
            .where(
                WebhookEvent.provider == provider,
                WebhookEvent.signature_valid.is_(True),
                WebhookEvent.deleted_at.is_(None),
            )
            .limit(1)
        )
        return row is not None

    async def _count_verified_deliveries(self) -> int:
        n = await self.session.scalar(
            select(func.count())
            .select_from(DeliveryEvent)
            .where(
                DeliveryEvent.state.in_(["delivered", "DELIVERED"]),
                DeliveryEvent.deleted_at.is_(None),
            )
        )
        return int(n or 0)

    async def _count_messages_sent(self) -> int:
        n = await self.session.scalar(
            select(func.count())
            .select_from(CommunicationMessage)
            .where(
                CommunicationMessage.direction == "outbound",
                CommunicationMessage.state.in_(["sent", "delivered", "SENT", "DELIVERED"]),
                CommunicationMessage.deleted_at.is_(None),
            )
        )
        return int(n or 0)

    async def _persist(self, snap: Any, providers: list[ProviderSnapshot]) -> None:
        now = datetime.now(UTC)
        # Upsert provider rows
        for p in providers:
            existing = await self.session.scalar(
                select(CommunicationProviderStatus).where(
                    CommunicationProviderStatus.organization_id == self.organization_id,
                    CommunicationProviderStatus.provider == p.provider.value,
                    CommunicationProviderStatus.deleted_at.is_(None),
                )
            )
            if existing:
                existing.connected = p.connected
                existing.oauth_valid = p.oauth_valid
                existing.webhook_verified = p.webhook_verified
                existing.can_send = p.can_send
                existing.can_receive = p.can_receive
                existing.last_sync = now if p.connected else existing.last_sync
                existing.payload = {"detail": p.detail}
            else:
                self.session.add(
                    CommunicationProviderStatus(
                        id=uuid.uuid4(),
                        organization_id=self.organization_id,
                        provider=p.provider.value,
                        connected=p.connected,
                        oauth_valid=p.oauth_valid,
                        webhook_verified=p.webhook_verified,
                        can_send=p.can_send,
                        can_receive=p.can_receive,
                        last_sync=now if p.connected else None,
                        payload={"detail": p.detail},
                    )
                )

        status_row = await self.session.scalar(
            select(ExecutionStatusRow).where(
                ExecutionStatusRow.organization_id == self.organization_id,
                ExecutionStatusRow.deleted_at.is_(None),
            )
        )
        if status_row:
            status_row.execution_mode = snap.execution_mode.value
            status_row.reason = snap.reason
            status_row.communication_ready = snap.communication_ready
            status_row.email_ready = snap.email_ready
            status_row.whatsapp_ready = snap.whatsapp_ready
            status_row.tracking_ready = snap.tracking_ready
            status_row.followup_ready = snap.followup_ready
            status_row.payload = self.engine.report_section(snap)
        else:
            self.session.add(
                ExecutionStatusRow(
                    id=uuid.uuid4(),
                    organization_id=self.organization_id,
                    execution_mode=snap.execution_mode.value,
                    reason=snap.reason,
                    communication_ready=snap.communication_ready,
                    email_ready=snap.email_ready,
                    whatsapp_ready=snap.whatsapp_ready,
                    tracking_ready=snap.tracking_ready,
                    followup_ready=snap.followup_ready,
                    payload=self.engine.report_section(snap),
                )
            )
        await self.session.flush()
