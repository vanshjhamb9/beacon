from __future__ import annotations

from typing import Any
from uuid import UUID

from app.repositories.account_intelligence import AccountIntelligenceRepository
from account_intelligence import AccountIntelligenceService


class AccountIntelligencePlatformService:
    def __init__(self, repository: AccountIntelligenceRepository) -> None:
        self.repository = repository
        self.engine = AccountIntelligenceService()
        self._cache: list[dict[str, Any]] = []

    async def refresh(self, company_id: UUID) -> dict[str, Any] | None:
        data = await self.repository.build_input(company_id)
        if data is None:
            return None
        decision = self.engine.evaluate(data)
        row = await self.repository.store_decision(decision)
        pack = self._pack(row)
        self._cache = [p for p in self._cache if p.get("company_id") != str(company_id)]
        self._cache.insert(0, pack)
        return pack

    async def refresh_batch(self, *, limit: int = 30) -> dict[str, Any]:
        ids = await self.repository.company_ids(limit=limit)
        n = 0
        for cid in ids:
            if await self.refresh(cid):
                n += 1
        return {"refreshed": n, "requested": len(ids)}

    async def company(self, company_id: UUID, *, refresh: bool = False) -> dict[str, Any] | None:
        if not refresh:
            latest = await self.repository.latest_for_company(company_id)
            if latest:
                return self._pack(latest)
        return await self.refresh(company_id)

    async def dashboard(self) -> dict[str, Any]:
        rows = await self.repository.recent(limit=40)
        by_cat: dict[str, int] = {}
        for r in rows:
            by_cat[r.sales_readiness_category] = by_cat.get(r.sales_readiness_category, 0) + 1
        return {
            "total_accounts": len(rows),
            "by_sales_readiness": by_cat,
            "accounts": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id) if r.company_id else None,
                    "company_name": r.company_name,
                    "sales_readiness_score": r.sales_readiness_score,
                    "sales_readiness_category": r.sales_readiness_category,
                    "ai_readiness_score": r.ai_readiness_score,
                    "overall_confidence": r.overall_confidence,
                }
                for r in rows
            ],
            "scoring_version": "aip-v1",
            "licensed_providers_disabled": ["apollo", "people_data_labs", "zoominfo", "clearbit", "crunchbase"],
        }

    async def search(self, *, q: str = "", industry: str | None = None, country: str | None = None, sales_readiness: str | None = None, technology: str | None = None) -> dict[str, Any]:
        rows = await self.repository.recent(limit=100)
        decisions = []
        for r in rows:
            # lightweight filter on stored payload
            payload = r.payload or {}
            hay = " ".join(
                [
                    r.company_name,
                    str(payload.get("profile", {}).get("industry", {}).get("value") or ""),
                    str(payload.get("profile", {}).get("country", {}).get("value") or ""),
                    r.sales_readiness_category,
                    " ".join(payload.get("technology", {}).get("crm") or []),
                    " ".join(payload.get("technology", {}).get("framework") or []),
                ]
            ).lower()
            if q and q.lower() not in hay:
                continue
            if industry and industry.lower() not in hay:
                continue
            if country and country.lower() not in hay:
                continue
            if sales_readiness and r.sales_readiness_category != sales_readiness:
                continue
            if technology and technology.lower() not in hay:
                continue
            decisions.append(self._pack(r))
        return {"results": decisions, "total": len(decisions)}

    def _section(self, pack: dict[str, Any], key: str) -> Any:
        return pack.get(key)

    def _pack(self, row: Any) -> dict[str, Any]:
        payload = dict(row.payload or {})
        payload["profile_id"] = str(row.id)
        payload["company_id"] = str(row.company_id) if row.company_id else None
        payload["company_name"] = row.company_name
        payload["sales_readiness_score"] = row.sales_readiness_score
        payload["sales_readiness_category"] = row.sales_readiness_category
        payload["ai_readiness_score"] = row.ai_readiness_score
        payload["overall_confidence"] = row.overall_confidence
        payload["scoring_version"] = row.scoring_version
        payload["created_at"] = row.created_at.isoformat() if row.created_at else None
        return payload
