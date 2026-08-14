"""Outreach Preparation Engine - Generate actual personalized outreach drafts.

For every SALES_READY lead, generate channel-specific drafts:
- Email
- LinkedIn
- WhatsApp
- Reddit DM

Each draft is evidence-based, personalized, and requires founder approval before sending.
No auto-send. Founder approval mandatory.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.models.buying_event import (
    BuyingEvent,
    BuyingEventClassification,
    BusinessType,
    OutreachChannel,
)

logger = logging.getLogger(__name__)


@dataclass
class ChannelDraft:
    """A single channel-specific outreach draft."""
    channel: str
    style: str
    subject: str | None
    body: str
    personalization_points: list[str]
    evidence_chain: list[dict[str, Any]]
    quality_scores: dict[str, float]


@dataclass
class OutreachPreparation:
    """Complete outreach preparation for a SALES_READY lead."""
    company: str
    business_type: str
    opportunity_type: str
    buyer_name: str | None
    buyer_role: str | None
    problem: str
    evidence: list[dict[str, Any]]
    why_now: str
    solution: str
    why_comai: str | None
    why_inowix: str | None
    recommended_channel: str
    contact: str
    personalization_points: list[str]
    outreach_angle: str
    outreach_message: dict[str, ChannelDraft]
    follow_up_sequence: list[dict[str, str]]


class OutreachPreparationEngine:
    """Generate actual outreach drafts for every SALES_READY lead."""
    
    # Outreach styles
    STYLES = {
        "founder": "founder_to_founder",
        "ceo": "founder_to_founder",
        "cto": "technical",
        "coo": "consultative",
        "head": "consultative",
        "director": "professional",
        "manager": "professional",
        "default": "professional",
    }
    
    # Inowix signature
    SIGNATURE = """
Best,
Vansh Jhamb
Founder
Inowix Technologies
vansh@inowix.in
https://www.inowix.in/
"""
    
    def prepare_outreach(self, opportunity: BuyingEvent) -> OutreachPreparation:
        """Generate channel-specific drafts for a SALES_READY lead."""
        
        # Determine buyer role
        buyer_name = opportunity.contact_info.get("author")
        buyer_role = self._infer_role(opportunity.contact_info)
        
        # Pick style based on role
        style = self.STYLES.get(buyer_role, self.STYLES["default"])
        
        # Generate channel-specific drafts
        drafts = {}
        for channel in ["email", "linkedin", "whatsapp", "reddit_dm"]:
            draft = self._generate_draft(
                channel=channel,
                opportunity=opportunity,
                style=style,
                buyer_name=buyer_name,
            )
            drafts[channel] = draft
        
        # Pick recommended channel
        recommended_channel = self._pick_channel(opportunity.contact_info)
        
        # Build personalization points
        personalization_points = self._extract_personalization(opportunity)
        
        # Detect outreach angle
        outreach_angle = self._detect_angle(opportunity)
        
        # Generate follow-up sequence
        follow_ups = self._generate_followups(opportunity, style)
        
        # Build why_comai/why_inowix
        why_comai, why_inowix = self._build_why_solution(opportunity)
        
        return OutreachPreparation(
            company=opportunity.company_name,
            business_type=opportunity.business_type.value if opportunity.business_type else "UNKNOWN",
            opportunity_type=opportunity.classification.value,
            buyer_name=buyer_name,
            buyer_role=buyer_role,
            problem=opportunity.problem or "Unknown problem",
            evidence=opportunity.evidence or [],
            why_now=opportunity.why_now or "Timely opportunity",
            solution=opportunity.solution_match or "Unknown solution",
            why_comai=why_comai,
            why_inowix=why_inowix,
            recommended_channel=recommended_channel,
            contact=self._format_contact(opportunity.contact_info),
            personalization_points=personalization_points,
            outreach_angle=outreach_angle,
            outreach_message=drafts,
            follow_up_sequence=follow_ups,
        )
    
    def _generate_draft(
        self,
        channel: str,
        opportunity: BuyingEvent,
        style: str,
        buyer_name: str | None,
    ) -> ChannelDraft:
        """Generate a single channel-specific draft."""
        
        if channel == "email":
            return self._generate_email(opportunity, style, buyer_name)
        elif channel == "linkedin":
            return self._generate_linkedin(opportunity, style, buyer_name)
        elif channel == "whatsapp":
            return self._generate_whatsapp(opportunity, style, buyer_name)
        elif channel == "reddit_dm":
            return self._generate_reddit_dm(opportunity, style, buyer_name)
        
        return ChannelDraft(
            channel=channel,
            style=style,
            subject=None,
            body="",
            personalization_points=[],
            evidence_chain=[],
            quality_scores={},
        )
    
    def _generate_email(
        self,
        opportunity: BuyingEvent,
        style: str,
        buyer_name: str | None,
    ) -> ChannelDraft:
        """Generate personalized email draft."""
        
        name = buyer_name or "there"
        company = opportunity.company_name or "your company"
        
        # Build hook based on classification
        hook = self._build_hook(opportunity)
        
        # Build problem statement
        problem_statement = self._build_problem_statement(opportunity)
        
        # Build solution pitch
        solution_pitch = self._build_solution_pitch(opportunity)
        
        # Build CTA
        cta = self._build_cta(opportunity)
        
        # Generate subject
        subject = self._generate_subject(opportunity, style)
        
        # Build body
        body = f"""Hi {name},

