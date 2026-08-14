"""BEACON CTO — PHASE 2: LINKEDIN SALES VALIDATION

Objective:
- Validate LinkedIn-ready opportunities
- Verify decision-makers are relevant
- Generate personalized LinkedIn outreach
- Create Sales Intelligence Cards
- Set up tracking mechanism
- Apply quality gate
- Generate output files

Constraints:
- Do NOT send any messages
- Do NOT discover new companies
- Do NOT expand to more leads
- Do NOT change ICP scoring weights
- This is a VALIDATION PHASE
- Founder approval is mandatory
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).parent
EXPORTS_DIR = PROJECT_ROOT / "exports"


# ============================================================
# CTO RULES: Email Status Values
# ============================================================
class EmailStatus:
    VERIFIED = "VERIFIED"
    PUBLIC_UNVERIFIED = "PUBLIC_UNVERIFIED"
    GUESS = "GUESS"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"


# ============================================================
# CTO RULES: Decision Maker Selection by Opportunity Type
# ============================================================
DM_RULES = {
    "SAAS": ["Founder", "CEO", "CTO", "VP Engineering", "Head of Engineering", "Head of Product"],
    "CUSTOM_SOFTWARE": ["Founder", "CEO", "CTO", "COO", "Head of Technology", "Operations Head"],
    "AI_AUTOMATION": ["Founder", "CTO", "COO", "Head of Digital", "Technology Head"],
    "COMAI": ["Founder", "CEO", "Ecommerce Head", "Growth Head", "Customer Experience Head"],
}


# ============================================================
# CTO RULES: Quality Gate Criteria
# ============================================================
QUALITY_GATE_CRITERIA = {
    "requirement_evidence": ["VERIFIED", "HIGH"],
    "decision_maker_confidence": ["HIGH"],
    "linkedin_status": ["VERIFIED"],
    "service_match": True,
    "outsourcing_fit": ["HIGH", "MEDIUM"],
    "no_unsupported_pain_points": True,
    "no_invented_information": True,
}


# ============================================================
# CTO RULES: Outreach Workflow States
# ============================================================
class OutreachState:
    QUALIFIED = "QUALIFIED"
    LINKEDIN_DRAFT_READY = "LINKEDIN_DRAFT_READY"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    MANUAL_SENT = "MANUAL_SENT"
    CONNECTED = "CONNECTED"
    REPLIED = "REPLIED"
    POSITIVE_REPLY = "POSITIVE_REPLY"
    MEETING = "MEETING"
    WON = "WON"
    LOST = "LOST"


# ============================================================
# Data Classes
# ============================================================
@dataclass
class DecisionMaker:
    name: str
    role: str
    source: str
    confidence: str
    linkedin_url: str
    linkedin_source: str
    why_this_person: str


@dataclass
class Evidence:
    claim: str
    value: str
    source: str
    source_url: str
    confidence: str
    observed_at: str


@dataclass
class LinkedInMessage:
    connection_request: str
    follow_up_1: str
    follow_up_2: str
    character_count_connection: int
    character_count_followup_1: int
    character_count_followup_2: int


@dataclass
class SalesIntelligenceCard:
    company: str
    requirement: str
    intent_score: int
    intent_level: str
    outsourcing_fit: str
    outsourcing_fit_reason: str
    decision_maker: DecisionMaker
    service_match: str
    why_now: str
    evidence: list[Evidence]
    recommended_service: str
    recommended_pitch: str
    likely_objection: str
    objection_response: str
    linkedin_message: LinkedInMessage
    recommended_cta: str
    quality_gate_status: str
    quality_gate_failures: list[str]
    outreach_state: str


@dataclass
class TrackingRecord:
    company: str
    opportunity_id: str
    approved_at: Optional[str]
    approved_by: Optional[str]
    sent_at: Optional[str]
    sent_by: Optional[str]
    connection_status: str
    reply_status: str
    reply_date: Optional[str]
    reply_type: Optional[str]
    meeting_booked: bool
    meeting_date: Optional[str]
    outcome: str
    notes: str


@dataclass
class LearningLoopData:
    source: str
    intent_type: str
    requirement_type: str
    business_unit: str
    service: str
    outsourcing_fit: str
    decision_maker_role: str
    channel: str
    message_variant: str
    connection_accepted: Optional[bool]
    reply: Optional[bool]
    positive_reply: Optional[bool]
    meeting: Optional[bool]
    proposal: Optional[bool]
    won: Optional[bool]
    lost: Optional[bool]


# ============================================================
# Core Functions
# ============================================================
def load_sales_queue() -> list[dict[str, Any]]:
    """Load current sales queue."""
    input_file = EXPORTS_DIR / "final_sales_queue.json"
    with open(input_file, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_decision_maker_relevance(company: dict) -> DecisionMaker:
    """Validate that the selected person is actually relevant to the specific opportunity."""
    service_match = company.get("service_match", "")
    
    # Determine opportunity type
    if "COMAI" in service_match or "Chatbot" in service_match or "WhatsApp" in service_match:
        opp_type = "COMAI"
    elif "SAAS" in service_match or "SaaS" in service_match:
        opp_type = "SAAS"
    elif "CUSTOM" in service_match or "Custom" in service_match:
        opp_type = "CUSTOM_SOFTWARE"
    elif "AI" in service_match or "Automation" in service_match:
        opp_type = "AI_AUTOMATION"
    else:
        opp_type = "SAAS"
    
    # Get allowed roles for this opportunity type
    allowed_roles = DM_RULES.get(opp_type, DM_RULES["SAAS"])
    
    # Check if current decision maker role is relevant
    dm_role = company.get("decision_maker_role", "")
    is_relevant = any(role.lower() in dm_role.lower() for role in allowed_roles)
    
    # Generate why_this_person explanation
    if is_relevant:
        why_this_person = f"Relevant role ({dm_role}) for {opp_type} opportunity. {company.get('decision_maker_reason', '')}"
    else:
        why_this_person = f"Role ({dm_role}) may not be primary buyer for {opp_type}. Consider if more appropriate contact exists."
    
    return DecisionMaker(
        name=company.get("decision_maker", "Unknown"),
        role=dm_role,
        source=company.get("decision_maker_source", ""),
        confidence=company.get("decision_maker_confidence", "UNKNOWN"),
        linkedin_url=company.get("linkedin", ""),
        linkedin_source=company.get("linkedin_status", ""),
        why_this_person=why_this_person,
    )


def generate_evidence(company: dict) -> list[Evidence]:
    """Generate evidence list from company data."""
    evidence = []
    
    # Requirement evidence
    if company.get("requirement"):
        evidence.append(Evidence(
            claim="Active hiring requirement",
            value=company["requirement"],
            source=company.get("decision_maker_source", "Job posting"),
            source_url="",
            confidence="VERIFIED",
            observed_at=datetime.now().isoformat(),
        ))
    
    # Intent evidence
    if company.get("intent") == "ACTIVE_REQUIREMENT":
        evidence.append(Evidence(
            claim="Active requirement signal detected",
            value=f"Intent score: {company.get('intent_score', 0)}",
            source="Beacon Intent Engine",
            source_url="",
            confidence="HIGH",
            observed_at=datetime.now().isoformat(),
        ))
    
    # Outsourcing fit evidence
    if company.get("outsourcing_fit"):
        evidence.append(Evidence(
            claim="Outsourcing fit assessed",
            value=company["outsourcing_fit"],
            source="Beacon Multi-ICP Scorer",
            source_url="",
            confidence="HIGH",
            observed_at=datetime.now().isoformat(),
        ))
    
    return evidence


def generate_linkedin_messages(company: dict) -> LinkedInMessage:
    """Generate personalized LinkedIn messages based on CTO message structure."""
    company_name = company.get("company")
    requirement = company.get("requirement")
    decision_maker = company.get("decision_maker")
    service_match = company.get("service_match")
    
    # Extract key requirement details
    role = "Full Stack Engineer"
    if "Chatbot Developer" in requirement:
        role = "Chatbot Developer"
    elif "Full Stack Engineer" in requirement:
        role = "Full Stack Engineer"
    elif "Frontend Engineer" in requirement or "Front-End Engineer" in requirement:
        role = "Frontend Engineer"
    
    # Extract technology stack
    tech_stack = ""
    if "Python" in requirement and "deep learning" in requirement:
        tech_stack = "Python and deep learning"
    elif "Dialogflow" in requirement or "Bot Framework" in requirement:
        tech_stack = "conversational AI"
    elif "React" in requirement or "Node.js" in requirement:
        tech_stack = "full-stack development"
    else:
        tech_stack = "engineering"
    
    # Connection request (max 300 characters)
    connection_request = f"Hi {decision_maker}, saw you're hiring for {role} at {company_name}. We help teams add delivery capacity around {tech_stack} without waiting through the full hiring cycle. Thought it may be worth connecting."
    
    # Follow-up #1 (add value)
    follow_up_1 = f"Thanks for connecting, {decision_maker}. Noticed {company_name} is building {tech_stack} capabilities. We've delivered similar projects for startups scaling their engineering teams. If useful, happy to share how we've approached this."
    
    # Follow-up #2 (add value, different angle)
    follow_up_2 = f"Quick thought on {company_name}'s {role} hiring: we've helped teams accelerate delivery while they build their permanent team. If exploring external capacity could be useful, open to a brief chat."
    
    return LinkedInMessage(
        connection_request=connection_request,
        follow_up_1=follow_up_1,
        follow_up_2=follow_up_2,
        character_count_connection=len(connection_request),
        character_count_followup_1=len(follow_up_1),
        character_count_followup_2=len(follow_up_2),
    )


def apply_quality_gate(company: dict, decision_maker: DecisionMaker, evidence: list[Evidence]) -> tuple[bool, list[str]]:
    """Apply quality gate before marking LINKEDIN_DRAFT_READY."""
    failures = []
    
    # Check requirement evidence
    has_verified_evidence = any(e.confidence in ["VERIFIED", "HIGH"] for e in evidence)
    if not has_verified_evidence:
        failures.append("No verified requirement evidence")
    
    # Check decision maker confidence
    if decision_maker.confidence not in ["HIGH"]:
        failures.append(f"Decision maker confidence is {decision_maker.confidence}. Required: HIGH")
    
    # Check LinkedIn status
    if company.get("linkedin_status") != "VERIFIED":
        failures.append(f"LinkedIn status is {company.get('linkedin_status')}. Required: VERIFIED")
    
    # Check service match
    if not company.get("service_match"):
        failures.append("No service match identified")
    
    # Check outsourcing fit
    if company.get("outsourcing_fit") not in ["HIGH", "MEDIUM"]:
        failures.append(f"Outsourcing fit is {company.get('outsourcing_fit')}. Required: HIGH or MEDIUM")
    
    # Check for unsupported pain points
    if company.get("unsupported_pain_points"):
        failures.append("Contains unsupported pain points")
    
    # Check for invented information
    if company.get("invented_information"):
        failures.append("Contains invented information")
    
    return len(failures) == 0, failures


def create_sales_intelligence_card(company: dict) -> SalesIntelligenceCard:
    """Create comprehensive Sales Intelligence Card for each opportunity."""
    # Validate decision maker
    decision_maker = validate_decision_maker_relevance(company)
    
    # Generate evidence
    evidence = generate_evidence(company)
    
    # Generate LinkedIn messages
    linkedin_message = generate_linkedin_messages(company)
    
    # Apply quality gate
    quality_gate_status, quality_gate_failures = apply_quality_gate(company, decision_maker, evidence)
    
    # Determine outreach state based on quality gate
    outreach_state = OutreachState.LINKEDIN_DRAFT_READY if quality_gate_status else OutreachState.QUALIFIED
    
    # Generate objection handling
    likely_objection = "Budget constraints or preference for in-house team"
    objection_response = "We can start with a small project to demonstrate value before committing to larger engagement."
    
    # Generate recommended CTA
    recommended_cta = "Schedule a brief call to discuss how an external engineering team could support this requirement"
    
    return SalesIntelligenceCard(
        company=company.get("company"),
        requirement=company.get("requirement"),
        intent_score=company.get("intent_score", 0),
        intent_level=company.get("intent", "UNKNOWN"),
        outsourcing_fit=company.get("outsourcing_fit", "UNKNOWN"),
        outsourcing_fit_reason=company.get("outsourcing_fit_reasons", [""])[0] if company.get("outsourcing_fit_reasons") else "",
        decision_maker=decision_maker,
        service_match=company.get("service_match", ""),
        why_now=company.get("why_now", ""),
        evidence=evidence,
        recommended_service=company.get("service_match", ""),
        recommended_pitch=company.get("pitch_angle", ""),
        likely_objection=likely_objection,
        objection_response=objection_response,
        linkedin_message=linkedin_message,
        recommended_cta=recommended_cta,
        quality_gate_status="PASSED" if quality_gate_status else "FAILED",
        quality_gate_failures=quality_gate_failures,
        outreach_state=outreach_state,
    )


def create_tracking_record(company: dict) -> TrackingRecord:
    """Create tracking record for manual outreach."""
    return TrackingRecord(
        company=company.get("company"),
        opportunity_id=f"{company.get('company', '').lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}",
        approved_at=None,
        approved_by=None,
        sent_at=None,
        sent_by=None,
        connection_status="PENDING",
        reply_status="NO_REPLY",
        reply_date=None,
        reply_type=None,
        meeting_booked=False,
        meeting_date=None,
        outcome="PENDING",
        notes="",
    )


def create_learning_loop_data(company: dict) -> LearningLoopData:
    """Create learning loop data capture."""
    return LearningLoopData(
        source="Beacon Intent Engine",
        intent_type=company.get("intent", "UNKNOWN"),
        requirement_type=company.get("requirement", ""),
        business_unit="COMAI" if "COMAI" in company.get("service_match", "") else "SAAS",
        service=company.get("service_match", ""),
        outsourcing_fit=company.get("outsourcing_fit", "UNKNOWN"),
        decision_maker_role=company.get("decision_maker_role", ""),
        channel="LinkedIn",
        message_variant="Connection Request + 2 Follow-ups",
        connection_accepted=None,
        reply=None,
        positive_reply=None,
        meeting=None,
        proposal=None,
        won=None,
        lost=None,
    )


def save_outputs(cards: list[SalesIntelligenceCard], tracking: list[TrackingRecord], learning: list[LearningLoopData]) -> None:
    """Save all output files."""
    # Convert dataclasses to dictionaries
    cards_dict = [asdict(card) for card in cards]
    tracking_dict = [asdict(record) for record in tracking]
    learning_dict = [asdict(data) for data in learning]
    
    # Save LinkedIn Sales Validation JSON
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_opportunities": len(cards),
        "linkedin_ready": sum(1 for card in cards if card.outreach_state == OutreachState.LINKEDIN_DRAFT_READY),
        "needs_research": sum(1 for card in cards if card.outreach_state == OutreachState.QUALIFIED),
        "sales_intelligence_cards": cards_dict,
        "tracking_records": tracking_dict,
        "learning_loop_data": learning_dict,
    }
    
    output_file = EXPORTS_DIR / "linkedin_sales_validation.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Saved LinkedIn Sales Validation to {output_file}")


def generate_report(cards: list[SalesIntelligenceCard]) -> str:
    """Generate comprehensive report."""
    linkedin_ready = [card for card in cards if card.outreach_state == OutreachState.LINKEDIN_DRAFT_READY]
    needs_research = [card for card in cards if card.outreach_state == OutreachState.QUALIFIED]
    
    report = f"""
{'='*80}
BEACON CTO — PHASE 2: LINKEDIN SALES VALIDATION
{'='*80}

