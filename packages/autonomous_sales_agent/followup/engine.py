from __future__ import annotations

from autonomous_sales_agent.models.types import (
    AutonomousSalesAgentInput,
    FollowUpChannel,
    FollowUpRecommendation,
)


class FollowUpIntelligenceEngine:
    """Deterministic follow-up cadence — fully configurable via FollowUpConfig."""

    def recommend(self, item: AutonomousSalesAgentInput) -> FollowUpRecommendation:
        cfg = item.follow_up_config
        days = max(0, int(item.days_since_last_touch))
        if item.reply_received or item.meeting_booked or item.won or item.lost:
            return FollowUpRecommendation(
                channel=FollowUpChannel.NONE,
                days_since_last_touch=days,
                message_hint="Active conversation — no automated follow-up.",
                due=False,
                evidence=[f"days:{days}", "active:true"],
            )
        if not item.email_sent and not item.whatsapp_sent:
            return FollowUpRecommendation(
                channel=FollowUpChannel.NONE,
                days_since_last_touch=days,
                message_hint="Outreach not started.",
                due=False,
                evidence=[f"days:{days}", "outreach:false"],
            )
        if days >= cfg.archive_days:
            return FollowUpRecommendation(
                channel=FollowUpChannel.ARCHIVE,
                days_since_last_touch=days,
                message_hint="Archive — no engagement after final cadence.",
                due=True,
                evidence=[f"days:{days}", f"archive_days:{cfg.archive_days}"],
            )
        if days >= cfg.final_email_days:
            return FollowUpRecommendation(
                channel=FollowUpChannel.FINAL_EMAIL,
                days_since_last_touch=days,
                message_hint="Send a polite final email and leave the door open.",
                due=True,
                evidence=[f"days:{days}", f"final_email_days:{cfg.final_email_days}"],
            )
        if days >= cfg.whatsapp_days:
            return FollowUpRecommendation(
                channel=FollowUpChannel.WHATSAPP,
                days_since_last_touch=days,
                message_hint="Send a short WhatsApp nudge with Calendly.",
                due=True,
                evidence=[f"days:{days}", f"whatsapp_days:{cfg.whatsapp_days}"],
            )
        if days >= cfg.value_email_days:
            return FollowUpRecommendation(
                channel=FollowUpChannel.VALUE_EMAIL,
                days_since_last_touch=days,
                message_hint="Send a value email with a relevant case study.",
                due=True,
                evidence=[f"days:{days}", f"value_email_days:{cfg.value_email_days}"],
            )
        if days >= cfg.follow_up_days:
            return FollowUpRecommendation(
                channel=FollowUpChannel.EMAIL_FOLLOW_UP,
                days_since_last_touch=days,
                message_hint="Send a short follow-up referencing the original pain.",
                due=True,
                evidence=[f"days:{days}", f"follow_up_days:{cfg.follow_up_days}"],
            )
        return FollowUpRecommendation(
            channel=FollowUpChannel.NONE,
            days_since_last_touch=days,
            message_hint="Wait — cadence not due yet.",
            due=False,
            evidence=[f"days:{days}", "wait:true"],
        )
