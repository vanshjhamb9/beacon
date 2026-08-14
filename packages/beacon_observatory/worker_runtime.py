"""Worker Runtime — tracks worker execution and health."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class WorkerInfo:
    """Worker runtime information."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.name: str = data.get("name", "unknown")
        self.status: str = data.get("status", "idle")
        self.started_at: datetime | None = data.get("started_at")
        self.last_heartbeat: datetime | None = data.get("last_heartbeat")
        self.tasks_completed: int = data.get("tasks_completed", 0)
        self.tasks_failed: int = data.get("tasks_failed", 0)
        self.avg_task_duration: float = data.get("avg_task_duration", 0.0)
        self.memory_usage_mb: float = data.get("memory_usage_mb", 0.0)
        self.cpu_usage_percent: float = data.get("cpu_usage_percent", 0.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "avg_task_duration": self.avg_task_duration,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
        }


class WorkerRuntime:
    """Tracks worker execution and health."""

    def __init__(self):
        self._workers: dict[str, WorkerInfo] = {}

    def register_worker(self, name: str) -> WorkerInfo:
        """Register a worker."""
        worker = WorkerInfo({"name": name, "status": "idle"})
        self._workers[name] = worker
        return worker

    def update_heartbeat(self, name: str):
        """Update worker heartbeat."""
        if name in self._workers:
            self._workers[name].last_heartbeat = datetime.now(timezone.utc)

    def record_task(self, name: str, duration: float, success: bool):
        """Record task completion."""
        if name in self._workers:
            worker = self._workers[name]
            if success:
                worker.tasks_completed += 1
            else:
                worker.tasks_failed += 1
            total = worker.tasks_completed + worker.tasks_failed
            worker.avg_task_duration = (
                (worker.avg_task_duration * (total - 1) + duration) / total
            )

    def get_worker(self, name: str) -> WorkerInfo | None:
        """Get worker info."""
        return self._workers.get(name)

    def get_all_workers(self) -> list[WorkerInfo]:
        """Get all workers."""
        return list(self._workers.values())

    def get_healthy_workers(self) -> list[WorkerInfo]:
        """Get healthy workers (heartbeat within 60s)."""
        now = datetime.now(timezone.utc)
        healthy = []
        for worker in self._workers.values():
            if worker.last_heartbeat:
                delta = (now - worker.last_heartbeat).total_seconds()
                if delta < 60:
                    healthy.append(worker)
        return healthy

    def get_statistics(self) -> dict[str, Any]:
        """Get worker statistics."""
        total = len(self._workers)
        healthy = len(self.get_healthy_workers())
        total_completed = sum(w.tasks_completed for w in self._workers.values())
        total_failed = sum(w.tasks_failed for w in self._workers.values())

        return {
            "total_workers": total,
            "healthy": healthy,
            "unhealthy": total - healthy,
            "total_completed": total_completed,
            "total_failed": total_failed,
        }
