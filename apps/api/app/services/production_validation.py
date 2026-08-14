from __future__ import annotations

from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.repositories.production_validation import ProductionValidationRepository
from app.services.production_hardening import ProductionHardeningService
from production_validation import ProductionValidationService


class ProductionValidationPlatformService:
    def __init__(
        self,
        repository: ProductionValidationRepository,
        *,
        session: AsyncSession | None = None,
        redis: Redis | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.repository = repository
        self.engine = ProductionValidationService()
        self.session = session
        self.redis = redis
        self.settings = settings

    async def _live_signals(self) -> dict[str, dict[str, float]] | None:
        if self.session is None or self.redis is None or self.settings is None:
            return None
        return await ProductionHardeningService(self.session, self.redis, self.settings).live_component_signals()

    async def refresh(self) -> dict[str, Any]:
        signals = await self._live_signals()
        data = await self.repository.build_platform_input(component_signals=signals)
        decision = self.engine.evaluate(data)
        row = await self.repository.store_decision(decision)
        return self._pack(decision, snapshot_id=str(row.id))

    async def report(self, *, refresh: bool = False) -> dict[str, Any]:
        if not refresh:
            latest = await self.repository.latest_snapshot()
            if latest and latest.payload:
                payload = dict(latest.payload)
                payload["snapshot_id"] = str(latest.id)
                payload["overall_score"] = latest.overall_score
                payload["overall_status"] = latest.overall_status
                payload["created_at"] = latest.created_at.isoformat() if latest.created_at else None
                return payload
        return await self.refresh()

    async def company_readiness(self, company_id: UUID, *, refresh: bool = True) -> dict[str, Any] | None:
        if not refresh:
            latest = await self.repository.latest_lead_score(company_id)
            if latest:
                return {
                    "company_id": str(latest.company_id),
                    "company_name": latest.company_name,
                    "score": latest.score,
                    "outreach_allowed": latest.outreach_allowed,
                    "checklist": latest.checklist,
                    "blocking_reasons": latest.blocking_reasons,
                    "evidence": latest.evidence,
                }
        data = await self.repository.build_company_input(company_id)
        if data is None:
            return None
        decision = self.engine.evaluate(data)
        await self.repository.store_decision(decision)
        if decision.lead_readiness is None:
            return None
        return decision.lead_readiness.model_dump(mode="json")

    async def production_health(self) -> dict[str, Any]:
        # Always refresh so component rates come from live probes, not stale hardcoded snapshots.
        pack = await self.refresh()
        health = pack.get("health") or {}
        return {
            "overall_status": health.get("overall_status") or pack.get("overall_status"),
            "overall_score": health.get("overall_score") or pack.get("overall_score"),
            "components": health.get("components") or [],
            "alerts": pack.get("alerts") or [],
            "scoring_version": pack.get("scoring_version"),
            "telemetry": "live",
        }

    async def revenue_dashboard(self) -> dict[str, Any]:
        pack = await self.report()
        return {
            "revenue": pack.get("revenue") or {},
            "founder_board": pack.get("founder_board") or {},
            "campaign_funnels": pack.get("campaign_funnels") or [],
            "weekly_report": pack.get("weekly_report") or {},
            "scoring_version": pack.get("scoring_version"),
        }

    async def alerts(self) -> dict[str, Any]:
        rows = await self.repository.open_alerts()
        if rows:
            return {
                "alerts": [
                    {
                        "id": str(r.id),
                        "code": r.code,
                        "title": r.title,
                        "severity": r.severity,
                        "recommendation": r.recommendation,
                        "owner": r.owner,
                        "evidence": r.evidence,
                    }
                    for r in rows
                ],
                "total": len(rows),
            }
        pack = await self.report()
        return {"alerts": pack.get("alerts") or [], "total": len(pack.get("alerts") or [])}

    async def playbooks(self) -> dict[str, Any]:
        books = [p.model_dump(mode="json") for p in self.engine.list_playbooks()]
        return {"playbooks": books, "total": len(books)}

    async def campaign_monitoring(self) -> dict[str, Any]:
        pack = await self.report()
        return {"funnels": pack.get("campaign_funnels") or [], "total": len(pack.get("campaign_funnels") or [])}

    def _pack(self, decision: Any, *, snapshot_id: str | None = None) -> dict[str, Any]:
        payload = decision.model_dump(mode="json")
        payload["snapshot_id"] = snapshot_id
        payload["overall_score"] = decision.readiness_report.overall_score
        payload["overall_status"] = decision.readiness_report.overall_status.value
        return payload
