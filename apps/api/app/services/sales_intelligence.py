from __future__ import annotations

from typing import Any
from uuid import UUID

from app.repositories.sales_intelligence import SalesIntelligenceRepository
from sales_intelligence import SalesIntelligenceService


class SalesIntelligencePlatformService:
    def __init__(self, repository: SalesIntelligenceRepository) -> None:
        self.repository = repository
        self.engine = SalesIntelligenceService()

    async def company_pack(self, company_id: UUID, *, refresh: bool = False) -> dict[str, Any] | None:
        if not refresh:
            latest = await self.repository.latest_for_company(company_id)
            if latest and latest.payload:
                return self._from_row(latest)
        return await self.refresh(company_id)

    async def opportunity_pack(self, opportunity_id: UUID, *, refresh: bool = False) -> dict[str, Any] | None:
        latest = await self.repository.latest_for_opportunity(opportunity_id)
        if latest and latest.payload and not refresh:
            return self._from_row(latest)
        if latest is None:
            return None
        return await self.refresh(latest.company_id, opportunity_id=opportunity_id)

    async def refresh(self, company_id: UUID, *, opportunity_id: UUID | None = None) -> dict[str, Any] | None:
        data = await self.repository.build_input(company_id, opportunity_id=opportunity_id)
        if data is None:
            return None
        decision = self.engine.evaluate(data)
        row = await self.repository.store_decision(decision)
        return self._from_row(row)

    async def dashboard(self) -> dict[str, Any]:
        return await self.repository.dashboard()

    async def process_reply_updates(self, *, limit: int = 40) -> dict[str, Any]:
        company_ids = await self.repository.companies_needing_refresh(limit=limit)
        refreshed: list[str] = []
        for company_id in company_ids:
            pack = await self.refresh(company_id)
            if pack:
                refreshed.append(str(company_id))
        return {"refreshed": len(refreshed), "company_ids": refreshed}

    def _from_row(self, row: Any) -> dict[str, Any]:
        payload = dict(row.payload or {})
        payload["snapshot_id"] = str(row.id)
        payload["company_id"] = str(row.company_id)
        payload["company_name"] = row.company_name
        payload["opportunity_id"] = str(row.opportunity_id) if row.opportunity_id else None
        payload["buying_intent_score"] = row.buying_intent_score
        payload["buying_stage"] = row.buying_stage
        payload["urgency"] = row.urgency
        payload["primary_offer"] = row.primary_offer
        payload["deal_probability"] = row.deal_probability
        payload["close_probability"] = row.close_probability
        payload["scoring_version"] = row.scoring_version
        payload["created_at"] = row.created_at.isoformat() if row.created_at else None
        return payload