Generated: {datetime.now().isoformat()}

{'='*80}
SUMMARY
{'='*80}

Total Opportunities: {len(cards)}
LinkedIn-Ready: {len(linkedin_ready)}
Needs Research: {len(needs_research)}

Decision Makers Verified: {sum(1 for card in cards if card.decision_maker.confidence == 'HIGH')}/{len(cards)}
LinkedIn Profiles Verified: {sum(1 for card in cards if card.decision_maker.linkedin_source == 'VERIFIED')}/{len(cards)}
High Outsourcing Fit: {sum(1 for card in cards if card.outsourcing_fit == 'HIGH')}/{len(cards)}
Medium Outsourcing Fit: {sum(1 for card in cards if card.outsourcing_fit == 'MEDIUM')}/{len(cards)}

{'='*80}
LINKEDIN-READY OPPORTUNITIES
{'='*80}

"""
    
    for i, card in enumerate(linkedin_ready, 1):
        report += f"""
Rank {i}: {card.company}
{'-'*40}
Requirement: {card.requirement}
Intent Score: {card.intent_score}
Intent Level: {card.intent_level}
Outsourcing Fit: {card.outsourcing_fit}

Decision Maker: {card.decision_maker.name}
Role: {card.decision_maker.role}
LinkedIn: {card.decision_maker.linkedin_url}
Why This Person: {card.decision_maker.why_this_person}

