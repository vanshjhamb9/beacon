from __future__ import annotations

from account_journey.models.types import (
    AccountJourneyInput,
    EngagementScores,
    FollowUpChannel,
    MultiTouchPlan,
    OutreachIntelligence,
    TouchStep,
)


class MultiTouchOrchestrator:
    """Adaptive sequences — timing from engagement, never fixed intervals."""

    def plan(self, item: AccountJourneyInput, *, engagement: EngagementScores, outreach: OutreachIntelligence) -> MultiTouchPlan:
        temp = engagement.account_temperature
        # Adaptive delays: hotter = faster cadence
        base = max(6.0, 72.0 - (temp * 0.5) - (engagement.overall_engagement * 0.2))
        if outreach.ghosting:
            base = max(24.0, base * 1.4)
        if item.replied or item.meeting_scheduled:
            base = max(4.0, base * 0.35)

        steps: list[TouchStep] = []
        seq = 1
        if not item.emailed:
            steps.append(self._step(FollowUpChannel.EMAIL, seq, base * 0.0, "intro_email", "Start personalized email", temp))
            seq += 1
        if not item.whatsapp_sent:
            steps.append(self._step(FollowUpChannel.WHATSAPP, seq, base * 0.45, "whatsapp_nudge", "Adaptive WhatsApp after email", temp))
            seq += 1
        if item.emailed and not item.replied:
            steps.append(self._step(FollowUpChannel.FOLLOW_UP_EMAIL, seq, base, "value_follow_up", "Engagement-adapted follow-up", temp))
            seq += 1
            steps.append(self._step(FollowUpChannel.REMINDER, seq, base * 1.6, "soft_reminder", "Reminder based on silence", temp))
            seq += 1
        if item.replied or engagement.intent_score >= 60:
            steps.append(self._step(FollowUpChannel.MEETING, seq, max(2.0, base * 0.25), "meeting_ask", "Ask for discovery meeting", temp))
            seq += 1
        if item.meeting_scheduled or item.proposal_requested:
            steps.append(self._step(FollowUpChannel.PROPOSAL, seq, max(8.0, base * 0.5), "proposal_pack", "Prepare/send proposal", temp))
            seq += 1
        if item.negotiation or engagement.overall_engagement >= 75:
            steps.append(
                self._step(FollowUpChannel.FOUNDER_FOLLOW_UP, seq, max(2.0, base * 0.2), "founder_touch", "Founder-led close path", temp)
            )

        if not steps:
            steps.append(
                TouchStep(
                    channel=FollowUpChannel.WAIT,
                    sequence=1,
                    delay_hours=base,
                    message_type="monitor",
                    reason="No outbound needed — monitor engagement",
                    requires_founder_approval=False,
                    evidence=["adaptive:wait"],
                )
            )
        return MultiTouchPlan(
            steps=steps,
            adaptive=True,
            evidence=[f"base_delay_h:{round(base, 2)}", f"temp:{temp}", "fixed_intervals:false"],
        )

    def _step(self, channel: FollowUpChannel, seq: int, delay: float, msg: str, reason: str, temp: float) -> TouchStep:
        return TouchStep(
            channel=channel,
            sequence=seq,
            delay_hours=round(delay, 2),
            message_type=msg,
            reason=f"{reason} (temp={round(temp, 1)})",
            requires_founder_approval=channel != FollowUpChannel.WAIT,
            evidence=[f"channel:{channel.value}", f"delay_h:{round(delay, 2)}", "founder_approval:required"],
        )
