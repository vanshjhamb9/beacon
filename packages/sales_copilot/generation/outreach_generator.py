from __future__ import annotations

from typing import Any

from sales_copilot.generation.grounding_helpers import attribution_for
from sales_copilot.models.types import (
    INSUFFICIENT,
    DraftKind,
    OutreachDraft,
    OutreachStyle,
    StyleVariantPackage,
)
from sales_copilot.templates.styles import STYLE_GUIDANCE


class OutreachGenerator:
    def generate_all_styles(self, facts: dict[str, Any]) -> list[StyleVariantPackage]:
        return [StyleVariantPackage(style=style, drafts=self.generate_for_style(facts, style)) for style in OutreachStyle]

    def generate_for_style(self, facts: dict[str, Any], style: OutreachStyle) -> list[OutreachDraft]:
        guide = STYLE_GUIDANCE[style]
        company = facts.get("company_name") or "your team"
        pain = facts.get("business_pain") or INSUFFICIENT
        service = facts.get("recommended_service") or INSUFFICIENT
        makers = facts.get("decision_makers") or []
        contact = makers[0]["name"] if makers else None
        greeting_name = contact or company
        mention_bits = []
        if pain != INSUFFICIENT:
            mention_bits.append(pain)
        techs = list(facts.get("technology_stack") or [])[:2]
        mention_bits.extend(techs)
        hiring = list(facts.get("recent_hiring") or [])[:1]
        mention_bits.extend(hiring)
        evidence_line = "; ".join(mention_bits[:3]) if mention_bits else INSUFFICIENT

        subjects = self._subject_lines(company, pain, service)
        email_body = self._email(guide, greeting_name, company, pain, service, evidence_line)
        linkedin = self._linkedin(guide, greeting_name, pain, service)
        whatsapp = self._whatsapp(guide, greeting_name, pain, service)
        video = self._video(company, pain, service, evidence_line)
        agenda = self._agenda(company, pain, service)
        questions = self._discovery_questions(pain, service)
        followups = self._followups(guide, style, facts, greeting_name, company, pain, service)

        drafts = [
            OutreachDraft(
                kind=DraftKind.EMAIL,
                style=style,
                title=f"{style.value} email",
                body=email_body,
                subject_lines=subjects,
                attribution=attribution_for("email", facts, categories=("pain", "service", "decision_maker", "technology")),
            ),
            OutreachDraft(
                kind=DraftKind.SUBJECT_LINE,
                style=style,
                title=f"{style.value} subject lines",
                body="\n".join(f"{idx + 1}. {line}" for idx, line in enumerate(subjects)),
                subject_lines=subjects,
                attribution=attribution_for("subject_lines", facts, categories=("pain", "service")),
            ),
            OutreachDraft(
                kind=DraftKind.LINKEDIN,
                style=style,
                title=f"{style.value} linkedin",
                body=linkedin,
                attribution=attribution_for("linkedin", facts, categories=("pain", "service", "decision_maker")),
            ),
            OutreachDraft(
                kind=DraftKind.WHATSAPP,
                style=style,
                title=f"{style.value} whatsapp",
                body=whatsapp,
                attribution=attribution_for("whatsapp", facts, categories=("pain", "service")),
            ),
            OutreachDraft(
                kind=DraftKind.VIDEO_SCRIPT,
                style=style,
                title=f"{style.value} video script",
                body=video,
                attribution=attribution_for("video_script", facts, categories=("pain", "service", "timeline")),
            ),
            OutreachDraft(
                kind=DraftKind.MEETING_AGENDA,
                style=style,
                title=f"{style.value} meeting agenda",
                body=agenda,
                attribution=attribution_for("meeting_agenda", facts, categories=("pain", "service", "decision_maker")),
            ),
            OutreachDraft(
                kind=DraftKind.DISCOVERY_QUESTION,
                style=style,
                title=f"{style.value} discovery questions",
                body=questions,
                attribution=attribution_for("discovery_questions", facts, categories=("pain", "service")),
            ),
            *followups,
        ]
        return drafts

    def _subject_lines(self, company: str, pain: str, service: str) -> list[str]:
        if pain == INSUFFICIENT and service == INSUFFICIENT:
            return [
                f"Quick question about {company}",
                f"Idea for {company}",
                f"Worth a brief look at {company}?",
            ]
        return [
            f"{company}: idea around {pain if pain != INSUFFICIENT else service}",
            f"Re: {service if service != INSUFFICIENT else 'next step'} for {company}",
            f"Noticed a signal at {company} — quick thought",
        ]

    def _email(self, guide: dict[str, str], greeting_name: str, company: str, pain: str, service: str, evidence_line: str) -> str:
        pain_line = (
            f"I noticed a verified challenge around {pain}."
            if pain != INSUFFICIENT
            else "I reviewed your Beacon profile and wanted to share a grounded observation."
        )
        service_line = (
            f"We help teams explore {service} when that challenge is confirmed."
            if service != INSUFFICIENT
            else "Happy to share a short perspective based only on verified signals."
        )
        evidence = (
            f"Signals we can cite: {evidence_line}."
            if evidence_line != INSUFFICIENT
            else "I will stick only to verified Beacon evidence in any follow-up."
        )
        return (
            f"{guide['salutation']} {greeting_name},\n\n"
            f"{pain_line} {service_line}\n\n"
            f"{evidence}\n\n"
            f"{guide['cta']}\n\n"
            f"{guide['signoff']}"
        )

    def _linkedin(self, guide: dict[str, str], greeting_name: str, pain: str, service: str) -> str:
        focus = pain if pain != INSUFFICIENT else service
        if focus == INSUFFICIENT:
            return f"{guide['salutation']} {greeting_name} — came across your company via Beacon and wanted to connect. {guide['cta']}"
        return (
            f"{guide['salutation']} {greeting_name}, I saw a verified signal around {focus}. "
            f"Would value your perspective. {guide['cta']}"
        )

    def _whatsapp(self, guide: dict[str, str], greeting_name: str, pain: str, service: str) -> str:
        focus = pain if pain != INSUFFICIENT else service
        if focus == INSUFFICIENT:
            return f"Hi {greeting_name}, sharing a draft note based on verified Beacon research. {guide['cta']}"
        return f"Hi {greeting_name}, quick draft based on verified research around {focus}. {guide['cta']}"

    def _video(self, company: str, pain: str, service: str, evidence_line: str) -> str:
        return (
            f"[0-5s] Hi — quick personal note for {company}.\n"
            f"[5-15s] Beacon verified signal: {pain if pain != INSUFFICIENT else 'limited verified context'}.\n"
            f"[15-25s] Potential fit to explore: {service if service != INSUFFICIENT else INSUFFICIENT}.\n"
            f"[25-30s] Evidence I can cite: {evidence_line}. Open to a short conversation?"
        )

    def _agenda(self, company: str, pain: str, service: str) -> str:
        return (
            f"Meeting agenda for {company}\n"
            f"1. Confirm verified pain: {pain if pain != INSUFFICIENT else INSUFFICIENT}\n"
            f"2. Review whether {service if service != INSUFFICIENT else 'a Beacon-recommended service'} is relevant\n"
            "3. Walk verified evidence only\n"
            "4. Agree owners and next step"
        )

    def _discovery_questions(self, pain: str, service: str) -> str:
        pain_q = pain if pain != INSUFFICIENT else "your current operational priorities"
        service_q = service if service != INSUFFICIENT else "possible solutions"
        return (
            f"1. How are you currently handling {pain_q}?\n"
            f"2. What would success look like if {service_q} helped?\n"
            "3. Who else should be involved based on your internal ownership?\n"
            "4. What evidence would you need before exploring next steps?\n"
            "5. What timeline is realistic if the pain is confirmed?"
        )

    def _followups(
        self,
        guide: dict[str, str],
        style: OutreachStyle,
        facts: dict[str, Any],
        greeting_name: str,
        company: str,
        pain: str,
        service: str,
    ) -> list[OutreachDraft]:
        focus = pain if pain != INSUFFICIENT else service
        bodies = [
            (
                DraftKind.FOLLOW_UP_1,
                (
                    f"{guide['salutation']} {greeting_name},\n\n"
                    f"Following up on my note about {company}. "
                    f"Happy to keep this tied to verified signals"
                    f"{f' around {focus}' if focus != INSUFFICIENT else ''}.\n\n{guide['cta']}\n\n{guide['signoff']}"
                ),
            ),
            (
                DraftKind.FOLLOW_UP_2,
                (
                    f"{guide['salutation']} {greeting_name},\n\n"
                    "Sharing a shorter follow-up for human review. "
                    "I will not invent details beyond Beacon evidence.\n\n"
                    f"{guide['cta']}\n\n{guide['signoff']}"
                ),
            ),
            (
                DraftKind.FOLLOW_UP_3,
                (
                    f"{guide['salutation']} {greeting_name},\n\n"
                    "Final soft follow-up draft. If now is not the right time, I will leave the door open.\n\n"
                    f"{guide['signoff']}"
                ),
            ),
        ]
        return [
            OutreachDraft(
                kind=kind,
                style=style,
                title=f"{style.value} {kind.value}",
                body=body,
                attribution=attribution_for(
                    kind.value,
                    facts,
                    categories=("pain", "service"),
                    grounded=focus != INSUFFICIENT,
                ),
            )
            for kind, body in bodies
        ]
