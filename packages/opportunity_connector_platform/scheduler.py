"""Deterministic connector scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    attempts: int = 3
    backoff_seconds: int = 60


@dataclass(frozen=True, slots=True)
class ScheduleDeclaration:
    connector_id: str
    interval: int
    priority: str
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    max_concurrency: int = 1
    timeout: int = 30
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)


class ConnectorScheduler:
    """Deterministic scheduler — declares jobs, orders by priority."""

    def declare(
        self,
        *,
        connector_id: str,
        interval: int,
        priority: str,
        dependencies: tuple[str, ...] = (),
        max_concurrency: int = 1,
        timeout: int = 30,
        retry_policy: RetryPolicy | None = None,
    ) -> ScheduleDeclaration:
        return ScheduleDeclaration(
            connector_id=connector_id,
            interval=interval,
            priority=priority,
            dependencies=dependencies,
            max_concurrency=max_concurrency,
            timeout=timeout,
            retry_policy=retry_policy or RetryPolicy(),
        )

    def order(self, declarations: list[ScheduleDeclaration]) -> list[ScheduleDeclaration]:
        priority = {"high": 0, "normal": 1, "low": 2}
        return sorted(declarations, key=lambda item: (priority.get(item.priority, 1), item.interval))

    def ready_jobs(
        self,
        declarations: list[ScheduleDeclaration],
        completed: set[str],
    ) -> list[ScheduleDeclaration]:
        ready = []
        for decl in self.order(declarations):
            deps_met = all(d in completed for d in decl.dependencies)
            if deps_met:
                ready.append(decl)
        return ready

    def blocked_jobs(
        self,
        declarations: list[ScheduleDeclaration],
        completed: set[str],
    ) -> list[ScheduleDeclaration]:
        blocked = []
        for decl in self.order(declarations):
            deps_met = all(d in completed for d in decl.dependencies)
            if not deps_met:
                blocked.append(decl)
        return blocked

    def schedule_graph(self, declarations: list[ScheduleDeclaration]) -> list[list[ScheduleDeclaration]]:
        levels: list[list[ScheduleDeclaration]] = []
        completed: set[str] = set()
        remaining = list(declarations)
        while remaining:
            ready = self.ready_jobs(remaining, completed)
            if not ready:
                break
            levels.append(ready)
            for job in ready:
                completed.add(job.connector_id)
            remaining = [j for j in remaining if j.connector_id not in completed]
        return levels
