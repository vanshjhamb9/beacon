from __future__ import annotations

from typing import Any
from uuid import UUID

from app.repositories.autonomous_sales_agent import AutonomousSalesAgentRepository
from autonomous_sales_agent import AutonomousSalesAgentService
from autonomous_sales_agent.analytics.engine import AsaAnalyticsEngine


class AutonomousSalesAgentPlatformService:
    def __init__(self, repository: AutonomousSalesAgentRepository) -> None:
        self.repository = repository
        self.engine = AutonomousSalesAgentService()
        self.analytics = AsaAnalyticsEngine()

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
        return self._from_row(row)

    async def work_queue(self, *, limit: int = 50, refresh: bool = False) -> dict[str, Any]:
        runs = await self.repository.recent_runs(limit=limit)
        if refresh or not runs:
            await self.refresh_batch(limit=min(limit, 25))
            runs = await self.repository.recent_runs(limit=limit)

        items: list[dict[str, Any]] = []
        for run in runs:
            payload = run.payload or {}
            for w in payload.get("work_queue") or []:
                items.append(
                    {
                        **w,
                        "run_id": str(run.id),
                        "stage": run.stage,
                        "next_action": run.next_action,
                        "confidence": run.confidence,
                    }
                )
        # Deduplicate by company+kind
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for item in items:
            key = f"{item.get('company_id')}:{item.get('kind')}:{item.get('summary')}"
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)

        priority_order = {"P0": 0, "P1": 1, "P2": 2}
        unique.sort(key=lambda x: (priority_order.get(str(x.get("priority") or "P2"), 9), str(x.get("kind"))))
        unique = unique[:limit]

        await self.repository.store_work_queue_snapshot(
            kind="work_queue",
            payload={"items": unique},
            item_count=len(unique),
            revenue_forecast=0.0,
            evidence=[f"items:{len(unique)}"],
        )
        return {
            "items": unique,
            "total": len(unique),
            "scoring_version": "asa-v1",
            "founder_focus": [
                "Approve outreach",
                "Attend meetings",
                "Write proposals",
                "Close deals",
            ],
        }

    async def morning_brief(self, *, refresh: bool = False) -> dict[str, Any]:
        if not refresh:
            latest = await self.repository.latest_brief()
            if latest and latest.payload:
                return {
                    **latest.payload,
                    "snapshot_id": str(latest.id),
                    "item_count": latest.item_count,
                    "revenue_forecast": latest.revenue_forecast,
                    "scoring_version": latest.scoring_version,
                    "created_at": latest.created_at.isoformat() if latest.created_at else None,
                }

        await self.refresh_batch(limit=30)
        runs = await self.repository.recent_runs(limit=40)
        priorities: list[str] = []
        meetings: list[dict[str, Any]] = []
        replies: list[dict[str, Any]] = []
        risks: list[dict[str, Any]] = []
        attention: list[dict[str, Any]] = []
        follow_ups: list[dict[str, Any]] = []
        forecast = 0.0
        for run in runs:
            brief = (run.payload or {}).get("morning_brief") or {}
            priorities.extend(list(brief.get("priorities") or [])[:2])
            meetings.extend(list(brief.get("expected_meetings") or []))
            replies.extend(list(brief.get("expected_replies") or []))
            risks.extend(list(brief.get("high_risk_deals") or []))
            attention.extend(list(brief.get("companies_requiring_attention") or []))
            follow_ups.extend(list(brief.get("follow_ups_due") or []))
            forecast += float(brief.get("revenue_forecast") or 0)

        # Deduplicate priorities
        seen_p: set[str] = set()
        uniq_priorities = []
        for p in priorities:
            if p in seen_p:
                continue
            seen_p.add(p)
            uniq_priorities.append(p)

        payload = {
            "priorities": uniq_priorities[:8],
            "expected_meetings": meetings[:10],
            "expected_replies": replies[:10],
            "high_risk_deals": risks[:10],
            "companies_requiring_attention": attention[:10],
            "revenue_forecast": round(forecast, 2),
            "follow_ups_due": follow_ups[:15],
        }
        row = await self.repository.store_work_queue_snapshot(
            kind="morning_brief",
            payload=payload,
            item_count=len(uniq_priorities),
            revenue_forecast=payload["revenue_forecast"],
            evidence=[f"runs:{len(runs)}"],
        )
        return {
            **payload,
            "snapshot_id": str(row.id),
            "scoring_version": "asa-v1",
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    async def timeline(self, company_id: UUID, *, limit: int = 100) -> dict[str, Any]:
        events = await self.repository.timeline_for_company(company_id, limit=limit)
        if not events:
            pack = await self.refresh(company_id)
            if pack is None:
                return {"events": [], "total": 0}
            events = await self.repository.timeline_for_company(company_id, limit=limit)
        return {
            "events": [
                {
                    "id": str(e.id),
                    "event_type": e.event_type,
                    "title": e.title,
                    "detail": e.detail,
                    "actor": e.actor,
                    "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
                    "evidence": e.evidence,
                }
                for e in events
            ],
            "total": len(events),
        }

    async def dashboard(self) -> dict[str, Any]:
        dash = await self.repository.dashboard()
        queue = await self.work_queue(limit=20)
        brief = await self.morning_brief()
        return {
            **dash,
            "work_queue_total": queue.get("total", 0),
            "morning_brief": {
                "priorities": (brief.get("priorities") or [])[:5],
                "revenue_forecast": brief.get("revenue_forecast", 0),
                "follow_ups_due": len(brief.get("follow_ups_due") or []),
            },
        }

    async def refresh_batch(self, *, limit: int = 25) -> dict[str, Any]:
        ids = await self.repository.company_ids_for_refresh(limit=limit)
        refreshed = 0
        for company_id in ids:
            pack = await self.refresh(company_id)
            if pack:
                refreshed += 1
        return {"refreshed": refreshed, "requested": len(ids)}

    def _from_row(self, row: Any) -> dict[str, Any]:
        payload = dict(row.payload or {})
        payload["run_id"] = str(row.id)
        payload["company_id"] = str(row.company_id)
        payload["company_name"] = row.company_name
        payload["stage"] = row.stage
        payload["next_action"] = row.next_action
        payload["confidence"] = row.confidence
        payload["scoring_version"] = row.scoring_version
        payload["created_at"] = row.created_at.isoformat() if row.created_at else None
        return payload
