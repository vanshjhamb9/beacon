from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.repositories.revenue_operations import RevenueOperationsRepository
from revenue_operations import RevenueOperationsService
from revenue_operations.models.types import AlertLifecycle


class RevenueOperationsPlatformService:
    def __init__(self, repository: RevenueOperationsRepository) -> None:
        self.repository = repository
        self.engine = RevenueOperationsService()

    async def dashboard(self, *, refresh: bool = False) -> dict[str, Any]:
        if not refresh:
            latest = await self.repository.latest_snapshot()
            if latest and latest.payload:
                return self._from_snapshot(latest)
        return await self.refresh()

    async def refresh(self) -> dict[str, Any]:
        data = await self.repository.build_input()
        decision = self.engine.evaluate(data)
        snap = await self.repository.store_decision(decision)
        return self._from_snapshot(snap)

    async def forecast(self, *, refresh: bool = False) -> dict[str, Any]:
        if refresh:
            await self.refresh()
        row = await self.repository.latest_forecast()
        if row is None:
            pack = await self.refresh()
            return pack.get("forecast") or {}
        return {
            "this_week": row.this_week,
            "this_month": row.this_month,
            "quarter": row.quarter,
            "annual": row.annual,
            "confidence_score": row.confidence_score,
            "pipeline_health": row.pipeline_health,
            "payload": row.payload,
            "scoring_version": row.scoring_version,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    async def alerts(self, *, lifecycle: str | None = None, limit: int = 50) -> dict[str, Any]:
        rows = await self.repository.list_alerts(lifecycle=lifecycle, limit=limit)
        return {
            "alerts": [self._alert_dict(r) for r in rows],
            "total": len(rows),
            "scoring_version": "roc-v1",
        }

    async def transition_alert(self, alert_row_id: UUID, target: str) -> dict[str, Any]:
        row = await self.repository.get_alert(alert_row_id)
        if row is None:
            return {"error": "not_found"}
        current = AlertLifecycle(row.lifecycle)
        next_state = self.engine.transition_alert(current, AlertLifecycle(target))
        row.lifecycle = next_state.value
        if next_state == AlertLifecycle.RESOLVED:
            row.resolved_at = datetime.now(UTC)
        await self.repository.session.flush()
        return self._alert_dict(row)

    async def memory(self, *, query: str = "", limit: int = 50) -> dict[str, Any]:
        rows = await self.repository.search_memory(query, limit=limit)
        return {
            "records": [
                {
                    "id": str(r.id),
                    "record_type": r.record_type,
                    "company_id": str(r.company_id) if r.company_id else None,
                    "company_name": r.company_name,
                    "title": r.title,
                    "body": r.body,
                    "tags": r.tags,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "total": len(rows),
            "query": query,
        }

    async def replay(self, replay_id: UUID) -> dict[str, Any] | None:
        row = await self.repository.get_replay(replay_id)
        if row is None:
            return None
        return {
            "id": str(row.id),
            "opportunity_id": str(row.opportunity_id) if row.opportunity_id else None,
            "company_id": str(row.company_id) if row.company_id else None,
            "company_name": row.company_name,
            "outcome": row.outcome,
            "events": row.events,
            "evidence": row.evidence,
            "scoring_version": row.scoring_version,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    async def learning(self, *, status: str | None = None, limit: int = 50) -> dict[str, Any]:
        rows = await self.repository.list_learning(status=status, limit=limit)
        return {
            "recommendations": [
                {
                    "id": str(r.id),
                    "recommendation_id": r.recommendation_id,
                    "category": r.category,
                    "title": r.title,
                    "detail": r.detail,
                    "status": r.status,
                    "modifies_production": r.modifies_production,
                    "evidence": r.evidence,
                    "approved_at": r.approved_at.isoformat() if r.approved_at else None,
                    "approved_by": r.approved_by,
                }
                for r in rows
            ],
            "total": len(rows),
            "note": "Recommendations never modify production without founder approval.",
        }

    async def approve_learning(self, recommendation_id: str, *, actor: str = "founder", approve: bool = True) -> dict[str, Any]:
        row = await self.repository.get_learning(recommendation_id)
        if row is None:
            return {"error": "not_found"}
        row.status = "approved" if approve else "rejected"
        row.approved_by = actor
        row.approved_at = datetime.now(UTC)
        # Never mutate production engines — approval is recorded only.
        await self.repository.session.flush()
        return {
            "recommendation_id": row.recommendation_id,
            "status": row.status,
            "modifies_production": False,
            "approved_by": actor,
        }

    async def metrics(self, *, refresh: bool = False) -> dict[str, Any]:
        if refresh:
            await self.refresh()
        row = await self.repository.latest_metrics()
        if row is None:
            pack = await self.refresh()
            return pack.get("operational_metrics") or {}
        return {
            **(row.payload or {}),
            "close_rate": row.close_rate,
            "reply_rate": row.reply_rate,
            "meeting_rate": row.meeting_rate,
            "revenue": row.revenue,
            "scoring_version": row.scoring_version,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    def _from_snapshot(self, snap: Any) -> dict[str, Any]:
        payload = dict(snap.payload or {})
        payload["snapshot_id"] = str(snap.id)
        payload["revenue_score"] = snap.revenue_score
        payload["pipeline_value"] = snap.pipeline_value
        payload["expected_revenue"] = snap.expected_revenue
        payload["scoring_version"] = snap.scoring_version
        payload["created_at"] = snap.created_at.isoformat() if snap.created_at else None
        return payload

    def _alert_dict(self, r: Any) -> dict[str, Any]:
        return {
            "id": str(r.id),
            "alert_id": r.alert_id,
            "kind": r.kind,
            "title": r.title,
            "severity": r.severity,
            "company_id": str(r.company_id) if r.company_id else None,
            "company_name": r.company_name,
            "recommendation": r.recommendation,
            "lifecycle": r.lifecycle,
            "dedupe_key": r.dedupe_key,
            "evidence": r.evidence,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
        }
