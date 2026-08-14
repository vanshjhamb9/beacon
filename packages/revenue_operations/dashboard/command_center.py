from __future__ import annotations

from revenue_operations.models.types import (
    CommandCenterView,
    ControlTowerMetrics,
    FounderAssistantBrief,
    LearningLabReport,
    RevenueForecastPack,
    RevenueOperationsInput,
)


class CommandCenterEngine:
    """Above-the-fold founder command center — no unnecessary widgets."""

    def build(
        self,
        item: RevenueOperationsInput,
        *,
        tower: ControlTowerMetrics,
        forecast: RevenueForecastPack,
        assistant: FounderAssistantBrief,
        learning: LearningLabReport,
    ) -> CommandCenterView:
        score = max(
            0.0,
            min(
                100.0,
                (forecast.pipeline_health * 0.45)
                + (forecast.confidence_score * 0.25)
                + (min(100.0, tower.expected_revenue / 1000.0) * 0.3),
            ),
        )
        queue = []
        for m in assistant.meetings[:3]:
            queue.append({"kind": "meeting", **m})
        for r in assistant.replies[:3]:
            queue.append({"kind": "reply", **r})
        for d in assistant.deals_requiring_attention[:3]:
            queue.append({"kind": "attention", **d})
        recs = [
            {
                "id": r.recommendation_id,
                "title": r.title,
                "detail": r.detail,
                "status": r.status.value,
                "requires_approval": True,
            }
            for r in learning.recommendations[:5]
        ]
        return CommandCenterView(
            greeting=assistant.greeting,
            revenue_score=round(score, 2),
            todays_mission=assistant.todays_mission,
            high_priority_queue=queue[:8],
            meetings=list(assistant.meetings)[:6],
            replies=list(assistant.replies)[:6],
            campaign_health={
                "campaigns_running": tower.campaigns_running,
                "top_campaign": tower.top_campaign,
                "status": "healthy" if tower.campaigns_running > 0 else "idle",
            },
            pipeline={
                "value": tower.pipeline_value,
                "expected_revenue": tower.expected_revenue,
                "deals_at_risk": tower.deals_at_risk,
                "proposals_pending": tower.proposals_pending,
                "negotiations": tower.negotiations,
            },
            forecast={
                "this_week": forecast.this_week.amount,
                "this_month": forecast.this_month.amount,
                "confidence": forecast.confidence_score,
                "pipeline_health": forecast.pipeline_health,
            },
            recommendations=recs,
            evidence=["command_center:v1", "above_the_fold:true", f"score:{score}"],
        )
