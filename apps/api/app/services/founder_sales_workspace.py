"""Founder Sales Workspace (FSW) service — Sprint 38."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.models.founder_sales_workspace import LeadStage
from app.repositories.founder_sales_workspace import FSWRepository


GARBAGE_REASONS = [
    "ai_company",
    "competitor",
    "duplicate",
    "closed",
    "no_buying_signal",
    "too_old",
    "wrong_industry",
    "wrong_geography",
    "already_customer",
    "spam",
    "other",
]

VALID_STAGES = [
    "revenue_ready",
    "contacted",
    "replied",
    "meeting",
    "proposal",
    "negotiation",
    "won",
    "lost",
    "archived",
    "garbage",
]

VALID_PRIORITIES = ["low", "medium", "high", "urgent"]


class FSWService:
    def __init__(self, repository: FSWRepository) -> None:
        self.repository = repository

    # ── Lead CRUD ──

    async def list_leads(self, **filters: Any) -> list[LeadStage]:
        return list(await self.repository.list_leads(**filters))

    async def get_lead(self, lead_id: uuid.UUID) -> LeadStage | None:
        return await self.repository.get_lead(lead_id)

    async def create_lead(self, data: dict[str, Any]) -> LeadStage:
        lead = await self.repository.create_lead(data)
        await self._timeline(lead.id, "stage_change", f"Lead created in {lead.stage}", actor=data.get("owner"))
        return lead

    async def update_lead(self, lead_id: uuid.UUID, data: dict[str, Any]) -> LeadStage | None:
        lead = await self.repository.update_lead(lead_id, data)
        if lead:
            await self._timeline(lead_id, "stage_change", f"Lead updated", actor=data.get("owner"))
        return lead

    # ── Stage Movement ──

    async def move_lead(self, lead_id: uuid.UUID, new_stage: str, sort_order: int | None = None, actor: str | None = None) -> LeadStage | None:
        lead = await self.repository.get_lead(lead_id)
        if not lead:
            return None
        old_stage = lead.stage
        lead = await self.repository.move_lead(lead_id, new_stage, sort_order)
        if lead:
            await self._timeline(lead_id, "stage_change", f"Moved from {old_stage} to {new_stage}", actor=actor, metadata={"old_stage": old_stage, "new_stage": new_stage})
            await self._record_action(lead_id, "move", actor=actor, details={"from": old_stage, "to": new_stage})
        return lead

    async def bulk_move(self, lead_ids: list[uuid.UUID], new_stage: str, actor: str | None = None) -> int:
        count = await self.repository.bulk_move(lead_ids, new_stage)
        for lid in lead_ids:
            await self._timeline(lid, "stage_change", f"Bulk moved to {new_stage}", actor=actor)
        return count

    # ── Garbage ──

    async def send_to_garbage(self, lead_id: uuid.UUID, reason: str, note: str | None = None, actor: str | None = None) -> LeadStage | None:
        if reason not in GARBAGE_REASONS:
            raise ValueError(f"Invalid garbage reason: {reason}")
        lead = await self.repository.get_lead(lead_id)
        if not lead:
            return None
        old_stage = lead.stage
        lead = await self.repository.update_lead(lead_id, {
            "stage": "garbage",
            "garbage_reason": reason,
            "garbage_note": note,
            "garbage_at": datetime.now(UTC),
        })
        if lead:
            await self._timeline(lead_id, "garbage", f"Sent to garbage: {reason}", actor=actor, metadata={"reason": reason, "note": note, "from_stage": old_stage})
        return lead

    async def restore_from_garbage(self, lead_id: uuid.UUID, actor: str | None = None) -> LeadStage | None:
        lead = await self.repository.get_lead(lead_id)
        if not lead or lead.stage != "garbage":
            return None
        lead = await self.repository.update_lead(lead_id, {
            "stage": "revenue_ready",
            "garbage_reason": None,
            "garbage_note": None,
            "garbage_at": None,
        })
        if lead:
            await self._timeline(lead_id, "restored", "Restored from garbage", actor=actor)
        return lead

    # ── Archive ──

    async def archive_lead(self, lead_id: uuid.UUID, actor: str | None = None) -> LeadStage | None:
        lead = await self.repository.move_lead(lead_id, "archived")
        if lead:
            await self._timeline(lead_id, "stage_change", "Archived", actor=actor)
        return lead

    # ── Snooze ──

    async def snooze_lead(self, lead_id: uuid.UUID, until: datetime, reason: str | None = None, actor: str | None = None) -> LeadStage | None:
        lead = await self.repository.update_lead(lead_id, {
            "snoozed_until": until,
            "snooze_reason": reason,
        })
        if lead:
            await self._timeline(lead_id, "stage_change", f"Snoozed until {until.isoformat()}", actor=actor, metadata={"until": until.isoformat(), "reason": reason})
        return lead

    # ── Manual Status ──

    async def set_manual_status(self, lead_id: uuid.UUID, status: str | None, actor: str | None = None) -> LeadStage | None:
        lead = await self.repository.update_lead(lead_id, {"manual_status": status})
        if lead:
            await self._timeline(lead_id, "status_change", f"Status set to {status}", actor=actor)
        return lead

    # ── Assignment ──

    async def assign_lead(self, lead_id: uuid.UUID, owner: str, actor: str | None = None) -> LeadStage | None:
        lead = await self.repository.update_lead(lead_id, {"owner": owner, "assigned_by": actor})
        if lead:
            await self._timeline(lead_id, "assigned", f"Assigned to {owner}", actor=actor)
        return lead

    # ── Notes ──

    async def add_note(self, lead_id: uuid.UUID, content: str, author: str | None = None) -> Any:
        note = await self.repository.add_note({
            "lead_stage_id": lead_id,
            "content": content,
            "author": author,
        })
        await self._timeline(lead_id, "note_added", f"Note added by {author or 'system'}", actor=author)
        return note

    async def list_notes(self, lead_id: uuid.UUID) -> list[Any]:
        return list(await self.repository.list_notes(lead_id))

    async def delete_note(self, note_id: uuid.UUID) -> bool:
        return await self.repository.delete_note(note_id)

    # ── Tasks ──

    async def add_task(self, lead_id: uuid.UUID, title: str, description: str | None = None, due_date: datetime | None = None, priority: str = "medium", owner: str | None = None) -> Any:
        if priority not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority: {priority}")
        task = await self.repository.add_task({
            "lead_stage_id": lead_id,
            "title": title,
            "description": description,
            "due_date": due_date,
            "priority": priority,
            "owner": owner,
        })
        await self._timeline(lead_id, "task_created", f"Task created: {title}", actor=owner)
        return task

    async def list_tasks(self, lead_id: uuid.UUID, include_completed: bool = True) -> list[Any]:
        return list(await self.repository.list_tasks(lead_id, include_completed=include_completed))

    async def complete_task(self, task_id: uuid.UUID, actor: str | None = None) -> Any:
        task = await self.repository.complete_task(task_id)
        if task:
            await self._timeline(task.lead_stage_id, "task_completed", f"Task completed: {task.title}", actor=actor)
        return task

    async def delete_task(self, task_id: uuid.UUID) -> bool:
        return await self.repository.delete_task(task_id)

    # ── Timeline ──

    async def list_timeline(self, lead_id: uuid.UUID) -> list[Any]:
        return list(await self.repository.list_timeline(lead_id))

    # ── Bulk Operations ──

    async def bulk_delete(self, lead_ids: list[uuid.UUID], actor: str | None = None) -> int:
        count = await self.repository.bulk_delete(lead_ids)
        for lid in lead_ids:
            await self._timeline(lid, "stage_change", "Deleted (soft)", actor=actor)
        return count

    # ── Stats ──

    async def get_stage_counts(self) -> dict[str, int]:
        return await self.repository.get_stage_counts()

    async def get_filter_values(self) -> dict[str, list[str]]:
        return {
            "industry": await self.repository.get_unique_values("industry"),
            "country": await self.repository.get_unique_values("country"),
            "service_match": await self.repository.get_unique_values("service_match"),
            "source_connector": await self.repository.get_unique_values("source_connector"),
            "trigger": await self.repository.get_unique_values("trigger"),
            "owner": await self.repository.get_unique_values("owner"),
        }

    # ── Internal ──

    async def _timeline(self, lead_id: uuid.UUID, event_type: str, title: str, actor: str | None = None, description: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        await self.repository.add_timeline_event({
            "lead_stage_id": lead_id,
            "event_type": event_type,
            "title": title,
            "description": description,
            "actor": actor,
            "metadata_json": metadata or {},
        })

    async def _record_action(self, lead_id: uuid.UUID, action_type: str, actor: str | None = None, details: dict[str, Any] | None = None) -> None:
        await self.repository.record_action({
            "lead_stage_id": lead_id,
            "action_type": action_type,
            "performed_by": actor,
            "details": details or {},
        })
