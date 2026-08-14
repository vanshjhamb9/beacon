from __future__ import annotations

from account_journey.models.types import (
    AccountHealth,
    AccountHealthCategory,
    AccountJourneyInput,
    EngagementScores,
    FollowUpChannel,
    FollowUpPlan,
    MultiTouchPlan,
)


class FollowUpPlannerEngine:
    """Deterministic next action — founder approval mandatory before external sends."""

    def plan(
        self,
        item: AccountJourneyInput,
        *,
        engagement: EngagementScores,
        health: AccountHealth,
        multi_touch: MultiTouchPlan,
    ) -> FollowUpPlan:
        if item.won or item.lost:
            return FollowUpPlan(
                next_action="close_file",
                best_timing_hours=0,
                channel=FollowUpChannel.WAIT,
                message_type="archive_notes",
                urgency="low",
                reason="Terminal outcome — capture learning only",
                requires_founder_approval=False,
                evidence=["terminal:true"],
            )
        if item.meeting_scheduled:
            return FollowUpPlan(
                next_action="prepare_meeting",
                best_timing_hours=4.0,
                channel=FollowUpChannel.MEETING,
                message_type="meeting_prep",
                urgency="high",
                reason="Meeting scheduled — prepare pack",
                requires_founder_approval=True,
                evidence=["stage:meeting"],
            )
        if item.proposal_requested:
            return FollowUpPlan(
                next_action="prepare_proposal",
                best_timing_hours=8.0,
                channel=FollowUpChannel.PROPOSAL,
                message_type="proposal",
                urgency="high",
                reason="Proposal requested",
                requires_founder_approval=True,
                evidence=["stage:proposal"],
            )
        if health.category == AccountHealthCategory.CRITICAL or item.negotiation:
            return FollowUpPlan(
                next_action="founder_follow_up",
                best_timing_hours=2.0,
                channel=FollowUpChannel.FOUNDER_FOLLOW_UP,
                message_type="founder_touch",
                urgency="critical",
                reason="Critical / negotiation — founder must engage",
                requires_founder_approval=True,
                evidence=["health:critical", "founder_approval:required"],
            )
        if item.replied and not item.meeting_scheduled:
            return FollowUpPlan(
                next_action="book_meeting",
                best_timing_hours=max(2.0, 24.0 - engagement.intent_score * 0.2),
                channel=FollowUpChannel.MEETING,
                message_type="meeting_ask",
                urgency="high",
                reason="Reply received — convert to meeting",
                requires_founder_approval=True,
                evidence=["signal:reply"],
            )
        # Use adaptive multi-touch first actionable step
        for step in multi_touch.steps:
            if step.channel == FollowUpChannel.WAIT:
                continue
            urgency = "medium"
            if engagement.account_temperature >= 70:
                urgency = "high"
            if item.no_reply_days >= 8:
                urgency = "high"
            return FollowUpPlan(
                next_action=step.message_type,
                best_timing_hours=step.delay_hours,
                channel=step.channel,
                message_type=step.message_type,
                urgency=urgency,
                reason=step.reason,
                requires_founder_approval=True,
                evidence=list(step.evidence) + ["founder_approval:mandatory"],
            )
        return FollowUpPlan(
            next_action="wait",
            best_timing_hours=48.0,
            channel=FollowUpChannel.WAIT,
            message_type="monitor",
            urgency="low",
            reason="No outbound due — continue monitoring",
            requires_founder_approval=False,
            evidence=["action:wait"],
        )