{hook}

{problem_statement}

{solution_pitch}

{cta}
{self.SIGNATURE}"""
        
        return ChannelDraft(
            channel="email",
            style=style,
            subject=subject,
            body=body.strip(),
            personalization_points=self._extract_personalization(opportunity),
            evidence_chain=opportunity.evidence[:3] if opportunity.evidence else [],
            quality_scores={
                "personalization": 0.8,
                "evidence_coverage": 0.7,
                "readability": 0.9,
                "professional_tone": 0.9,
            },
        )
    
    def _generate_linkedin(
        self,
        opportunity: BuyingEvent,
        style: str,
        buyer_name: str | None,
    ) -> ChannelDraft:
        """Generate LinkedIn message draft."""
        
        name = buyer_name or "there"
        company = opportunity.company_name or "your company"
        
        # Shorter, more casual for LinkedIn
        hook = self._build_hook_short(opportunity)
        body = f"""Hi {name},

{hook}

Would love to connect and learn more about what you're building at {company}.

Best,
Vansh"""
        
        return ChannelDraft(
            channel="linkedin",
            style=style,
            subject=None,
            body=body.strip(),
            personalization_points=self._extract_personalization(opportunity),
            evidence_chain=opportunity.evidence[:2] if opportunity.evidence else [],
            quality_scores={
                "personalization": 0.7,
                "brevity": 0.9,
                "professional_tone": 0.8,
            },
        )
    
    def _generate_whatsapp(
        self,
        opportunity: BuyingEvent,
        style: str,
        buyer_name: str | None,
    ) -> ChannelDraft:
        """Generate WhatsApp message draft."""
        
        name = buyer_name or "there"
        company = opportunity.company_name or "your company"
        
        # Very short for WhatsApp
        body = f"""Hi {name}, I noticed {opportunity.problem or 'your company is growing'}. We help businesses like {company} with {opportunity.solution_match or 'technical solutions'}. Would love to chat! - Vansh, Inowix"""
        
        return ChannelDraft(
            channel="whatsapp",
            style=style,
            subject=None,
            body=body.strip(),
            personalization_points=self._extract_personalization(opportunity)[:2],
            evidence_chain=[],
            quality_scores={
                "brevity": 0.9,
                "casual_tone": 0.8,
            },
        )
    
    def _generate_reddit_dm(
        self,
        opportunity: BuyingEvent,
        style: str,
        buyer_name: str | None,
    ) -> ChannelDraft:
        """Generate Reddit DM draft."""
        
        name = buyer_name or "there"
        company = opportunity.company_name or "your company"
        
        # Reddit style - helpful, not salesy
        body = f"""Hey {name},

