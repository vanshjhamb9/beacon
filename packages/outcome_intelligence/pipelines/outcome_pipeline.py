from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from outcome_intelligence.analytics.engine import OutcomeAnalyticsEngine
from outcome_intelligence.evaluation.engine import OutcomeEvaluationEngine
from outcome_intelligence.learning.engine import OutcomeLearningEngine
from outcome_intelligence.models.types import OutcomeAnalytics, OutcomeDashboard


class OutcomeIntelligencePipeline:
    def __init__(
        self,
        *,
        analytics: OutcomeAnalyticsEngine | None = None,
        evaluation: OutcomeEvaluationEngine | None = None,
        learning: OutcomeLearningEngine | None = None,
    ) -> None:
        self.analytics = analytics or OutcomeAnalyticsEngine()
        self.evaluation = evaluation or OutcomeEvaluationEngine()
        self.learning = learning or OutcomeLearningEngine()

    def build_dashboard(self, records: list[dict[str, Any]]) -> OutcomeDashboard:
        stages = [str(row.get("lifecycle_stage") or "new") for row in records]
        rates = self.analytics.rates(records)
        revenue = self.analytics.revenue(records)
        funnel = self.analytics.funnel(stages)
        by_collector = self.analytics.revenue_by_dimension(records, "collector")
        by_industry = self.analytics.revenue_by_dimension(records, "industry")
        by_service = self.analytics.revenue_by_dimension(records, "recommended_service")
        by_persona = self.analytics.revenue_by_dimension(records, "buyer_persona")
        by_technology = self.analytics.revenue_by_dimension(records, "technology")

        prediction = self.evaluation.opportunity_score_accuracy(records)
        revenue_rec_acc = self.evaluation.revenue_recommendation_accuracy(records)
        service_acc = self.evaluation.dimension_accuracy(records, category="service", dimension="recommended_service")
        collector_acc = self.evaluation.dimension_accuracy(records, category="collector", dimension="collector")
        persona_acc = self.evaluation.dimension_accuracy(records, category="persona", dimension="buyer_persona")
        industry_acc = self.evaluation.dimension_accuracy(records, category="industry", dimension="industry")
        technology_acc = self.evaluation.technology_accuracy(records)
        dm_acc = self.evaluation.decision_maker_accuracy(records)
        lead_acc = self.evaluation.lead_quality_accuracy(records)

        recommendations = self.learning.recommendations(
            rates=rates,
            collector_accuracy=collector_acc,
            service_accuracy=service_acc,
            industry_accuracy=industry_acc,
            persona_accuracy=persona_acc + dm_acc,
            prediction_accuracy=prediction + lead_acc + revenue_rec_acc,
            revenue_by_service=by_service,
        )

        invested = float(len(records))  # proxy unit cost for ROI absent spend telemetry
        roi_ratio = (revenue.total_revenue / invested) if invested else 0.0
        return OutcomeDashboard(
            generated_at=datetime.now(UTC),
            funnel=funnel,
            rates=rates,
            revenue=revenue,
            revenue_by_collector=by_collector,
            revenue_by_industry=by_industry,
            revenue_by_service=by_service,
            revenue_by_persona=by_persona,
            revenue_by_technology=by_technology,
            prediction_accuracy=prediction + lead_acc + dm_acc + revenue_rec_acc + technology_acc,
            service_accuracy=service_acc,
            collector_accuracy=collector_acc,
            persona_accuracy=persona_acc,
            industry_accuracy=industry_acc,
            roi={
                "total_revenue": revenue.total_revenue,
                "won_deals": revenue.won_deals,
                "average_deal_size": revenue.average_deal_size,
                "opportunities_tracked": len(records),
                "revenue_per_opportunity": round(revenue.total_revenue / max(len(records), 1), 4),
                "roi_index": round(roi_ratio, 4),
            },
            learning_recommendations=recommendations,
        )

    def build_analytics(self, records: list[dict[str, Any]]) -> OutcomeAnalytics:
        dashboard = self.build_dashboard(records)
        accuracy_values = [
            item.accuracy_score
            for item in (
                dashboard.prediction_accuracy
                + dashboard.service_accuracy
                + dashboard.collector_accuracy
                + dashboard.persona_accuracy
                + dashboard.industry_accuracy
            )
        ]
        return OutcomeAnalytics(
            generated_at=dashboard.generated_at,
            rates=dashboard.rates,
            revenue=dashboard.revenue,
            funnel=dashboard.funnel,
            accuracy_summary={
                "metrics": len(accuracy_values),
                "average_accuracy": round(sum(accuracy_values) / len(accuracy_values), 4) if accuracy_values else 0.0,
            },
            top_services=dashboard.revenue_by_service[:8],
            top_collectors=dashboard.revenue_by_collector[:8],
            top_industries=dashboard.revenue_by_industry[:8],
            learning_recommendations=dashboard.learning_recommendations,
        )