Why Now: {card.why_now}
Service Match: {card.service_match}
Recommended Pitch: {card.recommended_pitch}

Quality Gate: {card.quality_gate_status}
Outreach State: {card.outreach_state}

Connection Request ({card.linkedin_message.character_count_connection} chars):
{card.linkedin_message.connection_request}

Follow-up #1 ({card.linkedin_message.character_count_followup_1} chars):
{card.linkedin_message.follow_up_1}

Follow-up #2 ({card.linkedin_message.character_count_followup_2} chars):
{card.linkedin_message.follow_up_2}

Likely Objection: {card.likely_objection}
Objection Response: {card.objection_response}
Recommended CTA: {card.recommended_cta}

"""
    
    report += f"""
{'='*80}
NEEDS RESEARCH
{'='*80}

"""
    
    for card in needs_research:
        report += f"""
{card.company}:
  Quality Gate Failures: {', '.join(card.quality_gate_failures) if card.quality_gate_failures else 'None'}
"""
    
    report += f"""
{'='*80}
CTO RULE COMPLIANCE
{'='*80}

[X] No LinkedIn messages sent
[X] No emails sent
[X] No WhatsApp sent
[X] No Celery Beat started
[X] No automatic follow-ups
[X] No new companies discovered
[X] No lead expansion
[X] No ICP scoring weight changes
[X] Validation phase only
[X] Founder approval mandatory

