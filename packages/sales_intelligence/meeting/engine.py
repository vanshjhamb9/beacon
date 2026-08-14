from __future__ import annotations

from sales_intelligence.models.types import (
    BuyingIntentResult,
    MeetingCoachPack,
    PredictedObjection,
    PsychologyProfile,
    SalesIntelligenceInput,
)


class MeetingCoachEngine:
    def coach(
        self,
        item: SalesIntelligenceInput,
        *,
        intent: BuyingIntentResult,
        psychology: PsychologyProfile,
        objections: list[PredictedObjection],
    ) -> MeetingCoachPack:
        dms = [
            {
                "name": dm.get("name") or dm.get("full_name") or "Unknown",
                "title": dm.get("title") or dm.get("role") or "",
                "email": dm.get("email"),
            }
            for dm in item.decision_makers[:8]
        ]
        summary = (
            f"{item.company_name} ({item.industry or 'Unknown industry'}) — "
            f"intent {intent.buying_intent_score}, stage {intent.buying_stage.value}, "
            f"urgency {intent.urgency.value}."
        )
        pain = item.pains[:6] or ["Operational inefficiency", "Manual processes"]
        signals = item.signals[:6] or [
            f"Buying stage: {intent.buying_stage.value}",
            f"Budget band: {intent.budget_probability.value}",
        ]
        questions = [
            "What outcome would make this quarter a win for your team?",
            "Where do manual processes create the most delay today?",
            "Who else needs to approve a vendor decision?",
            "What have you already tried, and what failed?",
            f"How does {psychology.buyer_motivation} show up in your current roadmap?",
            "What is the decision window and success metric?",
        ]
        likely = [f"{o.objection.value}: {o.suggested_response}" for o in objections[:5]]
        closing = (
            "Secure a next-step owner and calendar a proposal review within the decision window."
            if intent.buying_intent_score >= 60
            else "Qualify pain and budget; book a technical discovery if interest is soft."
        )
        goals = [
            "Confirm buying committee and decision window",
            "Validate primary pain and success metric",
            "Align on preferred offer shape",
            "Agree next commercial step",
        ]
        follow = [
            "Send meeting summary within 24h",
            "Share relevant case study / trust pack",
            "Propose dated next meeting or proposal review",
        ]
        return MeetingCoachPack(
            company_summary=summary,
            decision_makers=dms,
            business_pain=pain,
            buying_signals=signals,
            discovery_questions=questions,
            likely_objections=likely,
            closing_strategy=closing,
            meeting_goals=goals,
            follow_up_plan=follow,
            evidence=[f"style:{psychology.preferred_communication_style.value}", f"dms:{len(dms)}"],
        )
