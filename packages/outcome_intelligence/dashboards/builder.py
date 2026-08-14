from __future__ import annotations

from typing import Any

from outcome_intelligence.models.types import OutcomeAnalytics, OutcomeDashboard
from outcome_intelligence.pipelines.outcome_pipeline import OutcomeIntelligencePipeline


class OutcomeDashboardBuilder:
    """Pure dashboard projection helpers for Outcome Intelligence surfaces."""

    def __init__(self, pipeline: OutcomeIntelligencePipeline | None = None) -> None:
        self.pipeline = pipeline or OutcomeIntelligencePipeline()

    def sales_funnel(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        dashboard = self.pipeline.build_dashboard(records)
        return [item.model_dump() for item in dashboard.funnel]

    def revenue_dashboard(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        dashboard = self.pipeline.build_dashboard(records)
        return {
            "revenue": dashboard.revenue.model_dump(),
            "by_collector": [item.model_dump() for item in dashboard.revenue_by_collector],
            "by_industry": [item.model_dump() for item in dashboard.revenue_by_industry],
            "by_service": [item.model_dump() for item in dashboard.revenue_by_service],
            "by_persona": [item.model_dump() for item in dashboard.revenue_by_persona],
            "by_technology": [item.model_dump() for item in dashboard.revenue_by_technology],
            "roi": dashboard.roi,
        }

    def collector_accuracy(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [item.model_dump() for item in self.pipeline.build_dashboard(records).collector_accuracy]

    def service_accuracy(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [item.model_dump() for item in self.pipeline.build_dashboard(records).service_accuracy]

    def industry_accuracy(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [item.model_dump() for item in self.pipeline.build_dashboard(records).industry_accuracy]

    def prediction_accuracy(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [item.model_dump() for item in self.pipeline.build_dashboard(records).prediction_accuracy]

    def roi(self, records: list[dict[str, Any]]) -> dict[str, float | int]:
        return self.pipeline.build_dashboard(records).roi

    def full(self, records: list[dict[str, Any]]) -> OutcomeDashboard:
        return self.pipeline.build_dashboard(records)

    def analytics(self, records: list[dict[str, Any]]) -> OutcomeAnalytics:
        return self.pipeline.build_analytics(records)
