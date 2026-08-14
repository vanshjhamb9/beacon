from __future__ import annotations

from autonomous_sales_agent.models.types import (
    AutonomousSalesAgentInput,
    FollowUpRecommendation,
    FounderWorkItem,
    MorningBrief,
    NextBestAction,
)


class MorningBriefEngine:
    def generate(
        self,
        item: AutonomousSalesAgentInput,
        *,
        work_queue: list[FounderWorkItem],
        follow_up: FollowUpRecommendation,
        next_action: NextBestAction,
    ) -> MorningBrief:
        priorities = [w.summary for w in work_queue[:5]]
        if not priorities:
            priorities = [next_action.reason]
        follow_ups = []
        if follow_up.due:
            follow_ups.append(
                {
                    "company_name": item.company_name,
                    "channel": follow_up.channel.value,
                    "hint": follow_up.message_hint,
                    "days": follow_up.days_since_last_touch,
                }
            )
        attention = []
        if item.buying_intent_score >= 75 or item.priority_grade in {"A+", "A"}:
            attention.append(
                {
                    "company_name": item.company_name,
                    "reason": "High intent / priority account",
                    "intent": item.buying_intent_score,
                }
            )
        risk = []
        if item.days_since_last_touch >= 8 and item.email_sent and not item.reply_received:
            risk.append({"company_name": item.company_name, "reason": "Silent after outreach", "days": item.days_since_last_touch})
        if item.negotiation:
            risk.append({"company_name": item.company_name, "reason": "Active negotiation risk", "days": 0})
        forecast = float(item.pipeline_value or item.probability * 500.0)
        return MorningBrief(
            priorities=priorities[:6],
            expected_meetings=list(item.meetings_today)[:8],
            expected_replies=list(item.high_intent_replies)[:8],
            high_risk_deals=risk[:8],
            companies_requiring_attention=attention[:8],
            revenue_forecast=round(forecast, 2),
            follow_ups_due=follow_ups,
            evidence=[f"work_items:{len(work_queue)}", f"forecast:{forecast}", f"next:{next_action.action.value}"],
        )
