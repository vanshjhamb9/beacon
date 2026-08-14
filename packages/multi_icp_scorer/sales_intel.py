"""Sales Intelligence Generator for Beacon.

Produces actionable sales intel for each opportunity:
- Why this matters to Inowix
- What problem our service solves
- Why contact now (evidence-based)
- Recommended pitch angle
- Likely objection
- Suggested CTA

Every field must have evidence. No speculation.
"""

from __future__ import annotations

from datetime import date

from packages.opportunity_intelligence.canonical import (
    BusinessUnit,
    EvidenceConfidence,
    IntentLevel,
    Opportunity,
    ServiceMatch,
)


def generate_sales_intel(opportunity: Opportunity) -> Opportunity:
    """Generate sales intelligence for an opportunity.

    Fills in:
    - why_this_matters
    - what_they_achieving
    - likely_pain
    - evidence_for_pain
    - why_inowix_relevant
    - recommended_service
    - recommended_pitch
    - why_now
    - likely_objection
    - suggested_cta
    """
    bu = opportunity.primary_business_unit
    intent = opportunity.intent_level
    signals_text = " ".join([
        s.signal_text for s in opportunity.intent_signals
    ] + [e.claim for e in opportunity.evidence])
    signals_lower = signals_text.lower()

    # --- Why this matters ---
    if intent == IntentLevel.ACTIVE_REQUIREMENT:
        opportunity.why_this_matters = (
            f"Active buying requirement detected. {opportunity.company_name} "
            f"has explicitly expressed a need that Inowix can fulfill."
        )
    elif intent == IntentLevel.EVALUATION:
        opportunity.why_this_matters = (
            f"Active evaluation detected. {opportunity.company_name} is "
            f"evaluating solutions — we should be in the conversation."
        )
    elif intent == IntentLevel.EARLY_INTENT:
        opportunity.why_this_matters = (
            f"Problem awareness detected. {opportunity.company_name} knows they "
            f"have a challenge — we can position before they choose a competitor."
        )
    else:
        opportunity.why_this_matters = (
            f"Company profile matches Inowix ICP. No explicit intent detected, "
            f"but {opportunity.company_name} could benefit from our services."
        )

    # --- What they're achieving ---
    opportunity.what_they_achieving = _detect_achieving(signals_lower, bu)

    # --- Pain ---
    opportunity.likely_pain = _detect_pain(signals_lower, bu, intent)

    # --- Evidence for pain ---
    pain_evidence = []
    for e in opportunity.evidence:
        if any(kw in e.claim.lower() for kw in ["manual", "struggling", "challenge",
                                                   "inefficient", "bottleneck", "problem"]):
            pain_evidence.append(f"{e.claim} (confidence: {e.confidence.value})")
    opportunity.evidence_for_pain = (
        "; ".join(pain_evidence[:3]) if pain_evidence
        else "No direct pain evidence found — this is a profile-based opportunity."
    )

    # --- Why Inowix relevant ---
    opportunity.why_inowix_relevant = _generate_relevance(bu, intent, signals_lower)

    # --- Recommended service ---
    if opportunity.service_matches:
        best = opportunity.service_matches[0]
        opportunity.recommended_service = f"{best.service_name} ({best.business_unit.value})"
    else:
        opportunity.recommended_service = "Consultation"

    # --- Recommended pitch ---
    opportunity.recommended_pitch = _generate_pitch(bu, intent, signals_lower)

    # --- Why now ---
    opportunity.why_now = _generate_why_now(intent, opportunity)

    # --- Likely objection ---
    opportunity.likely_objection = _generate_objection(bu, signals_lower)

    # --- Suggested CTA ---
    opportunity.suggested_cta = _generate_cta(bu, intent)

    return opportunity


# ============================================================
# PRIVATE HELPERS
# ============================================================

def _detect_achieving(text: str, bu: BusinessUnit) -> str:
    achievements = []
    if any(kw in text for kw in ["shopify", "ecommerce", "store", "online"]):
        achievements.append("Running ecommerce operations")
    if any(kw in text for kw in ["saas", "platform", "product"]):
        achievements.append("Building SaaS product")
    if any(kw in text for kw in ["funded", "raised", "series"]):
        achievements.append("Secured funding")
    if any(kw in text for kw in ["team", "employees", "staff"]):
        achievements.append("Has team in place")
    if any(kw in text for kw in ["customers", "users", "clients"]):
        achievements.append("Has existing customer base")
    return "Company is " + (", ".join(achievements) if achievements else "operating in their market")


