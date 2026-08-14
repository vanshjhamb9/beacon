from __future__ import annotations

from typing import Any
from uuid import UUID

from app.repositories.account_journey import AccountJourneyRepository
from account_journey import AccountJourneyService


class AccountJourneyPlatformService:
    def __init__(self, repository: AccountJourneyRepository) -> None:
        self.repository = repository
        self.engine = AccountJourneyService()

    async def company_pack(self, company_id: UUID, *, refresh: bool = False) -> dict[str, Any] | None:
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
        await self.repository.store_analytics(decision)
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
        recent = await self.repository.recent_journeys(limit=20)
        return {
            **counts,
            "accounts": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "company_name": r.company_name,
                    "stage": r.stage,
                    "health_category": r.health_category,
                    "overall_engagement": r.overall_engagement,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in recent
            ],
        }

    async def followups(self, *, limit: int = 50) -> dict[str, Any]:
        rows = await self.repository.recent_followups(limit=limit)
        return {
            "plans": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "next_action": r.next_action,
                    "channel": r.channel,
                    "message_type": r.message_type,
                    "urgency": r.urgency,
                    "best_timing_hours": r.best_timing_hours,
                    "reason": r.reason,
                    "requires_founder_approval": r.requires_founder_approval,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "total": len(rows),
            "note": "Founder approval required before external sends.",
        }

    async def analytics(self) -> dict[str, Any]:
        row = await self.repository.latest_analytics()
        if row is None:
            await self.refresh_batch(limit=15)
            row = await self.repository.latest_analytics()
        if row is None:
            return {"payload": {}, "total": 0}
        return {
            "payload": row.payload,
            "scoring_version": row.scoring_version,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    async def replies(self, *, limit: int = 50) -> dict[str, Any]:
        rows = await self.repository.recent_replies(limit=limit)
        return {
            "replies": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "classification": r.classification,
                    "confidence": r.confidence,
                    "structured_outcome": r.structured_outcome,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "total": len(rows),
        }

    async def health(self, *, limit: int = 50) -> dict[str, Any]:
        rows = await self.repository.recent_health(limit=limit)
        return {
            "snapshots": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "category": r.category,
                    "score": r.score,
                    "reason": r.reason,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "total": len(rows),
        }

    def _from_row(self, row: Any) -> dict[str, Any]:
        payload = dict(row.payload or {})
        payload["journey_id"] = str(row.id)
        payload["company_id"] = str(row.company_id)
        payload["company_name"] = row.company_name
        payload["stage"] = row.stage
        payload["health_category"] = row.health_category
        payload["overall_engagement"] = row.overall_engagement
        payload["scoring_version"] = row.scoring_version
        payload["created_at"] = row.created_at.isoformat() if row.created_at else None
        return payload
