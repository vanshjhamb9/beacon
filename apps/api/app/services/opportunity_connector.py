"""App service for Opportunity Connector Platform (OCP v1)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity_connector import (
    ConnectorCapabilityRow,
    ConnectorConfigurationRow,
    ConnectorEventRow,
    ConnectorFailureRow,
    ConnectorHealthRow,
    ConnectorRateLimitRow,
    ConnectorRegistryRow,
    ConnectorRunRow,
    ConnectorStatisticsRow,
    ConnectorYieldRow,
)


class OpportunityConnectorService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_connectors(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(ConnectorRegistryRow).where(ConnectorRegistryRow.deleted_at.is_(None))
            )
        ).scalars().all()
        return {
            "connectors": [
                {
                    "connector_id": r.connector_id,
                    "name": r.name,
                    "version": r.version,
                    "category": r.category,
                    "enabled": r.enabled,
                    "configured": r.configured,
                    "healthy": r.healthy,
                    "events_today": r.events_today,
                    "events_accepted": r.events_accepted,
                    "events_rejected": r.events_rejected,
                    "average_latency": r.average_latency,
                    "failure_rate": r.failure_rate,
                    "rate_limit_remaining": r.rate_limit_remaining,
                    "last_sync": r.last_sync.isoformat() if r.last_sync else None,
                }
                for r in rows
            ],
            "total": len(rows),
        }

    async def get_connector(self, connector_id: str) -> dict[str, Any]:
        row = await self.session.scalar(
            select(ConnectorRegistryRow).where(
                ConnectorRegistryRow.connector_id == connector_id,
                ConnectorRegistryRow.deleted_at.is_(None),
            )
        )
        if not row:
            return {"error": f"connector_not_found: {connector_id}"}
        events = await self._connector_events(connector_id, limit=100)
        health = await self._connector_health(connector_id)
        return {
            "connector_id": row.connector_id,
            "name": row.name,
            "version": row.version,
            "category": row.category,
            "enabled": row.enabled,
            "configured": row.configured,
            "healthy": row.healthy,
            "events_today": row.events_today,
            "events_accepted": row.events_accepted,
            "events_rejected": row.events_rejected,
            "average_latency": row.average_latency,
            "failure_rate": row.failure_rate,
            "rate_limit_remaining": row.rate_limit_remaining,
            "last_sync": row.last_sync.isoformat() if row.last_sync else None,
            "health": health,
            "recent_events": events,
        }

    async def connectors_health(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(ConnectorHealthRow).where(ConnectorHealthRow.deleted_at.is_(None))
            )
        ).scalars().all()
        return {
            "health": [
                {
                    "connector_id": r.connector_id,
                    "status": r.status,
                    "latency_ms": r.latency_ms,
                    "failures": r.failures,
                    "retries": r.retries,
                    "authenticated": r.authenticated,
                    "rate_limit_remaining": r.rate_limit_remaining,
                    "queue_size": r.queue_size,
                    "freshness_minutes": r.freshness_minutes,
                    "consecutive_failures": r.consecutive_failures,
                    "last_success": r.last_success.isoformat() if r.last_success else None,
                    "last_failure": r.last_failure.isoformat() if r.last_failure else None,
                }
                for r in rows
            ],
            "total": len(rows),
        }

    async def connector_statistics(self, period: str = "today") -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(ConnectorStatisticsRow).where(
                    ConnectorStatisticsRow.period == period,
                    ConnectorStatisticsRow.deleted_at.is_(None),
                )
            )
        ).scalars().all()
        return {
            "period": period,
            "statistics": [
                {
                    "connector_id": r.connector_id,
                    "signals": r.signals,
                    "accepted": r.accepted,
                    "rejected": r.rejected,
                    "identity_matched": r.identity_matched,
                    "verified_companies": r.verified_companies,
                    "sales_ready": r.sales_ready,
                    "revenue_ready": r.revenue_ready,
                    "contacted": r.contacted,
                    "replies": r.replies,
                    "meetings": r.meetings,
                    "won": r.won,
                    "revenue": r.revenue,
                    "acceptance_rate": r.acceptance_rate,
                    "signal_yield": r.signal_yield,
                    "revenue_yield": r.revenue_yield,
                    "meeting_yield": r.meeting_yield,
                    "revenue_per_signal": r.revenue_per_signal,
                }
                for r in rows
            ],
        }

    async def connector_yield(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(ConnectorYieldRow).where(ConnectorYieldRow.deleted_at.is_(None))
            )
        ).scalars().all()
        return {
            "yield": [
                {
                    "connector_id": r.connector_id,
                    "signals": r.signals,
                    "accepted": r.accepted,
                    "identity_matched": r.identity_matched,
                    "verified_companies": r.verified_companies,
                    "sales_ready": r.sales_ready,
                    "revenue_ready": r.revenue_ready,
                    "contacted": r.contacted,
                    "replies": r.replies,
                    "meetings": r.meetings,
                    "won": r.won,
                    "revenue": r.revenue,
                    "signal_yield": r.signal_yield,
                    "revenue_yield": r.revenue_yield,
                    "meeting_yield": r.meeting_yield,
                    "acceptance_rate": r.acceptance_rate,
                    "conversion_rate": r.conversion_rate,
                    "revenue_per_signal": r.revenue_per_signal,
                }
                for r in rows
            ],
        }

    async def connector_failures(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(ConnectorFailureRow).where(ConnectorFailureRow.deleted_at.is_(None))
                .order_by(ConnectorFailureRow.created_at.desc())
                .limit(100)
            )
        ).scalars().all()
        return {
            "failures": [
                {
                    "connector_id": r.connector_id,
                    "error_type": r.error_type,
                    "error_message": r.error_message,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
        }

    async def connector_feed(self, *, limit: int = 40) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(ConnectorEventRow).where(ConnectorEventRow.deleted_at.is_(None))
                .order_by(ConnectorEventRow.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return {
            "feed": [
                {
                    "event_id": r.event_id,
                    "connector_id": r.connector_id,
                    "company_name": r.company_name,
                    "headline": r.headline,
                    "event_type": r.event_type,
                    "accepted": r.accepted,
                    "rejection_reason": r.rejection_reason,
                    "published_at": r.published_at.isoformat() if r.published_at else None,
                }
                for r in rows
            ],
        }

    async def connector_events(
        self,
        *,
        connector_id: str | None = None,
        event_type: str | None = None,
        accepted: bool | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        filters: list[Any] = [ConnectorEventRow.deleted_at.is_(None)]
        if connector_id:
            filters.append(ConnectorEventRow.connector_id == connector_id)
        if event_type:
            filters.append(ConnectorEventRow.event_type == event_type)
        if accepted is not None:
            filters.append(ConnectorEventRow.accepted == accepted)
        rows = (
            await self.session.execute(
                select(ConnectorEventRow)
                .where(and_(*filters))
                .order_by(ConnectorEventRow.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return {
            "events": [
                {
                    "event_id": r.event_id,
                    "connector_id": r.connector_id,
                    "company_name": r.company_name,
                    "headline": r.headline,
                    "event_type": r.event_type,
                    "event_category": r.event_category,
                    "accepted": r.accepted,
                    "rejection_reason": r.rejection_reason,
                    "confidence": r.confidence,
                    "published_at": r.published_at.isoformat() if r.published_at else None,
                }
                for r in rows
            ],
            "total": len(rows),
        }

    async def _connector_events(self, connector_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(ConnectorEventRow).where(
                    ConnectorEventRow.connector_id == connector_id,
                    ConnectorEventRow.deleted_at.is_(None),
                )
                .order_by(ConnectorEventRow.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return [
            {
                "event_id": r.event_id,
                "headline": r.headline,
                "event_type": r.event_type,
                "accepted": r.accepted,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    async def _connector_health(self, connector_id: str) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(ConnectorHealthRow).where(
                ConnectorHealthRow.connector_id == connector_id,
                ConnectorHealthRow.deleted_at.is_(None),
            )
        )
        if not row:
            return None
        return {
            "status": row.status,
            "latency_ms": row.latency_ms,
            "failures": row.failures,
            "retries": row.retries,
            "authenticated": row.authenticated,
            "rate_limit_remaining": row.rate_limit_remaining,
            "consecutive_failures": row.consecutive_failures,
        }
