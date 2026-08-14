from __future__ import annotations

from typing import Any

from sales_copilot.generation.grounding_helpers import (
    attribution_for,
    evidence_or_insufficient,
    join_sentences,
)
from sales_copilot.models.types import INSUFFICIENT, IntelligenceSection


SECTION_SPECS: list[tuple[str, str, tuple[str, ...]]] = [
    ("executive_summary", "Executive Summary", ("opportunity", "pain", "service", "decision_maker")),
    ("company_overview", "Company Overview", ("opportunity", "evidence", "knowledge_graph")),
    ("business_model", "Business Model", ("evidence", "knowledge_graph")),
    ("current_situation", "Current Situation", ("opportunity", "timeline", "pain")),
    ("pain_points", "Pain Points", ("pain",)),
    ("growth_signals", "Growth Signals", ("timeline", "hiring")),
    ("buying_signals", "Buying Signals", ("timeline", "opportunity")),
    ("technology_stack", "Technology Stack", ("technology",)),
    ("recent_hiring", "Recent Hiring", ("hiring",)),
    ("decision_makers", "Decision Makers", ("decision_maker",)),
    ("recommended_service", "Recommended Service", ("service", "pain")),
    ("value_proposition", "Value Proposition", ("service", "pain")),
    ("conversation_strategy", "Conversation Strategy", ("service", "pain", "decision_maker")),
    ("opening_angle", "Opening Angle", ("pain", "timeline", "service")),
    ("things_to_mention", "Things To Mention", ("pain", "technology", "hiring", "timeline")),
    ("things_to_avoid", "Things To Avoid", ("verification",)),
    ("possible_objections", "Possible Objections", ("pain", "service")),
    ("suggested_responses", "Suggested Responses", ("service", "pain")),
    ("meeting_objectives", "Meeting Objectives", ("service", "pain", "decision_maker")),
]


