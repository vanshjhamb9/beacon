from __future__ import annotations

from typing import Any
from uuid import UUID

from app.repositories.founder_os import FounderOsRepository
from founder_os import FounderOsService
from founder_os.models.types import AnalyticsEventType


class FounderOsPlatformService:
    def __init__(self, repository: FounderOsRepository) -> None:
        self.repository = repository
        self.engine = FounderOsService()

    async def refresh(self) -> dict[str, Any]:
        data = await self.repository.build_input()
        decision = self.engine.evaluate(data)
        row = await self.repository.store_decision(decision)
        await self.repository.append_analytics(self.engine.track_brief_view())
        return self._pack(decision, brief_id=str(row.id))

    async def command_center(self) -> dict[str, Any]:
        latest = await self.repository.latest_brief()
        if latest and latest.payload:
            return self._from_payload(latest.payload, brief_id=str(latest.id))
        return await self.refresh()

    async def daily_brief(self) -> dict[str, Any]:
        pack = await self.command_center()
        return pack.get("brief", {})

    async def assistant(self) -> dict[str, Any]:
        pack = await self.command_center()
        return pack.get("assistant", {})

    async def tasks(self, *, status: str | None = "open") -> list[dict[str, Any]]:
        rows = await self.repository.list_tasks(status=status)
        if rows:
            return [self._task_dict(r) for r in rows]
        pack = await self.command_center()
        return list(pack.get("tasks") or [])

    async def complete_task(self, task_id: UUID) -> dict[str, Any] | None:
        row = await self.repository.complete_task(task_id)
        if row is None:
            return None
        await self.repository.append_analytics(
            self.engine.track(
                event_type=AnalyticsEventType.TASK,
                action="complete_task",
                entity_type="task",
                entity_id=str(task_id),
                company_id=row.company_id,
            )
        )
        return self._task_dict(row)

    async def kpis(self) -> dict[str, Any]:
        pack = await self.command_center()
        return pack.get("kpis", {})

    async def recommendations(self) -> list[dict[str, Any]]:
        pack = await self.command_center()
        return list(pack.get("recommendations") or [])

    async def proposals(self) -> list[dict[str, Any]]:
        pack = await self.command_center()
        return list(pack.get("proposals") or [])

    async def meetings(self) -> list[dict[str, Any]]:
        pack = await self.command_center()
        return list(pack.get("meeting_packs") or [])

    async def timeline(self, company_id: UUID) -> list[dict[str, Any]]:
        rows = await self.repository.company_timeline(company_id)
        return [
            {
                "id": str(r.id),
                "event_key": r.event_key,
                "company_id": str(r.company_id),
                "company_name": r.company_name,
                "stage": r.stage,
                "occurred_at": r.occurred_at.isoformat() if r.occurred_at else None,
                "summary": r.summary,
                "evidence": r.evidence,
                "actor": r.actor,
                "immutable": r.immutable,
            }
            for r in rows
        ]

    async def track(
        self,
        *,
        event_type: str,
        action: str,
        actor: str = "founder",
        company_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        event = self.engine.track(
            event_type=AnalyticsEventType(event_type),
            action=action,
            actor=actor,
            company_id=company_id,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload or {},
        )
        row = await self.repository.append_analytics(event)
        return {"id": str(row.id), "tracked": "true"}

    def _pack(self, decision: Any, *, brief_id: str | None = None) -> dict[str, Any]:
        return {
            "brief_id": brief_id,
            "brief": decision.brief.model_dump(mode="json"),
            "command_center": decision.command_center.model_dump(mode="json"),
            "assistant": decision.assistant.model_dump(mode="json"),
            "tasks": [t.model_dump(mode="json") for t in decision.tasks],
            "kpis": decision.kpis.model_dump(mode="json"),
            "recommendations": [r.model_dump(mode="json") for r in decision.recommendations],
            "proposals": [p.model_dump(mode="json") for p in decision.proposals],
            "meeting_packs": [m.model_dump(mode="json") for m in decision.meeting_packs],
            "timeline_events": [e.model_dump(mode="json") for e in decision.timeline_events],
            "scoring_version": decision.scoring_version,
        }

    def _from_payload(self, payload: dict[str, Any], *, brief_id: str | None = None) -> dict[str, Any]:
        out = dict(payload)
        out["brief_id"] = brief_id
        return out

    def _task_dict(self, row: Any) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "task_id": row.task_key,
            "kind": row.kind,
            "title": row.title,
            "priority": row.priority,
            "deadline": row.deadline.isoformat() if row.deadline else None,
            "owner": row.owner,
            "status": row.status,
            "reason": row.reason,
            "evidence": row.evidence,
            "company_id": str(row.company_id) if row.company_id else None,
            "company_name": row.company_name,
            "related_id": row.related_id,
        }