def _detect_pain(text: str, bu: BusinessUnit, intent: IntentLevel) -> str:
    pains = []
    if any(kw in text for kw in ["manual", "repetitive", "time-consuming"]):
        pains.append("Manual processes consuming team time")
    if any(kw in text for kw in ["struggling", "problem", "challenge", "bottleneck"]):
        pains.append("Identified operational challenges")
    if any(kw in text for kw in ["scaling", "growing", "expanding"]) and \
       any(kw in text for kw in ["challenge", "struggle", "problem", "bottleneck"]):
        pains.append("Growing pains from scaling")
    if any(kw in text for kw in ["customer support", "support team", "customer queries"]):
        pains.append("Customer support burden")
    if not pains:
        if intent in (IntentLevel.ACTIVE_REQUIREMENT, IntentLevel.EVALUATION):
            pains.append("Actively seeking a solution (explicit intent detected)")
        else:
            pains.append("Pain not directly evidenced — infer from profile")
    return "; ".join(pains)


def _generate_relevance(bu: BusinessUnit, intent: IntentLevel, text: str) -> str:
    if bu == BusinessUnit.COMAI:
        return (
            "Inowix COMAI offers AI-powered automation for ecommerce brands — "
            "WhatsApp bots, customer support automation, product recommendations, "
            "and cart recovery. This aligns with the company's ecommerce operations "
            "and customer engagement needs."
        )
    elif bu == BusinessUnit.SAAS_DEVELOPMENT:
        return (
            "Inowix SaaS Development provides product engineering, dedicated teams, "
            "CTO-as-a-service, and cloud architecture. This aligns with the company's "
            "technical needs and product development requirements."
        )
    elif bu == BusinessUnit.CUSTOM_SOFTWARE:
        return (
            "Inowix Custom Software delivers business-specific solutions — ERP, CRM, "
            "AI automation, legacy modernization, and custom web applications. This "
            "aligns with the company's operational needs."
        )
    return "Inowix has relevant services for this opportunity."


def _generate_pitch(bu: BusinessUnit, intent: IntentLevel, text: str) -> str:
    if intent == IntentLevel.ACTIVE_REQUIREMENT:
        if bu == BusinessUnit.COMAI:
            return (
                "Lead with: 'We help D2C brands automate their customer operations "
                "with AI. Based on what you're looking for, we can help with [specific "
                "need]. Would you be open to a quick call to discuss how we've helped "
                "similar brands?'"
            )
        elif bu == BusinessUnit.SAAS_DEVELOPMENT:
            return (
                "Lead with: 'We help SaaS founders build and scale their products. "
                "We've built [similar product]. Based on your requirements, we can "
                "start with an MVP or provide a dedicated team. Can we discuss your "
                "technical needs?'"
            )
        else:
            return (
                "Lead with: 'We help businesses build custom software solutions "
                "tailored to their operations. Based on your requirements, we can "
                "deliver [specific solution]. Would you be open to a quick call?'"
            )
    elif intent == IntentLevel.EVALUATION:
        return (
            "Lead with: 'We noticed you're exploring solutions. We've helped similar "
            "companies with [specific outcome]. Happy to share our approach and see "
            "if we're a good fit. Open to a 15-minute call?'"
        )
    elif intent == IntentLevel.EARLY_INTENT:
        return (
            "Lead with: 'We work with companies facing similar challenges. We helped "
            "[similar company] solve [specific problem] with [specific solution]. "
            "Would it be helpful to see how?'"
        )
    else:
        return (
            "Lead with: 'We help companies like yours with [specific service]. "
            "I noticed [specific trigger]. Would you be open to learning more?'"
        )


def _generate_why_now(intent: IntentLevel, opp: Opportunity) -> str:
    reasons = []
    if intent == IntentLevel.ACTIVE_REQUIREMENT:
        reasons.append("They have an active requirement — first responder advantage")
    if intent == IntentLevel.EVALUATION:
        reasons.append("They're actively evaluating — they'll decide soon")
    for e in opp.evidence:
        if any(kw in e.claim.lower() for kw in ["funded", "raised", "new launch"]):
            reasons.append(f"Recent trigger: {e.claim}")
            break
    if not reasons:
        reasons.append("Profile matches ICP — no urgency signal, but early engagement builds relationship")
    return "; ".join(reasons[:2])


def _generate_objection(bu: BusinessUnit, text: str) -> str:
    if bu == BusinessUnit.COMAI:
        return "May already have basic automation (Shopify built-ins, third-party apps). Position COMAI as AI-native upgrade."
    elif bu == BusinessUnit.SAAS_DEVELOPMENT:
        return "May be evaluating freelancers, agencies, or in-house hires. Position as specialized SaaS partner with relevant experience."
    elif bu == BusinessUnit.CUSTOM_SOFTWARE:
        return "May prefer off-the-shelf solutions. Position as custom-built alternative when off-the-shelf doesn't fit."
    return "Unknown objection profile."


def _generate_cta(bu: BusinessUnit, intent: IntentLevel) -> str:
    if intent == IntentLevel.ACTIVE_REQUIREMENT:
        return "Book a 15-minute technical discovery call"
    elif intent == IntentLevel.EVALUATION:
        return "Share case study + offer comparison call"
    elif intent == IntentLevel.EARLY_INTENT:
        return "Send educational content + invite to webinar/demo"
    else:
        return "Connect on LinkedIn + follow up in 30 days"
