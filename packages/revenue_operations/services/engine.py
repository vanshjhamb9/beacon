from __future__ import annotations

from revenue_operations.alerts.engine import SmartAlertEngine
from revenue_operations.memory.engine import AgencyMemoryEngine
from revenue_operations.models.types import (
    AlertLifecycle,
    MemoryRecord,
    RevenueOperationsDecision,
    RevenueOperationsInput,
)
from revenue_operations.pipelines.roc_pipeline import RevenueOperationsPipeline


class RevenueOperationsService:
    def __init__(self, pipeline: RevenueOperationsPipeline | None = None) -> None:
        self.pipeline = pipeline or RevenueOperationsPipeline()
        self.alerts = SmartAlertEngine()
        self.memory = AgencyMemoryEngine()

    def evaluate(self, data: RevenueOperationsInput) -> RevenueOperationsDecision:
        return self.pipeline.process(data)

    def evaluate_many(self, items: list[RevenueOperationsInput]) -> list[RevenueOperationsDecision]:
        return [self.evaluate(item) for item in items]

    def transition_alert(self, current: AlertLifecycle, target: AlertLifecycle) -> AlertLifecycle:
        return self.alerts.transition(current, target)

    def search_memory(self, records: list[MemoryRecord], query: str) -> list[MemoryRecord]:
        return self.memory.search(records, query)
