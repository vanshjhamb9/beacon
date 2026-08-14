from __future__ import annotations

from typing import Any
from uuid import UUID

from app.repositories.revenue_optimization import RevenueOptimizationRepository
from revenue_optimization import RevenueOptimizationService
from revenue_optimization.models.types import ROIPInput


class RevenueOptimizationPlatformService:
    def __init__(self, repository: RevenueOptimizationRepository) -> None:
        self.repository = repository
        self.engine = RevenueOptimizationService()
        self._last: dict[str, Any] | None = None

    async def refresh(self, *, limit: int = 100) -> dict[str, Any]:
        data = await self.repository.build_input(limit=limit)
        decision = self.engine.evaluate(data)
        await self.repository.store_decision(decision)
        payload = decision.model_dump(mode="json")
        self._last = payload
        return payload

    async def dashboard(self) -> dict[str, Any]:
        if self._last is None:
            await self.refresh(limit=50)
        last = self._last or {}
        return {
            "scoring_version": last.get("scoring_version", "roip-v1"),
            "email": last.get("email_metrics", {}),
            "founder": last.get("founder", {}),
            "subjects": last.get("subjects", [])[:20],
            "ctas": last.get("ctas", [])[:20],
            "followup": last.get("followup", {}),
            "industries": last.get("industries", [])[:10],
            "offers": last.get("offers", [])[:10],
            "replies": last.get("replies", [])[:50],
            "recommendations": last.get("recommendations", [])[:10],
            "benchmarks": last.get("benchmarks", []),
            "learning": last.get("learning", {}),
            "learning_summary": (last.get("learning") or {}).get("summary"),
            "evidence_chain": last.get("evidence_chain", []),
            "note": "Recommendations require founder approval and never auto-apply.",
        }

    async def company(self, company_id: UUID) -> dict[str, Any]:
        data = await self.repository.build_input(limit=200)
        filtered = [e for e in data.events if e.company_id == company_id]
        decision = self.engine.evaluate(ROIPInput(events=filtered, previous_period_events=[], portfolio_assets=data.portfolio_assets))
        return decision.model_dump(mode="json")

    async def campaign(self, campaign_id: str) -> dict[str, Any]:
        data = await self.repository.build_input(limit=200)
        filtered = [e for e in data.events if e.campaign_id == campaign_id]
        decision = self.engine.evaluate(ROIPInput(events=filtered, previous_period_events=[], portfolio_assets=[]))
        return decision.model_dump(mode="json")

    async def founder(self) -> dict[str, Any]:
        row = await self.repository.latest_founder()
        if row:
            return row.payload
        if self._last is None:
            await self.refresh(limit=40)
        return (self._last or {}).get("founder", {})

    async def industry(self) -> dict[str, Any]:
        rows = await self.repository.recent_industries()
        if rows:
            return {"industries": [r.payload for r in rows], "total": len(rows)}
        if self._last is None:
            await self.refresh(limit=40)
        return {"industries": (self._last or {}).get("industries", []), "total": len((self._last or {}).get("industries", []))}

    async def offers(self) -> dict[str, Any]:
        rows = await self.repository.recent_offers()
        if rows:
            return {"offers": [r.payload for r in rows], "total": len(rows)}
        if self._last is None:
            await self.refresh(limit=40)
        return {"offers": (self._last or {}).get("offers", []), "total": len((self._last or {}).get("offers", []))}

    async def recommendations(self) -> dict[str, Any]:
        rows = await self.repository.recent_recommendations()
        if rows:
            return {
                "recommendations": [r.payload for r in rows],
                "total": len(rows),
                "note": "Founder approval required. Never auto-applies.",
            }
        if self._last is None:
            await self.refresh(limit=40)
        return {
            "recommendations": (self._last or {}).get("recommendations", []),
            "total": len((self._last or {}).get("recommendations", [])),
            "note": "Founder approval required. Never auto-applies.",
        }

    async def benchmarks(self) -> dict[str, Any]:
        rows = await self.repository.recent_benchmarks()
        if rows:
            return {"benchmarks": [r.payload for r in rows], "total": len(rows)}
        if self._last is None:
            await self.refresh(limit=40)
        return {"benchmarks": (self._last or {}).get("benchmarks", []), "total": len((self._last or {}).get("benchmarks", []))}

    async def learning(self) -> dict[str, Any]:
        row = await self.repository.latest_learning()
        if row:
            return {**row.payload, "modifies_production": False}
        if self._last is None:
            await self.refresh(limit=40)
        return (self._last or {}).get("learning", {})

    async def replies(self) -> dict[str, Any]:
        rows = await self.repository.recent_replies()
        if rows:
            return {"replies": [r.payload for r in rows], "total": len(rows)}
        if self._last is None:
            await self.refresh(limit=40)
        return {"replies": (self._last or {}).get("replies", []), "total": len((self._last or {}).get("replies", []))}

    async def search(self, *, q: str = "", industry: str | None = None, offer: str | None = None, reply_type: str | None = None) -> dict[str, Any]:
        if self._last is None:
            await self.refresh(limit=50)
        from revenue_optimization.models.types import ROIPDecision

        decision = ROIPDecision.model_validate(self._last)
        return self.engine.search(
            decision,
            query=q,
            filters={"industry": industry, "offer": offer, "reply_type": reply_type},
        )
