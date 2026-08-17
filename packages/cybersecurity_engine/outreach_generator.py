"""Outreach Message Generator — Creates personalized outreach messages.

NEVER say: "We noticed your company has security vulnerabilities."
Unless the company explicitly disclosed a vulnerability.

Instead say: "Saw that your team is preparing for [verified requirement].
We help teams with [specific security assessment]."
"""

from __future__ import annotations

from cybersecurity_engine.models import (
    CybersecurityOpportunity,
    OpportunityPriority,
    OutreachPreparation,
)


# ============================================================
# MESSAGE TEMPLATES
# ============================================================

TEMPLATES = {
    "direct_response": {
        "subject": "Re: {service_needed} for {company_name}",
        "body": (
            "Hi {buyer_name},\n\n"
            "Saw your post about {problem_summary}.\n\n"
            "We specialize in {services} and have helped teams like yours "
            "{value_proposition}.\n\n"
            "Would you have 15 minutes this week to discuss how we can help?\n\n"
            "Best,\n{name}"
        ),
    },
    "problem_first": {
        "subject": "{company_name} — {service_needed}",
        "body": (
            "Hi {buyer_name},\n\n"
            "{problem_context}\n\n"
            "We help companies with {services}. Our approach includes "
            "{approach}.\n\n"
            "Happy to share how we've helped similar companies.\n\n"
            "Best,\n{name}"
        ),
    },
    "value_proposition": {
        "subject": "Security testing for {company_name}",
        "body": (
            "Hi {buyer_name},\n\n"
            "Noticed {company_name} is {growth_signal}. "
            "Companies at your stage typically need {services} "
            "before {trigger_event}.\n\n"
            "We've helped {similar_companies} with similar requirements.\n\n"
            "Worth a quick chat?\n\n"
            "Best,\n{name}"
        ),
    },
}

FOLLOW_UP_TEMPLATES = [
    {
        "timing": "3 days",
        "body": (
            "Hi {buyer_name},\n\n"
            "Following up on my previous email about {service_needed} "
            "for {company_name}.\n\n"
            "Would love to understand your timeline and how we can help.\n\n"
            "Best,\n{name}"
        ),
    },
    {
        "timing": "7 days",
        "body": (
            "Hi {buyer_name},\n\n"
            "Quick check-in — is {service_needed} still on your radar?\n\n"
            "We have availability starting {available_date} and could "
            "start with a {entry_service}.\n\n"
            "Best,\n{name}"
        ),
    },
    {
        "timing": "14 days",
        "body": (
            "Hi {buyer_name},\n\n"
            "Wanted to share a quick case study of how we helped "
            "{similar_company} with {similar_service}.\n\n"
            "If the timing isn't right, no worries — just let me know.\n\n"
            "Best,\n{name}"
        ),
    },
]


