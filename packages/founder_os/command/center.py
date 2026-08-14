from __future__ import annotations

from founder_os.models.types import CommandCenterState, FounderOsInput, ProposalQueueItem, RevenueTask


class CommandCenterBuilder:
    """Single-screen actionable state for the founder."""

    def build(
        self,
        data: FounderOsInput,
        *,
        tasks: list[RevenueTask],
        proposals: list[ProposalQueueItem],
    ) -> CommandCenterState:
        return CommandCenterState(
            revenue_pipeline=round(data.estimated_pipeline, 2),
            expected_revenue=round(data.expected_revenue, 2),
            meetings=data.meetings_today,
            campaign_queue=data.campaigns_waiting_approval,
            inbox=data.replies_waiting,
            daily_tasks=tasks[:25],
            proposal_queue=proposals[:25],
            work_queue=list(data.work_queue_items)[:25],
            todays_top_companies=list(data.top_companies)[:10],
            follow_up_queue=list(data.follow_ups)[:25],
        )
