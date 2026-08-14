from __future__ import annotations

from autonomous_sales_agent.models.types import AutonomousSalesAgentInput, MeetingIntelligencePack


class MeetingIntelligenceEngine:
    def prepare(self, item: AutonomousSalesAgentInput) -> MeetingIntelligencePack:
        service = item.recommended_service or "Custom engagement"
        pains = item.pains[:8] or ["Operational inefficiency"]
        objections = item.objections_seen[:6] or ["Budget", "Timing", "Internal team"]
        return MeetingIntelligencePack(
            company_overview=(
                f"{item.company_name} ({item.industry or 'Unknown'}) — "
                f"intent {item.buying_intent_score}, grade {item.priority_grade or 'n/a'}, "
                f"probability {item.probability}."
            ),
            decision_makers=list(item.decision_makers)[:8],
            business_pains=pains,
            automation_opportunities=[
                f"Automate {pains[0]} with {service}",
                "Reduce manual handoffs across teams",
                "Instrument ROI metrics in first 90 days",
            ],
            likely_objections=objections,
            discovery_questions=[
                "What outcome would make this quarter a win?",
                "Where do manual processes create the most delay?",
                "Who else needs to approve a vendor decision?",
                "What have you already tried, and what failed?",
                "What is the decision window and success metric?",
            ],
            upsell_ideas=[f"Expand {service} into adjacent workflows", "Add analytics dashboard"],
            cross_sell_ideas=["Website conversion improvements", "Support automation", "MVP extension"],
            budget_hints=item.expected_budget or "$25k–$55k",
            technology_stack=list(item.technologies)[:12],
            recent_activity=list(item.recent_activity)[:10],
            competitive_landscape=list(item.vendors)[:8] or ["Incumbent tools unknown"],
            roi_talking_points=[
                "Status-quo cost of manual work",
                "90-day measurable outcome targets",
                "Phased delivery reduces risk",
            ],
            meeting_agenda=[
                "Intro + context (5m)",
                "Pain validation (10m)",
                "Solution sketch (10m)",
                "Objections + stakeholders (10m)",
                "Next steps / proposal path (5m)",
            ],
            success_checklist=[
                "Confirm buying committee",
                "Confirm decision window",
                "Align on primary offer",
                "Book proposal review",
            ],
            evidence=[f"service:{service}", f"dms:{len(item.decision_makers)}", f"pains:{len(pains)}"],
        )
