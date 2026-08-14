from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.repositories.client_execution import ClientExecutionRepository
from client_execution import ClientExecutionService


class ClientExecutionPlatformService:
    def __init__(self, repository: ClientExecutionRepository) -> None:
        self.repository = repository
        self.engine = ClientExecutionService()

    async def client_pack(self, company_id: UUID, *, refresh: bool = False) -> dict[str, Any] | None:
        if not refresh:
            latest = await self.repository.latest_for_company(company_id)
            if latest and latest.payload:
                return self._from_row(latest)
        return await self.refresh(company_id)

    async def refresh(self, company_id: UUID) -> dict[str, Any] | None:
        data = await self.repository.build_input(company_id)
        if data is None:
            return None
        decision = self.engine.evaluate(data)
        row = await self.repository.store_decision(decision)
        return self._from_row(row)

    async def refresh_batch(self, *, limit: int = 30) -> dict[str, Any]:
        ids = await self.repository.company_ids(limit=limit)
        refreshed = 0
        for company_id in ids:
            if await self.refresh(company_id):
                refreshed += 1
        return {"refreshed": refreshed, "requested": len(ids)}

    async def dashboard(self) -> dict[str, Any]:
        counts = await self.repository.dashboard_counts()
        delivery = await self.repository.latest_delivery()
        recent = await self.repository.recent_profiles(limit=20)
        return {
            **counts,
            "delivery": delivery.payload if delivery else {},
            "founder_view": delivery.founder_view if delivery else {},
            "clients": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "company_name": r.company_name,
                    "stage": r.stage,
                    "health_status": r.health_status,
                    "overall_health": r.overall_health,
                    "contract_value": r.contract_value,
                }
                for r in recent
            ],
        }

    async def health(self, *, limit: int = 50) -> dict[str, Any]:
        rows = await self.repository.recent_health(limit=limit)
        return {
            "snapshots": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "status": r.status,
                    "overall_health": r.overall_health,
                    "renewal_probability": r.renewal_probability,
                    "upsell_probability": r.upsell_probability,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "total": len(rows),
        }

    async def handoffs(self, *, limit: int = 50) -> dict[str, Any]:
        rows = await self.repository.recent_handoffs(limit=limit)
        return {
            "handoffs": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "payload": r.payload,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "total": len(rows),
        }

    async def upsells(self, *, limit: int = 50) -> dict[str, Any]:
        rows = await self.repository.recent_upsells(limit=limit)
        return {
            "recommendations": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "recommendation_id": r.recommendation_id,
                    "service": r.service,
                    "title": r.title,
                    "reason": r.reason,
                    "confidence": r.confidence,
                    "requires_founder_approval": r.requires_founder_approval,
                    "modifies_production": r.modifies_production,
                    "status": r.status,
                }
                for r in rows
            ],
            "total": len(rows),
            "note": "Founder approval required. Upsells never auto-apply.",
        }

    async def approve_upsell(self, recommendation_id: str, *, actor: str = "founder", approve: bool = True) -> dict[str, Any]:
        row = await self.repository.get_upsell(recommendation_id)
        if row is None:
            return {"error": "not_found"}
        row.status = "approved" if approve else "rejected"
        row.approved_by = actor
        row.approved_at = datetime.now(UTC)
        row.modifies_production = False
        await self.repository.session.flush()
        return {
            "recommendation_id": row.recommendation_id,
            "status": row.status,
            "modifies_production": False,
            "approved_by": actor,
        }

    async def projects(self, *, limit: int = 50) -> dict[str, Any]:
        rows = await self.repository.recent_projects(limit=limit)
        return {
            "projects": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "name": r.name,
                    "stage": r.stage,
                    "blocked": r.blocked,
                    "at_risk": r.at_risk,
                    "payload": r.payload,
                }
                for r in rows
            ],
            "total": len(rows),
        }

    def _from_row(self, row: Any) -> dict[str, Any]:
        payload = dict(row.payload or {})
        payload["profile_id"] = str(row.id)
        payload["company_id"] = str(row.company_id)
        payload["company_name"] = row.company_name
        payload["stage"] = row.stage
        payload["health_status"] = row.health_status
        payload["overall_health"] = row.overall_health
        payload["contract_value"] = row.contract_value
        payload["scoring_version"] = row.scoring_version
        payload["created_at"] = row.created_at.isoformat() if row.created_at else None
        return payload