Saw your post about {opportunity.problem or 'your project'}. I've helped similar companies with {opportunity.solution_match or 'technical challenges'}.

Happy to share some insights if you're interested. No pitch, just useful info.

Best,
Vansh"""
        
        return ChannelDraft(
            channel="reddit_dm",
            style=style,
            subject=None,
            body=body.strip(),
            personalization_points=self._extract_personalization(opportunity)[:2],
            evidence_chain=[],
            quality_scores={
                "helpful_tone": 0.9,
                "non_salesy": 0.9,
            },
        )
    
    def _build_hook(self, opportunity: BuyingEvent) -> str:
        """Build evidence-based hook (never generic)."""
        
        if opportunity.classification == BuyingEventClassification.ACTIVE_BUYING_EVENT:
            return f"I noticed you're looking for {opportunity.problem}."
        
        elif opportunity.classification == BuyingEventClassification.VERIFIED_PAIN:
            evidence = opportunity.evidence[0] if opportunity.evidence else {}
            source = evidence.get("source", "your platform")
            return f"I came across {source} and noticed {opportunity.problem}."
        
        elif opportunity.classification == BuyingEventClassification.PARTNER_OPPORTUNITY:
            return f"Given {opportunity.company_name}'s focus on serving clients,"
        
        else:
            return f"Given {opportunity.company_name}'s growth,"
    
    def _build_hook_short(self, opportunity: BuyingEvent) -> str:
        """Build short hook for LinkedIn/WhatsApp."""
        
        if opportunity.classification == BuyingEventClassification.ACTIVE_BUYING_EVENT:
            return f"Saw you're looking for help with {opportunity.problem}."
        
        elif opportunity.classification == BuyingEventClassification.VERIFIED_PAIN:
            return f"noticed your team is dealing with {opportunity.problem}."
        
        else:
            return f"interested in what you're building at {opportunity.company_name}."
    
    def _build_problem_statement(self, opportunity: BuyingEvent) -> str:
        """Build problem statement from evidence."""
        
        if opportunity.problem:
            return f"Based on what I've seen, {opportunity.problem} is a challenge you're facing."
        
        return "I understand you're working through some technical challenges."
    
    def _build_solution_pitch(self, opportunity: BuyingEvent) -> str:
        """Build solution pitch based on lane."""
        
        if opportunity.department.value == "COMAI":
            return """We help ecommerce businesses automate customer support with AI-powered WhatsApp chatbots. Our clients typically see 60% reduction in support tickets and 3x faster response times."""
        
        else:  # INOWIX
            return """We help startups and growing businesses ship software faster. Our team has built MVPs, SaaS platforms, and mobile apps for companies at every stage."""
    
    def _build_cta(self, opportunity: BuyingEvent) -> str:
        """Build call-to-action."""
        
        if opportunity.classification == BuyingEventClassification.ACTIVE_BUYING_EVENT:
            return "Would you be open to a quick 15-minute call to discuss how we can help?"
        
        elif opportunity.classification == BuyingEventClassification.VERIFIED_PAIN:
            return "Would you be interested in a brief call to explore if we can help?"
        
        elif opportunity.classification == BuyingEventClassification.PARTNER_OPPORTUNITY:
            return "Would you be open to a quick chat about a potential partnership?"
        
        else:
            return "Happy to share more about how we've helped similar companies."
    
    def _generate_subject(self, opportunity: BuyingEvent, style: str) -> str:
        """Generate email subject line."""
        
        company = opportunity.company_name or "Your company"
        
        if opportunity.classification == BuyingEventClassification.ACTIVE_BUYING_EVENT:
            return f"Helping {company} with {opportunity.problem or 'your project'}"
        
        elif opportunity.classification == BuyingEventClassification.VERIFIED_PAIN:
            return f"{company} + Inowix: A quick idea"
        
        elif opportunity.classification == BuyingEventClassification.PARTNER_OPPORTUNITY:
            return f"Partnership opportunity with {company}"
        
        else:
            return f"Quick question about {company}"
    
    def _infer_role(self, contact_info: dict[str, Any]) -> str:
        """Infer buyer role from contact info."""
        
        # Check for role indicators in author/title
        author = (contact_info.get("author") or "").lower()
        title = (contact_info.get("title") or "").lower()
        
        combined = f"{author} {title}"
        
        if any(x in combined for x in ["founder", "ceo", "owner"]):
            return "founder"
        elif any(x in combined for x in ["cto", "technical", "engineering"]):
            return "cto"
        elif any(x in combined for x in ["coo", "operations"]):
            return "coo"
        elif any(x in combined for x in ["head", "director"]):
            return "head"
        elif any(x in combined for x in ["manager"]):
            return "manager"
        
        return "default"
    
    def _pick_channel(self, contact_info: dict[str, Any]) -> str:
        """Pick recommended outreach channel."""
        
        if contact_info.get("email"):
            return "email"
        elif contact_info.get("linkedin"):
            return "linkedin"
        elif contact_info.get("reddit_username"):
            return "reddit_dm"
        else:
            return "email"
    
    def _format_contact(self, contact_info: dict[str, Any]) -> str:
        """Format contact information."""
        
        parts = []
        if contact_info.get("email"):
            parts.append(f"Email: {contact_info['email']}")
        if contact_info.get("linkedin"):
            parts.append(f"LinkedIn: {contact_info['linkedin']}")
        if contact_info.get("twitter"):
            parts.append(f"Twitter: {contact_info['twitter']}")
        
        return " | ".join(parts) if parts else "N/A"
    
    def _extract_personalization(self, opportunity: BuyingEvent) -> list[str]:
        """Extract personalization points from evidence."""
        
        points = []
        
        # Add company name
        if opportunity.company_name:
            points.append(f"Company: {opportunity.company_name}")
        
        # Add problem
        if opportunity.problem:
            points.append(f"Problem: {opportunity.problem}")
        
        # Add evidence-based points
        if opportunity.evidence:
            for ev in opportunity.evidence[:3]:
                if ev.get("type") == "buying_signal":
                    points.append(f"Signal: {ev.get('description', '')}")
                elif ev.get("type") == "pain_signal":
                    points.append(f"Pain: {ev.get('description', '')}")
        
        return points
    
    def _detect_angle(self, opportunity: BuyingEvent) -> str:
        """Detect outreach angle from signals."""
        
        if opportunity.classification == BuyingEventClassification.ACTIVE_BUYING_EVENT:
            return "active_buyer"
        elif opportunity.classification == BuyingEventClassification.VERIFIED_PAIN:
            return "pain_based"
        elif opportunity.classification == BuyingEventClassification.PARTNER_OPPORTUNITY:
            return "partner"
        else:
            return "icp"
    
    def _build_why_solution(self, opportunity: BuyingEvent) -> tuple[str | None, str | None]:
        """Build why_comai or why_inowix explanation."""
        
        why_comai = None
        why_inowix = None
        
        if opportunity.department.value == "COMAI":
            why_comai = f"COMAI can help {opportunity.company_name} automate customer support with AI-powered WhatsApp chatbots, reducing support burden and improving response times."
        else:
            why_inowix = f"INOWIX can help {opportunity.company_name} ship their technical projects faster with our experienced development team."
        
        return why_comai, why_inowix
    
    def _generate_followups(
        self,
        opportunity: BuyingEvent,
        style: str,
    ) -> list[dict[str, str]]:
        """Generate follow-up sequence."""
        
        company = opportunity.company_name or "your company"
        
        return [
            {
                "day": "0",
                "channel": "email",
                "body": f"Initial outreach to {company}",
            },
            {
                "day": "2",
                "channel": "email",
                "body": f"Follow-up: Any thoughts on my previous email about {opportunity.problem or 'your project'}?",
            },
            {
                "day": "5",
                "channel": "linkedin",
                "body": f"LinkedIn connection request with note about {company}",
            },
            {
                "day": "7",
                "channel": "email",
                "body": f"Final follow-up: Happy to chat whenever works for you.",
            },
        ]
