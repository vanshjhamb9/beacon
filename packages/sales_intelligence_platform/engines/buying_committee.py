"""Buying Committee Engine - Determine likely stakeholders for COMAI sale."""

from __future__ import annotations

from packages.sales_intelligence_platform.models import BuyingCommittee, DecisionMaker


def build_buying_committee(
    lead_data: dict, decision_makers: list[DecisionMaker]
) -> BuyingCommittee:
    """Build the likely buying committee based on company signals."""
    committee = BuyingCommittee()

    # Determine trigger
    committee.trigger = _detect_trigger(lead_data)

    # Map decision makers to committee roles
    for dm in decision_makers:
        role_lower = dm.normalized_role.lower()
        if "founder" in role_lower or "ceo" in role_lower or "owner" in role_lower:
            committee.founder = dm.name
        elif "operation" in role_lower:
            committee.operations = dm.name
        elif "technology" in role_lower or "cto" in role_lower or "engineering" in role_lower:
            committee.technology = dm.name
        elif "growth" in role_lower or "marketing" in role_lower:
            committee.growth = dm.name
        elif "support" in role_lower or "customer" in role_lower:
            committee.operations = dm.name or committee.operations

    committee.members = [
        {"role": "Founder/CEO", "name": committee.founder},
        {"role": "Operations", "name": committee.operations},
        {"role": "Technology", "name": committee.technology},
        {"role": "Growth/Marketing", "name": committee.growth},
    ]
    committee.members = [m for m in committee.members if m["name"]]

    committee.confidence = _calculate_committee_confidence(committee, decision_makers)
    committee.evidence = [
        f"Trigger: {committee.trigger}",
        f"Members identified: {len(committee.members)}",
    ]

    return committee


def _detect_trigger(lead_data: dict) -> str:
    """Detect what trigger would drive a COMAI purchase."""
    product_count = lead_data.get("product_count", 0)
    has_chatbot = lead_data.get("chatbot_detected", False)
    has_whatsapp = lead_data.get("whatsapp_detected", False)
    has_crm = lead_data.get("crm_detected", False)

    if product_count >= 100 and not has_chatbot:
        return "scaling_support"
    if has_whatsapp and not has_crm:
        return "whatsapp_automation"
    if not has_chatbot and not has_crm:
        return "support_gap"
    if product_count >= 50:
        return "catalog_growth"
    return "general_pain"


def _calculate_committee_confidence(
    committee: BuyingCommittee, decision_makers: list[DecisionMaker]
) -> float:
    """Calculate confidence in the buying committee."""
    score = 0.0
    if committee.founder:
        score += 40.0
    if committee.operations:
        score += 20.0
    if committee.technology:
        score += 20.0
    if committee.growth:
        score += 10.0
    if committee.trigger != "general_pain":
        score += 10.0
    return min(100.0, score)
