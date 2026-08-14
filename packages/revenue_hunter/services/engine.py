from __future__ import annotations

from revenue_hunter.dashboard.founder import FounderDashboardBuilder
from revenue_hunter.filters.taxonomy import default_filter_criteria
from revenue_hunter.models.types import FilterCriteria, FounderDashboard, RevenueDossier, RevenueHunterDecision, RevenueHunterInput
from revenue_hunter.pipelines.revenue_hunter_pipeline import RevenueHunterPipeline
from revenue_hunter.queue.work_queue import WorkQueueBuilder


class RevenueHunterService:
    """Facade for pipeline + founder dashboard + work queue."""

    def __init__(
        self,
        *,
        criteria: FilterCriteria | None = None,
        pipeline: RevenueHunterPipeline | None = None,
    ) -> None:
        self.criteria = criteria or default_filter_criteria()
        self.pipeline = pipeline or RevenueHunterPipeline(criteria=self.criteria)
        self.dashboard_builder = FounderDashboardBuilder()
        self.queue_builder = WorkQueueBuilder()

    def evaluate(self, item: RevenueHunterInput) -> RevenueHunterDecision:
        return self.pipeline.process(item)

    def build_dashboard(self, dossiers: list[RevenueDossier], **kwargs: int) -> FounderDashboard:
        return self.dashboard_builder.build(dossiers, **kwargs)
