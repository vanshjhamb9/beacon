"""Read-only FastAPI APIs for Opportunity Intelligence."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from opportunity_intelligence.constants import SCORING_VERSION, SCORE_WEIGHTS
from opportunity_intelligence.dashboard_service import DashboardService
from opportunity_intelligence.signal_registry import SignalRegistry
from opportunity_intelligence.source_registry import SourceRegistry


class OpportunityReadService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.dashboard = DashboardService()

    async def list(self, *, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        rows = await self._opportunity_rows(limit=limit, offset=offset)
        return {"items": rows, "count": len(rows), "scoring_version": SCORING_VERSION}

    async def get(self, opportunity_id: UUID) -> dict[str, Any]:
        result = await self.session.execute(
            text("select * from opportunities where id = :id"),
            {"id": str(opportunity_id)},
        )
        row = result.mappings().first()
        if row is None:
            return {"error": "opportunity_not_found", "id": str(opportunity_id)}
        payload = dict(row)
        payload["evidence"] = await self._evidence_rows(opportunity_id)
        payload["scores"] = await self._score_rows(opportunity_id)
        return self._serialize(payload)

    async def top(self, *, limit: int = 25) -> dict[str, Any]:
        rows = await self._opportunity_rows(limit=limit, offset=0, top=True)
        return {"items": rows, "count": len(rows), "scoring_version": SCORING_VERSION}

    async def stats(self) -> dict[str, Any]:
        rows = await self._opportunity_rows(limit=500, offset=0, top=True)
        dashboard = self.dashboard.build(rows)
        dashboard["scoring_version"] = SCORING_VERSION
        return dashboard

    def config(self) -> dict[str, Any]:
        return {
            "scoring_version": SCORING_VERSION,
            "weights": dict(SCORE_WEIGHTS),
            "signals": [asdict(signal) for signal in SignalRegistry().all()],
            "sources": [asdict(source) for source in SourceRegistry().all()],
        }

    def signal_types(self) -> dict[str, Any]:
        signals = SignalRegistry().enabled()
        return {"items": [signal.name.value for signal in signals], "count": len(signals)}

    async def _opportunity_rows(
        self,
        *,
        limit: int,
        offset: int,
        top: bool = False,
    ) -> list[dict[str, Any]]:
        query = text("select * from opportunities order by created_at desc limit :limit offset :offset")
        if top:
            query = text(
                "select * from opportunities "
                "order by opportunity_score desc, confidence desc nulls last, freshness_score desc nulls last "
                "limit :limit offset :offset"
            )
        result = await self.session.execute(
            query,
            {"limit": limit, "offset": offset},
        )
        rows = [self._serialize(dict(row)) for row in result.mappings().all()]
        for row in rows:
            row["evidence_count"] = await self._evidence_count(row["id"])
        return rows

    async def _evidence_count(self, opportunity_id: UUID | str) -> int:
        result = await self.session.execute(
            text("select count(*) from opportunity_evidence where opportunity_id = :id"),
            {"id": str(opportunity_id)},
        )
        return int(result.scalar_one() or 0)

    async def _evidence_rows(self, opportunity_id: UUID) -> list[dict[str, Any]]:
        result = await self.session.execute(
            text("select * from opportunity_evidence where opportunity_id = :id order by captured_at desc"),
            {"id": str(opportunity_id)},
        )
        return [self._serialize(dict(row)) for row in result.mappings().all()]

    async def _score_rows(self, opportunity_id: UUID) -> list[dict[str, Any]]:
        result = await self.session.execute(
            text("select * from opportunity_scores where opportunity_id = :id order by calculated_at desc"),
            {"id": str(opportunity_id)},
        )
        return [self._serialize(dict(row)) for row in result.mappings().all()]

    def _serialize(self, row: dict[str, Any]) -> dict[str, Any]:
        return {key: value.isoformat() if hasattr(value, "isoformat") else value for key, value in row.items()}


def build_opportunity_router(get_service: Callable[..., Any]) -> APIRouter:
    router = APIRouter(prefix="/opportunities", tags=["opportunities"])

    @router.get("")
    async def list_opportunities(
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        service: Any = Depends(get_service),
    ) -> dict[str, Any]:
        return await service.list(limit=limit, offset=offset)

    @router.get("/top")
    async def top_opportunities(
        limit: int = Query(default=25, ge=1, le=100),
        service: Any = Depends(get_service),
    ) -> dict[str, Any]:
        return await service.top(limit=limit)

    @router.get("/stats")
    async def stats(service: Any = Depends(get_service)) -> dict[str, Any]:
        return await service.stats()

    @router.get("/config")
    async def config(service: Any = Depends(get_service)) -> dict[str, Any]:
        return service.config()

    @router.get("/signal-types")
    async def signal_types(service: Any = Depends(get_service)) -> dict[str, Any]:
        return service.signal_types()

    @router.get("/{opportunity_id}")
    async def get_opportunity(opportunity_id: UUID, service: Any = Depends(get_service)) -> dict[str, Any]:
        payload = await service.get(opportunity_id)
        if payload.get("error") == "opportunity_not_found":
            raise HTTPException(status_code=404, detail="Opportunity not found")
        return payload

    return router
