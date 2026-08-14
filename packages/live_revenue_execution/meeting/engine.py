from __future__ import annotations

from live_revenue_execution.models.types import LREInput, MeetingAutomationPack


class MeetingAutomationEngine:
    """Compose meeting packs from Sales Intelligence + Revenue Hunter shaped inputs."""

    def build(self, item: LREInput) -> MeetingAutomationPack:
        questions = [
            "What outcome would make this quarter a win?",
            "Where do manual processes create the most delay?",
            "Who else needs to approve a vendor decision?",
            "What have you already tried?",
            "What is the decision window?",
        ]
        follow_ups = [
            "Send meeting summary within 24h",
            "Create proposal task",
            "Schedule reminder for next commercial step",
            "Update company timeline",
        ]
        timeline = [
            "Pre-meeting: review dossier + buying intent",
            "Meeting: discovery + offer alignment",
            "Post-meeting: summary + proposal path",
        ]
        return MeetingAutomationPack(
            company_id=item.company_id,
            company_name=item.company_name,
            company_summary=(
                f"{item.company_name} ({item.industry or 'Unknown'}) — "
                f"intent {item.buying_intent_score}, grade {item.priority_grade or 'n/a'}, "
                f"probability {item.probability}."
            ),
            pain_points=list(item.pain_points)[:8],
            dossier_highlights=list(item.dossier_highlights)[:8],
            buying_intent_score=float(item.buying_intent_score),
            decision_makers=list(item.decision_makers)[:8],
            past_emails=list(item.past_emails)[:10],
            reply_history=list(item.reply_history)[:10],
            recommended_questions=questions,
            likely_objections=list(item.objections)[:6],
            recommended_offer=item.recommended_service,
            estimated_budget=item.expected_budget,
            suggested_pricing=item.expected_budget or "$25k–$55k",
            competitor_signals=list(item.competitors)[:6],
            case_studies=list(item.case_studies)[:6],
            meeting_timeline=timeline,
            follow_up_tasks=follow_ups,
            evidence=[
                f"buying_intent:{item.buying_intent_score}",
                f"dms:{len(item.decision_makers)}",
                f"replies:{len(item.reply_history)}",
            ],
        )
