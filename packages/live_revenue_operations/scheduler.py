"""Scheduler — manages periodic tasks for revenue operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4


class ScheduledTask:
    """Single scheduled task."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.name: str = data.get("name", "unknown")
        self.frequency: str = data.get("frequency", "daily")
        self.enabled: bool = data.get("enabled", True)
        self.last_run: datetime | None = data.get("last_run")
        self.next_run: datetime | None = data.get("next_run")
        self.run_count: int = data.get("run_count", 0)
        self.callback: Callable | None = data.get("callback")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "frequency": self.frequency,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
        }


class Scheduler:
    """Manages periodic tasks."""

    def __init__(self):
        self._tasks: dict[str, ScheduledTask] = {}
        self._history: list[dict[str, Any]] = []

    def add_task(
        self,
        name: str,
        frequency: str,
        callback: Callable | None = None,
    ) -> ScheduledTask:
        """Add a scheduled task."""
        task = ScheduledTask({
            "name": name,
            "frequency": frequency,
            "callback": callback,
        })
        self._tasks[task.id] = task
        return task

    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def enable_task(self, task_id: str) -> bool:
        """Enable a task."""
        task = self._tasks.get(task_id)
        if task:
            task.enabled = True
            return True
        return False

    def disable_task(self, task_id: str) -> bool:
        """Disable a task."""
        task = self._tasks.get(task_id)
        if task:
            task.enabled = False
            return True
        return False

    def run_task(self, task_id: str) -> dict[str, Any]:
        """Run a task immediately."""
        task = self._tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}

        result = {
            "task_id": task_id,
            "task_name": task.name,
            "run_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
        }

        if task.callback:
            try:
                task.callback()
            except Exception as e:
                result["status"] = "failed"
                result["error"] = str(e)

        task.last_run = datetime.now(timezone.utc)
        task.run_count += 1

        self._history.append(result)
        return result

    def get_task(self, task_id: str) -> ScheduledTask | None:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[ScheduledTask]:
        """Get all tasks."""
        return list(self._tasks.values())

    def get_enabled_tasks(self) -> list[ScheduledTask]:
        """Get enabled tasks."""
        return [t for t in self._tasks.values() if t.enabled]

    def get_history(self) -> list[dict[str, Any]]:
        """Get task run history."""
        return list(self._history)

    def get_statistics(self) -> dict[str, Any]:
        """Get scheduler statistics."""
        total = len(self._tasks)
        enabled = sum(1 for t in self._tasks.values() if t.enabled)
        total_runs = sum(t.run_count for t in self._tasks.values())

        return {
            "total_tasks": total,
            "enabled": enabled,
            "disabled": total - enabled,
            "total_runs": total_runs,
        }
