from __future__ import annotations

from typing import Any
from uuid import UUID

from app.repositories.live_revenue import LiveRevenueRepository
from live_revenue_execution import LiveRevenueExecutionService


class LiveRevenuePlatformService:
    def __init__(self, repository: LiveRevenueRepository) -> None:
        self.repository = repository
        self.engine = LiveRevenueExecutionService()

    async def company_pack(self, company_id: UUID, *, refresh: bool = False) -> dict[str, Any] | None:
        if not refresh:
            latest = await self.repository.latest_for_company(company_id)
            if latest and latest.payload:
                return self._from_row(latest)
        return await self.refresh(company_id)

    async def refresh(self, company_id: UUID, *, campaign_id: UUID | None = None) -> dict[str, Any] | None:
        data = await self.repository.build_input(company_id, campaign_id=campaign_id)
        if data is None:
            return None
        decision = self.engine.evaluate(data)
        row = await self.repository.store_decision(decision)
        return self._from_row(row)

    async def approval_center(self, *, limit: int = 50) -> dict[str, Any]:
        cards = await self.repository.list_approval_queue(limit=limit)
        return {"cards": cards, "total": len(cards), "scoring_version": "lre-v1"}

    async def proposals(self, *, limit: int = 50) -> dict[str, Any]:
        rows = await self.repository.list_proposals(limit=limit)
        return {
            "proposals": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),
                    "campaign_id": str(r.campaign_id) if r.campaign_id else None,
                    "title": r.title,
                    "version": r.version,
                    "tracking_id": r.tracking_id,
                    "pricing": r.pricing,
                    "status": r.status,
                    "opens": r.opens,
                    "downloads": r.downloads,
                    "payload": r.payload,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "total": len(rows),
        }

    async def track(
        self,
        *,
        tracking_id: str,
        event_type: str,
        company_id: UUID | None = None,
        campaign_id: UUID | None = None,
        target_url: str | None = None,
    ) -> dict[str, str]:
        row = await self.repository.record_tracking(
            tracking_id=tracking_id,
            event_type=event_type,
            company_id=company_id,
            campaign_id=campaign_id,
            target_url=target_url,
        )
        return {"id": str(row.id), "tracked": "true", "event_type": event_type}

    async def dashboard(self) -> dict[str, Any]:
        return await self.repository.dashboard()

    async def command_center(self) -> dict[str, Any]:
        dash = await self.dashboard()
        approvals = await self.approval_center(limit=10)
        proposals = await self.proposals(limit=10)
        return {
            **dash,
            "approvals": approvals.get("cards") or [],
            "proposal_queue": proposals.get("proposals") or [],
            "mission": "Approve outreach, reply to interested companies, attend meetings, send proposals, close clients.",
        }

    def _from_row(self, row: Any) -> dict[str, Any]:
        payload = dict(row.payload or {})
        payload["run_id"] = str(row.id)
        payload["company_id"] = str(row.company_id)
        payload["company_name"] = row.company_name
        payload["campaign_id"] = str(row.campaign_id) if row.campaign_id else None
        payload["stage"] = row.stage
        payload["scoring_version"] = row.scoring_version
        payload["created_at"] = row.created_at.isoformat() if row.created_at else None
        return payload