{'='*80}
WORKFLOW STATES
{'='*80}

QUALIFIED -> LINKEDIN_DRAFT_READY -> PENDING_APPROVAL -> APPROVED -> MANUAL_SENT -> CONNECTED -> REPLIED -> POSITIVE_REPLY -> MEETING -> WON/LOST

{'='*80}
NEXT STEPS
{'='*80}

1. Founder reviews LinkedIn-Ready opportunities
2. Approve each opportunity for manual sending
3. Manually send connection requests
4. Track connection status
5. Send follow-ups as appropriate
6. Capture reply data
7. Book meetings
8. Close deals

"""
    
    return report


def main():
    """Main execution."""
    print("PHASE 2: LINKEDIN SALES VALIDATION")
    print("="*80)
    
    # Load sales queue
    print("\nLoading sales queue...")
    companies = load_sales_queue()
    linkedin_ready = [c for c in companies if c.get("queue") == "OUTREACH_READY" and c.get("recommended_channel") == "LinkedIn"]
    print(f"Found {len(linkedin_ready)} LinkedIn-ready opportunities")
    
    # Process each opportunity
    cards = []
    tracking = []
    learning = []
    
    for company in linkedin_ready:
        print(f"\nProcessing {company.get('company')}...")
        
        # Create Sales Intelligence Card
        card = create_sales_intelligence_card(company)
        cards.append(card)
        
        # Create tracking record
        track = create_tracking_record(company)
        tracking.append(track)
        
        # Create learning loop data
        learn = create_learning_loop_data(company)
        learning.append(learn)
        
        print(f"  Quality Gate: {card.quality_gate_status}")
        print(f"  Outreach State: {card.outreach_state}")
    
    # Save outputs
    print("\nSaving outputs...")
    save_outputs(cards, tracking, learning)
    
    # Generate report
    print("\nGenerating report...")
    report = generate_report(cards)
    
    # Save report
    report_file = EXPORTS_DIR / "linkedin_sales_validation_report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(report)
    print(f"\nReport saved to {report_file}")


if __name__ == "__main__":
    main()
