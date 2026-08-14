from __future__ import annotations

from typing import Any
from uuid import UUID

from app.repositories.global_opportunity_acquisition import GlobalOpportunityAcquisitionRepository
from global_opportunity_acquisition import GlobalOpportunityAcquisitionService
from global_opportunity_acquisition.connectors.catalog import connector_catalog
from global_opportunity_acquisition.models.types import CompanyObservation, GOAPInput


class GlobalOpportunityAcquisitionPlatformService:
    def __init__(self, repository: GlobalOpportunityAcquisitionRepository) -> None:
        self.repository = repository
        self.engine = GlobalOpportunityAcquisitionService()
        self._last: dict[str, Any] | None = None

    async def refresh(self, *, limit: int = 40) -> dict[str, Any]:
        data = await self.repository.build_input(limit=limit)
        decision = self.engine.evaluate(data)
        stored = await self.repository.store_decision(decision)
        payload = {
            "scoring_version": decision.scoring_version,
            "analytics": decision.analytics.model_dump(mode="json"),
            "daily_report": decision.daily_report.model_dump(mode="json") if decision.daily_report else {},
            "connectors": [c.model_dump(mode="json") for c in decision.connectors],
            "benchmarks": [b.model_dump(mode="json") for b in decision.benchmarks[:20]],
            "companies": [
                {
                    "company_name": p.company_name,
                    "canonical_key": p.canonical_key,
                    "intents": [i.intent.value for i in p.intents],
                    "freshness": p.freshness.score if p.freshness else 0,
                    "website_opportunity": p.website.opportunity_score if p.website else 0,
                }
                for p in decision.companies[:50]
            ],
            "stored": stored,
            "evidence_chain": decision.evidence_chain,
        }
        self._last = payload
        return payload

    async def dashboard(self) -> dict[str, Any]:
        if self._last is None:
            return await self.refresh(limit=25)
        return {
            "scoring_version": self._last.get("scoring_version"),
            "analytics": self._last.get("analytics", {}),
            "companies": self._last.get("companies", []),
            "benchmarks": self._last.get("benchmarks", []),
            "daily_report": self._last.get("daily_report", {}),
        }

    async def connectors(self) -> dict[str, Any]:
        rows = await self.repository.list_connectors()
        if not rows:
            catalog = connector_catalog()
            return {
                "connectors": [c.model_dump(mode="json") for c in catalog],
                "total": len(catalog),
            }
        return {
            "connectors": [
                {
                    "connector_id": r.connector_id,
                    "connector_name": r.connector_name,
                    "access_mode": r.access_mode,
                    "status": r.status,
                    "category": r.category,
                    "payload": r.payload,
                }
                for r in rows
            ],
            "total": len(rows),
        }

    async def connector(self, connector_id: str) -> dict[str, Any] | None:
        row = await self.repository.get_connector(connector_id)
        if row:
            return {
                "connector_id": row.connector_id,
                "connector_name": row.connector_name,
                "access_mode": row.access_mode,
                "status": row.status,
                "category": row.category,
                "payload": row.payload,
                "evidence": row.evidence,
            }
        for c in connector_catalog():
            if c.connector_id == connector_id:
                return c.model_dump(mode="json")
        return None

    async def company_graph(self, company_id: UUID) -> dict[str, Any] | None:
        company = await self.repository.company_by_id(company_id)
        if company is None:
            # allow direct key lookup
            return await self.repository.graph_for_company(str(company_id))
        attrs = company.attributes or {}
        obs = CompanyObservation(
            company_id=company.id,
            company_name=company.name,
            company_domain=str(attrs.get("domain") or "") or None,
            industry=company.industry,
            source_texts=list(attrs.get("source_texts") or [company.name]),
            html_hints=list(attrs.get("html_hints") or []),
            job_titles=list(attrs.get("job_titles") or []),
            funding_text=list(attrs.get("funding_text") or []),
            review_text=list(attrs.get("review_text") or []),
            community_text=list(attrs.get("community_text") or []),
            decision_makers=list(attrs.get("decision_makers") or []),
        )
        decision = self.engine.evaluate(GOAPInput(companies=[obs]))
        pack = decision.companies[0] if decision.companies else None
        if pack is None or pack.graph is None:
            return None
        await self.repository.store_decision(decision)
        return pack.graph.model_dump(mode="json")

    async def websites(self) -> dict[str, Any]:
        rows = await self.repository.latest_websites()
        return {
            "profiles": [
                {
                    "company_key": r.company_key,
                    "company_name": r.company_name,
                    "domain": r.domain,
                    "modernization_score": r.modernization_score,
                    "opportunity_score": r.opportunity_score,
                    "payload": r.payload,
                }
                for r in rows
            ],
            "total": len(rows),
        }

    async def website(self, company_key: str) -> dict[str, Any] | None:
        rows = await self.repository.latest_websites(limit=100)
        for r in rows:
            if r.company_key == company_key:
                return r.payload
        return None

    async def technologies(self) -> dict[str, Any]:
        rows = await self.repository.latest_tech()
        return {
            "profiles": [
                {
                    "company_key": r.company_key,
                    "technology": r.technology,
                    "category": r.category,
                    "confidence": r.confidence,
                }
                for r in rows
            ],
            "total": len(rows),
        }

    async def technology(self, company_key: str) -> dict[str, Any]:
        rows = await self.repository.latest_tech(limit=200)
        items = [r for r in rows if r.company_key == company_key]
        return {
            "company_key": company_key,
            "technologies": [{"technology": r.technology, "category": r.category, "confidence": r.confidence} for r in items],
            "total": len(items),
        }

    async def funding(self) -> dict[str, Any]:
        rows = await self.repository.latest_funding()
        return {"events": [{"company_key": r.company_key, "round": r.round, "confidence": r.confidence} for r in rows], "total": len(rows)}

    async def hiring(self) -> dict[str, Any]:
        rows = await self.repository.latest_hiring()
        return {"events": [{"company_key": r.company_key, "growth": r.growth, "payload": r.payload} for r in rows], "total": len(rows)}

    async def reviews(self) -> dict[str, Any]:
        rows = await self.repository.latest_reviews()
        return {"signals": [{"company_key": r.company_key, "payload": r.payload} for r in rows], "total": len(rows)}

    async def community(self) -> dict[str, Any]:
        rows = await self.repository.latest_community()
        return {
            "signals": [{"company_key": r.company_key, "confidence": r.confidence, "payload": r.payload} for r in rows],
            "total": len(rows),
        }

    async def benchmarks(self) -> dict[str, Any]:
        rows = await self.repository.latest_benchmarks()
        if rows:
            return {
                "benchmarks": [
                    {"connector_id": r.connector_id, "rank": r.rank, "recommendation": r.recommendation, "payload": r.payload}
                    for r in rows
                ],
                "total": len(rows),
            }
        if self._last:
            return {"benchmarks": self._last.get("benchmarks", []), "total": len(self._last.get("benchmarks", []))}
        refreshed = await self.refresh(limit=10)
        return {"benchmarks": refreshed.get("benchmarks", []), "total": len(refreshed.get("benchmarks", []))}

    async def freshness(self) -> dict[str, Any]:
        if self._last is None:
            await self.refresh(limit=20)
        companies = (self._last or {}).get("companies", [])
        return {
            "scores": [{"company_name": c.get("company_name"), "freshness": c.get("freshness")} for c in companies],
            "average": (self._last or {}).get("analytics", {}).get("average_freshness", 0),
            "total": len(companies),
        }

    async def analytics(self) -> dict[str, Any]:
        if self._last is None:
            await self.refresh(limit=20)
        return (self._last or {}).get("analytics", {})

    async def daily_report(self) -> dict[str, Any]:
        if self._last is None:
            await self.refresh(limit=20)
        return (self._last or {}).get("daily_report", {})