class OutreachMessageGenerator:
    """Generates personalized outreach messages for qualified opportunities."""

    def __init__(
        self,
        sender_name: str = "Security Team",
        sender_company: str = "",
    ) -> None:
        self.sender_name = sender_name
        self.sender_company = sender_company

    def generate(
        self,
        opportunity: CybersecurityOpportunity,
    ) -> OutreachPreparation:
        """Generate full outreach preparation for a qualified opportunity."""
        prep = opportunity.outreach_preparation

        # Generate personalized message
        angle = prep.outreach_angle or "value_proposition"
        template = TEMPLATES.get(angle, TEMPLATES["value_proposition"])

        message = self._fill_template(template, opportunity, prep)
        prep.personalized_message = message

        # Generate subject line
        prep.outreach_angle = self._generate_subject(opportunity, prep)

        # Generate follow-up sequence
        prep.follow_up_sequence = self._generate_follow_ups(opportunity, prep)

        return prep

    def _fill_template(
        self,
        template: dict[str, str],
        opportunity: CybersecurityOpportunity,
        prep: OutreachPreparation,
    ) -> str:
        """Fill a template with opportunity-specific data."""
        company = opportunity.company
        event = opportunity.buying_event
        contact = opportunity.contact

        # Build context variables
        services = "; ".join(event.services_needed[:3]) if event.services_needed else "security testing"

        value_proposition = self._determine_value_proposition(opportunity)
        problem_context = self._determine_problem_context(opportunity)
        growth_signal = self._determine_growth_signal(opportunity)
        trigger_event = self._determine_trigger_event(opportunity)
        approach = self._determine_approach(opportunity)
        similar_companies = self._determine_similar_companies(opportunity)

        fills = {
            "buyer_name": contact.name.split()[0] if contact.name else "there",
            "company_name": company.name,
            "service_needed": services,
            "services": services,
            "problem_summary": event.description[:100],
            "problem_context": problem_context,
            "value_proposition": value_proposition,
            "growth_signal": growth_signal,
            "trigger_event": trigger_event,
            "approach": approach,
            "similar_companies": similar_companies,
            "similar_company": similar_companies.split(",")[0] if similar_companies else "a similar company",
            "similar_service": services,
            "name": self.sender_name,
            "available_date": "next week",
            "entry_service": "vulnerability assessment",
        }

        body = template["body"]
        for key, value in fills.items():
            body = body.replace("{" + key + "}", str(value))

        return body

    def _generate_subject(
        self,
        opportunity: CybersecurityOpportunity,
        prep: OutreachPreparation,
    ) -> str:
        """Generate an email subject line."""
        company = opportunity.company.name
        services = opportunity.buying_event.services_needed
        service = services[0].replace("_", " ").title() if services else "Security Testing"

        if opportunity.priority == OpportunityPriority.P0:
            return f"Re: {service} for {company}"
        elif opportunity.priority == OpportunityPriority.P1:
            return f"{company} — {service}"
        else:
            return f"Security testing for {company}"

    def _determine_value_proposition(self, opportunity: CybersecurityOpportunity) -> str:
        """Determine the value proposition based on opportunity type."""
        if opportunity.priority == OpportunityPriority.P0:
            return "deliver comprehensive security assessments within your timeline"
        elif opportunity.priority == OpportunityPriority.P1:
            return "identify and remediate security issues efficiently"
        else:
            return "establish a strong security posture as you scale"

    def _determine_problem_context(self, opportunity: CybersecurityOpportunity) -> str:
        """Determine problem context for P1 outreach."""
        event = opportunity.buying_event
        if "vulnerability" in event.description.lower():
            return (
                "Security vulnerabilities can impact customer trust and compliance. "
                "A professional assessment helps identify and address these issues "
                "before they become critical."
            )
        elif "compliance" in event.description.lower():
            return (
                "Compliance requirements are increasingly demanding thorough security "
                "assessments. We help teams meet these requirements efficiently."
            )
        else:
            return (
                "External security testing provides an independent view of your "
                "security posture and helps prioritize remediation efforts."
            )

    def _determine_growth_signal(self, opportunity: CybersecurityOpportunity) -> str:
        """Determine growth signal for P2 outreach."""
        if "funding" in opportunity.buying_event.description.lower():
            return "recently secured funding"
        elif "launch" in opportunity.buying_event.description.lower():
            return "launching new products"
        elif "enterprise" in opportunity.buying_event.description.lower():
            return "expanding into enterprise sales"
        else:
            return "growing rapidly"

    def _determine_trigger_event(self, opportunity: CybersecurityOpportunity) -> str:
        """Determine trigger event for P2 outreach."""
        if "soc 2" in opportunity.buying_event.description.lower():
            return "SOC 2 certification"
        elif "iso" in opportunity.buying_event.description.lower():
            return "ISO 27001 certification"
        elif "enterprise" in opportunity.buying_event.description.lower():
            return "enterprise customer onboarding"
        else:
            return "your next growth milestone"

    def _determine_approach(self, opportunity: CybersecurityOpportunity) -> str:
        """Determine the approach to mention."""
        services = opportunity.buying_event.services_needed
        if "penetration_testing" in services:
            return "OWASP-aligned methodology with detailed remediation guidance"
        elif "vulnerability_assessment" in services:
            return "automated scanning combined with manual verification"
        elif "compliance" in services:
            return "compliance-focused assessment aligned with your target framework"
        else:
            return "a structured approach tailored to your specific needs"

    def _determine_similar_companies(self, opportunity: CybersecurityOpportunity) -> str:
        """Determine similar companies for social proof."""
        industry = opportunity.company.industry.lower()
        if "saas" in industry:
            return "B2B SaaS companies preparing for SOC 2"
        elif "fintech" in industry:
            return "fintech companies meeting PCI DSS requirements"
        elif "health" in industry:
            return "healthtech companies ensuring HIPAA compliance"
        else:
            return "growing technology companies"

    def _generate_follow_ups(
        self,
        opportunity: CybersecurityOpportunity,
        prep: OutreachPreparation,
    ) -> list[str]:
        """Generate follow-up sequence."""
        follow_ups = []
        for template in FOLLOW_UP_TEMPLATES:
            message = template["body"]
            message = message.replace("{buyer_name}", prep.buyer_name.split()[0] if prep.buyer_name else "there")
            message = message.replace("{company_name}", prep.company_name)
            message = message.replace("{service_needed}", prep.recommended_service)
            message = message.replace("{name}", self.sender_name)
            message = message.replace("{available_date}", "next week")
            message = message.replace("{entry_service}", "vulnerability assessment")
            message = message.replace("{similar_company}", "a similar company")
            message = message.replace("{similar_service}", prep.recommended_service)
            follow_ups.append(f"[{template['timing']}]\n{message}")

        return follow_ups
