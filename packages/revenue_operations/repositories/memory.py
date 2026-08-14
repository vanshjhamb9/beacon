from __future__ import annotations

from revenue_operations.models.types import RevenueOperationsDecision


class InMemoryRocRepository:
    def __init__(self) -> None:
        self.snapshots: list[RevenueOperationsDecision] = []

    def append(self, decision: RevenueOperationsDecision) -> None:
        self.snapshots.append(decision)

    def latest(self) -> RevenueOperationsDecision | None:
        return self.snapshots[-1] if self.snapshots else None
