from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from runtime_ops.models.types import CeleryRuntimeStatus


class CeleryRuntimeProbe:
    """Probe Celery control + broker depth without redesigning workers."""

    def probe(
        self,
        *,
        broker_ok: bool,
        queue_depth: int = 0,
        inspect_payload: dict[str, Any] | None = None,
        beat_schedule_count: int = 0,
        last_collector_run_at: datetime | None = None,
        heartbeat_key_ttl_ok: bool = False,
    ) -> CeleryRuntimeStatus:
        inspect_payload = inspect_payload or {}
        ping = inspect_payload.get("ping") or {}
        stats = inspect_payload.get("stats") or {}
        active = inspect_payload.get("active") or {}
        scheduled = inspect_payload.get("scheduled") or {}
        registered = inspect_payload.get("registered") or {}

        worker_online = bool(ping) or bool(stats) or bool(registered)
        active_tasks = sum(len(v or []) for v in active.values()) if isinstance(active, dict) else 0
        scheduled_tasks = sum(len(v or []) for v in scheduled.values()) if isinstance(scheduled, dict) else 0
        registered_count = 0
        if isinstance(registered, dict):
            for tasks in registered.values():
                registered_count += len(tasks or [])

        memory_mb = None
        cpu = None
        if isinstance(stats, dict) and stats:
            first = next(iter(stats.values()))
            if isinstance(first, dict):
                mem = first.get("rusage") or {}
                if isinstance(mem, dict) and mem.get("maxrss") is not None:
                    # Linux maxrss is KB; Windows varies — store raw converted best-effort.
                    memory_mb = round(float(mem["maxrss"]) / 1024.0, 2)
                cpu = first.get("pool", {}).get("writes") if isinstance(first.get("pool"), dict) else None

        beat_online = heartbeat_key_ttl_ok
        if not beat_online and last_collector_run_at is not None:
            age = datetime.now(UTC) - (
                last_collector_run_at if last_collector_run_at.tzinfo else last_collector_run_at.replace(tzinfo=UTC)
            )
            beat_online = age.total_seconds() <= 900

        # On Windows, inspect.ping can be empty while worker is processing; recent collector
        # activity is durable evidence that a worker consumed Beat-scheduled tasks.
        if not worker_online and last_collector_run_at is not None:
            age = datetime.now(UTC) - (
                last_collector_run_at if last_collector_run_at.tzinfo else last_collector_run_at.replace(tzinfo=UTC)
            )
            if age.total_seconds() <= 900:
                worker_online = True

        evidence = [
            f"broker_ok:{broker_ok}",
            f"worker_online:{worker_online}",
            f"beat_online:{beat_online}",
            f"queue_depth:{queue_depth}",
            f"beat_schedule_count:{beat_schedule_count}",
            f"registered_tasks:{registered_count}",
            f"inspect_ping_workers:{len(ping) if isinstance(ping, dict) else 0}",
            f"inspect_registered_workers:{len(registered) if isinstance(registered, dict) else 0}",
        ]
        return CeleryRuntimeStatus(
            worker_online=worker_online,
            beat_online=beat_online,
            broker_ok=broker_ok,
            active_tasks=active_tasks,
            scheduled_tasks=scheduled_tasks or beat_schedule_count,
            registered_task_count=registered_count,
            queue_depth=queue_depth,
            worker_memory_mb=memory_mb,
            worker_cpu_percent=float(cpu) if isinstance(cpu, (int, float)) else None,
            last_heartbeat_at=last_collector_run_at,
            evidence=evidence,
        )