class PackageGenerator:
    def generate(self, facts: dict[str, Any]) -> list[IntelligenceSection]:
        builders = {
            "executive_summary": self._executive_summary,
            "company_overview": self._company_overview,
            "business_model": self._business_model,
            "current_situation": self._current_situation,
            "pain_points": self._pain_points,
            "growth_signals": self._growth_signals,
            "buying_signals": self._buying_signals,
            "technology_stack": self._technology_stack,
            "recent_hiring": self._recent_hiring,
            "decision_makers": self._decision_makers,
            "recommended_service": self._recommended_service,
            "value_proposition": self._value_proposition,
            "conversation_strategy": self._conversation_strategy,
            "opening_angle": self._opening_angle,
            "things_to_mention": self._things_to_mention,
            "things_to_avoid": self._things_to_avoid,
            "possible_objections": self._possible_objections,
            "suggested_responses": self._suggested_responses,
            "meeting_objectives": self._meeting_objectives,
        }
        sections: list[IntelligenceSection] = []
        for key, title, categories in SECTION_SPECS:
            content = builders[key](facts)
            attribution = attribution_for(key, facts, categories=categories, grounded=content != INSUFFICIENT)
            sections.append(IntelligenceSection(key=key, title=title, content=content, attribution=attribution))
        return sections

    def _executive_summary(self, facts: dict[str, Any]) -> str:
        pain = facts.get("business_pain") or INSUFFICIENT
        service = facts.get("recommended_service") or INSUFFICIENT
        score = facts.get("opportunity_score")
        if pain == INSUFFICIENT and service == INSUFFICIENT:
            return INSUFFICIENT
        return join_sentences(
            f"{facts.get('company_name')} shows an opportunity score of {score:.1f}." if isinstance(score, (int, float)) else "",
            f"Verified business pain: {pain}." if pain != INSUFFICIENT else "",
            f"Recommended Beacon service: {service}." if service != INSUFFICIENT else "",
        )

    def _company_overview(self, facts: dict[str, Any]) -> str:
        return join_sentences(
            f"{facts.get('company_name')} operates in {facts.get('industry')}." if facts.get("industry") else f"{facts.get('company_name')}.",
            f"Domain: {facts.get('domain')}." if facts.get("domain") else "",
            f"Website: {facts.get('website')}." if facts.get("website") else "",
        )

    def _business_model(self, facts: dict[str, Any]) -> str:
        return facts.get("business_model") or INSUFFICIENT

    def _current_situation(self, facts: dict[str, Any]) -> str:
        return facts.get("current_situation") or evidence_or_insufficient(facts.get("timeline_highlights"))

    def _pain_points(self, facts: dict[str, Any]) -> str:
        return evidence_or_insufficient(facts.get("pain_points"))

    def _growth_signals(self, facts: dict[str, Any]) -> str:
        return evidence_or_insufficient(facts.get("growth_signals"))

    def _buying_signals(self, facts: dict[str, Any]) -> str:
        return evidence_or_insufficient(facts.get("buying_signals"))

    def _technology_stack(self, facts: dict[str, Any]) -> str:
        return evidence_or_insufficient(facts.get("technology_stack"))

    def _recent_hiring(self, facts: dict[str, Any]) -> str:
        return evidence_or_insufficient(facts.get("recent_hiring"))

    def _decision_makers(self, facts: dict[str, Any]) -> str:
        return evidence_or_insufficient(facts.get("decision_makers"))

    def _recommended_service(self, facts: dict[str, Any]) -> str:
        service = facts.get("recommended_service")
        pain = facts.get("business_pain")
        if not service:
            return INSUFFICIENT
        if pain:
            return f"{service} — aligned to verified pain: {pain}."
        return str(service)

    def _value_proposition(self, facts: dict[str, Any]) -> str:
        value = facts.get("value_proposition")
        if value:
            return str(value)
        service = facts.get("recommended_service")
        pain = facts.get("business_pain")
        if service and pain:
            return f"{service} can address the verified need around {pain}."
        return INSUFFICIENT

    def _conversation_strategy(self, facts: dict[str, Any]) -> str:
        angles = facts.get("conversation_angles") or []
        makers = facts.get("decision_makers") or []
        primary = makers[0]["name"] if makers else None
        parts = []
        if primary:
            parts.append(f"Lead with the verified contact {primary}.")
        if angles:
            parts.append("Use verified conversation angles: " + "; ".join(angles[:3]) + ".")
        elif facts.get("business_pain"):
            parts.append(f"Open on the verified pain: {facts.get('business_pain')}.")
        return join_sentences(*parts)

    def _opening_angle(self, facts: dict[str, Any]) -> str:
        angles = facts.get("conversation_angles") or []
        if angles:
            return str(angles[0])
        if facts.get("business_pain"):
            return f"Reference the verified challenge around {facts.get('business_pain')}."
        return INSUFFICIENT

    def _things_to_mention(self, facts: dict[str, Any]) -> str:
        mentions: list[str] = []
        for key in ("business_pain",):
            if facts.get(key):
                mentions.append(str(facts[key]))
        mentions.extend(list(facts.get("technology_stack") or [])[:3])
        mentions.extend(list(facts.get("recent_hiring") or [])[:2])
        mentions.extend(list(facts.get("timeline_highlights") or [])[:2])
        return evidence_or_insufficient(mentions)

    def _things_to_avoid(self, facts: dict[str, Any]) -> str:
        return (
            "Do not invent contacts, revenue figures, tech stack items, or hiring claims. "
            "Do not claim outreach was sent. Only reference Beacon-verified evidence. "
            f"Verification status: {facts.get('verification_status') or 'not available'}."
        )

    def _possible_objections(self, facts: dict[str, Any]) -> str:
        service = facts.get("recommended_service")
        if not service:
            return INSUFFICIENT
        return (
            f"- Timing: leadership may not prioritize {service} yet.\n"
            f"- Scope: they may question whether {service} fits current operations.\n"
            "- Proof: they may ask for evidence tied to their verified pain points."
        )

    def _suggested_responses(self, facts: dict[str, Any]) -> str:
        pain = facts.get("business_pain")
        service = facts.get("recommended_service")
        if not pain or not service:
            return INSUFFICIENT
        return (
            f"- Timing: acknowledge priorities, then reconnect the discussion to verified pain ({pain}).\n"
            f"- Scope: propose a narrow discovery focused on whether {service} maps to that pain.\n"
            "- Proof: share only Beacon-verified signals already present in this package."
        )

    def _meeting_objectives(self, facts: dict[str, Any]) -> str:
        service = facts.get("recommended_service") or "the recommended service"
        pain = facts.get("business_pain") or "verified operational challenges"
        return (
            f"1. Confirm the verified pain around {pain}.\n"
            f"2. Validate whether {service} is a fit.\n"
            "3. Identify next-step owners from verified decision makers.\n"
            "4. Agree on a follow-up with clear success criteria."
        )
