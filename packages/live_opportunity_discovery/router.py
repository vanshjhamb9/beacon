"""Read-only APIs for Live Opportunity Discovery Engine."""

from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from live_opportunity_discovery.buying_signal_classifier import DISCOVERY_CATEGORIES
from live_opportunity_discovery.dashboard_service import DashboardService
from live_opportunity_discovery.freshness_filter import LIVE_REFRESH_MINUTES


class LiveOpportunityReadService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.dashboard_service = DashboardService()

    async def live(self, *, window_days: int = 7, limit: int = 100) -> dict[str, Any]:
        rows = await self._rows(window_days=window_days, limit=limit)
        return {
            "items": rows,
            "count": len(rows),
            "refresh_minutes": LIVE_REFRESH_MINUTES,
            "strategy": "buying_events",
        }

    async def company(self, company_id: UUID) -> dict[str, Any]:
        rows = await self._rows(company_id=company_id, window_days=45, limit=200)
        return {
            "company_id": str(company_id),
            "items": rows,
            "timeline": self.dashboard_service.timeline(rows),
            "count": len(rows),
        }

    async def timeline(self, company_id: UUID | None = None) -> dict[str, Any]:
        rows = await self._rows(company_id=company_id, window_days=45, limit=500)
        return {"items": self.dashboard_service.timeline(rows), "count": len(rows)}

    async def categories(self) -> dict[str, Any]:
        return {"items": list(DISCOVERY_CATEGORIES), "count": len(DISCOVERY_CATEGORIES)}

    async def trending(self) -> dict[str, Any]:
        rows = await self._rows(window_days=7, limit=500)
        items = self.dashboard_service.trending(rows)
        return {"items": items, "count": len(items)}

    async def dashboard(self, *, window_days: int = 7) -> dict[str, Any]:
        rows = await self._rows(window_days=window_days, limit=500)
        return self.dashboard_service.build(rows)

    async def _rows(
        self,
        *,
        company_id: UUID | None = None,
        window_days: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"window_days": window_days, "limit": limit}
        query = text(
            "select * from live_opportunity_events "
            "where event_timestamp >= now() - (:window_days * interval '1 day') "
            "order by priority_score desc, event_timestamp desc limit :limit"
        )
        if company_id is not None:
            params["company_id"] = str(company_id)
            query = text(
                "select * from live_opportunity_events "
                "where event_timestamp >= now() - (:window_days * interval '1 day') "
                "and company_id = :company_id "
                "order by priority_score desc, event_timestamp desc limit :limit"
            )
        result = await self.session.execute(query, params)
        rows = [self._serialize(dict(row)) for row in result.mappings().all()]
        for row in rows:
            row["evidence"] = await self._evidence(row["id"])
            row["evidence_count"] = len(row["evidence"])
        return rows

    async def _evidence(self, event_id: UUID | str) -> list[dict[str, Any]]:
        result = await self.session.execute(
            text("select * from live_opportunity_evidence where event_id = :event_id order by discovered_at desc"),
            {"event_id": str(event_id)},
        )
        return [self._serialize(dict(row)) for row in result.mappings().all()]

    def _serialize(self, row: dict[str, Any]) -> dict[str, Any]:
        return {key: value.isoformat() if hasattr(value, "isoformat") else value for key, value in row.items()}


def build_live_opportunity_router(get_service: Callable[..., Any]) -> APIRouter:
    router = APIRouter(prefix="/opportunities", tags=["live-opportunity-discovery"])

    @router.get("/live")
    async def live(
        window_days: int = Query(default=7, ge=0, le=21),
        limit: int = Query(default=100, ge=1, le=500),
        service: Any = Depends(get_service),
    ) -> dict[str, Any]:
        return await service.live(window_days=window_days, limit=limit)

    @router.get("/company/{company_id}")
    async def company(company_id: UUID, service: Any = Depends(get_service)) -> dict[str, Any]:
        return await service.company(company_id)

    @router.get("/timeline")
    async def timeline(
        company_id: UUID | None = Query(default=None),
        service: Any = Depends(get_service),
    ) -> dict[str, Any]:
        return await service.timeline(company_id)

    @router.get("/categories")
    async def categories(service: Any = Depends(get_service)) -> dict[str, Any]:
        return await service.categories()

    @router.get("/trending")
    async def trending(service: Any = Depends(get_service)) -> dict[str, Any]:
        return await service.trending()

    @router.get("/dashboard")
    async def dashboard(
        window_days: int = Query(default=7, ge=0, le=21),
        service: Any = Depends(get_service),
    ) -> dict[str, Any]:
        return await service.dashboard(window_days=window_days)

    return router
