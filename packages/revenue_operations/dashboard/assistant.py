from __future__ import annotations

from revenue_operations.models.types import (
    ControlTowerMetrics,
    FounderAssistantBrief,
    RevenueForecastPack,
    RevenueOperationsInput,
)


class FounderAssistantV2Engine:
    """Actionable morning intelligence — no chat."""

    def generate(
        self,
        item: RevenueOperationsInput,
        *,
        tower: ControlTowerMetrics,
        forecast: RevenueForecastPack,
    ) -> FounderAssistantBrief:
        hour = (item.now.hour if item.now else 9)
        greeting = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 18 else "Good Evening")
        greeting = f"{greeting}, {item.founder_name}"
        hot = sorted(
            [o for o in item.opportunities if not o.lost and not o.won],
            key=lambda o: (-o.probability, -o.pipeline_value),
        )[:5]
        attention = [
            {"company_name": o.company_name, "reason": self._attention_reason(o), "probability": o.probability}
            for o in item.opportunities
            if o.at_risk or o.proposal_pending or o.negotiation or (o.reply_waiting and o.days_in_stage >= 2)
        ][:8]
        replies = [
            {"company_name": o.company_name, "probability": o.probability, "summary": "Reply waiting"}
            for o in item.opportunities
            if o.reply_waiting
        ][:10]
        follow_ups = [
            {"company_name": o.company_name, "days_in_stage": o.days_in_stage, "summary": "Follow-up due"}
            for o in item.opportunities
            if o.days_in_stage >= 2 and not o.reply_waiting and not o.won and not o.lost
        ][:10]
        meetings = [
            {"company_name": o.company_name, "summary": "Meeting today", "probability": o.probability}
            for o in item.opportunities
            if o.meeting_today
        ][:10]
        priorities = []
        if tower.meetings_today:
            priorities.append(f"Attend {tower.meetings_today} meeting(s)")
        if tower.replies_waiting:
            priorities.append(f"Clear {tower.replies_waiting} waiting reply(ies)")
        if tower.proposals_pending:
            priorities.append(f"Advance {tower.proposals_pending} proposal(s)")
        if tower.negotiations:
            priorities.append(f"Push {tower.negotiations} negotiation(s)")
        if not priorities:
            priorities.append("Review pipeline and approve ready campaigns")
        mission = priorities[0]
        summary = (
            f"Pipeline {tower.pipeline_value:,.0f} · Expected {tower.expected_revenue:,.0f} · "
            f"{tower.meetings_today} meetings · {tower.replies_waiting} replies · "
            f"{tower.deals_at_risk} at risk."
        )
        return FounderAssistantBrief(
            greeting=greeting,
            executive_summary=summary,
            todays_mission=mission,
            top_priorities=priorities[:6],
            highest_probability_deals=[
                {
                    "company_name": o.company_name,
                    "probability": o.probability,
                    "pipeline_value": o.pipeline_value,
                    "service": o.service,
                }
                for o in hot
            ],
            deals_requiring_attention=attention,
            replies=replies,
            follow_ups=follow_ups,
            meetings=meetings,
            revenue_target=float(item.revenue_target_week),
            expected_revenue=float(forecast.this_week.amount),
            evidence=["assistant:v2", "no_chat:true", f"forecast_week:{forecast.this_week.amount}"],
        )

    def _attention_reason(self, o) -> str:
        if o.at_risk:
            return "At risk"
        if o.negotiation:
            return "Negotiation"
        if o.proposal_pending:
            return "Proposal pending"
        if o.reply_waiting:
            return "Reply overdue"
        return "Needs attention"
