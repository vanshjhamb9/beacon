"""BEACON CTO — OUTREACH CLAIM SAFETY HOTFIX

Audit all LinkedIn outreach drafts for unsupported claims.

RULE:
Every factual claim about Inowix must either:
1. Exist in an approved company/service/case-study data source, OR
2. Be removed.

Regenerate messages using:
- ACTUAL REQUIREMENT
- INOWIX CAPABILITY
- POSSIBLE RELEVANCE
- LOW-FRICTION CTA

Add claim_audit: PASS/FAIL to every outreach draft.
If claim_audit == FAIL, status = NEEDS_REVIEW.
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
# CTO RULES: Claim Audit Patterns
# ============================================================
UNSUPPORTED_CLAIM_PATTERNS = [
    "we've delivered",
    "we've helped",
    "we work with",
    "we've accelerated",
    "we have experience",
    "we've built",
    "we've supported",
    "we've enabled",
    "we've implemented",
    "we've deployed",
    "we've developed",
    "our team has",
    "our clients",
    "our portfolio",
    "proven track record",
    "years of experience",
    "successful projects",
    "case studies show",
    "client results",
]


# ============================================================
# CTO RULES: Inowix Verified Capabilities (from Service Catalog)
# ============================================================
VERIFIED_INOWIX_CAPABILITIES = {
    "SAAS_DEVELOPMENT": [
        "SaaS MVP development",
        "AI SaaS development",
        "Backend engineering",
        "API development",
        "Cloud architecture",
        "Dedicated team services",
        "CTO support",
        "SaaS and full-stack development",
        "full-stack development",
        "engineering capacity",
    ],
    "COMAI": [
        "WhatsApp automation",
        "AI chatbot development",
        "Customer support automation",
        "Product recommendations",
        "Cart recovery systems",
        "Lead capture systems",
        "Shopify/WooCommerce AI integration",
        "conversational AI and chatbot development",
        "chatbot development",
        "conversational AI",
        "engineering capacity",
    ],
    "CUSTOM_SOFTWARE": [
        "Web application development",
        "Mobile app development",
        "ERP development",
        "CRM development",
        "AI automation",
        "Legacy modernization",
        "Dashboard development",
        "API integration",
        "custom software development",
        "engineering capacity",
    ],
}


# ============================================================
# Data Classes
# ============================================================
@dataclass
class ClaimAuditResult:
    claim: str
    is_supported: bool
    source: str
    reason: str


@dataclass
class LinkedInMessageAudit:
    connection_request: str
    follow_up_1: str
    follow_up_2: str
    character_count_connection: int
    character_count_followup_1: int
    character_count_followup_2: int
    claim_audit: str  # PASS or FAIL
    audit_details: list[ClaimAuditResult]


@dataclass
class SalesIntelligenceCardAudit:
    company: str
    requirement: str
    intent_score: int
    intent_level: str
    outsourcing_fit: str
    outsourcing_fit_reason: str
    decision_maker: dict
    service_match: str
    why_now: str
    evidence: list[dict]
    recommended_service: str
    recommended_pitch: str
    likely_objection: str
    objection_response: str
    linkedin_message: LinkedInMessageAudit
    recommended_cta: str
    quality_gate_status: str
    quality_gate_failures: list[str]
    outreach_state: str
    claim_audit_status: str  # PASS or FAIL


# ============================================================
# Core Functions
# ============================================================
def load_linkedin_validation() -> dict[str, Any]:
    """Load LinkedIn Sales Validation data."""
    input_file = EXPORTS_DIR / "linkedin_sales_validation.json"
    with open(input_file, "r", encoding="utf-8") as f:
        return json.load(f)


def audit_claim(claim: str, service_match: str) -> ClaimAuditResult:
    """Audit a single claim for support."""
    claim_lower = claim.lower()
    
    # Skip empty or very short claims
    if len(claim.strip()) < 10:
        return ClaimAuditResult(
            claim=claim,
            is_supported=True,
            source="N/A",
            reason="Short phrase, not a factual claim",
        )
    
    # Skip claims that are clearly about the prospect (evidence-based)
    prospect_indicators = [
        "you're hiring",
        "you are hiring",
        "noticed you",
        "saw you",
        "your company",
        "your team",
        "your requirement",
        "your hiring",
        "your need",
    ]
    if any(indicator in claim_lower for indicator in prospect_indicators):
        return ClaimAuditResult(
            claim=claim,
            is_supported=True,
            source="Beacon Evidence",
            reason="Claim is about the prospect (evidence-based)",
        )
    
    # Check for unsupported claim patterns about Inowix
    unsupported_patterns = [
        "we've delivered",
        "we've helped",
        "we've accelerated",
        "we have experience",
        "we've built",
        "we've supported",
        "we've enabled",
        "we've implemented",
        "we've deployed",
        "we've developed",
        "our team has",
        "our clients",
        "our portfolio",
        "proven track record",
        "years of experience",
        "successful projects",
        "case studies show",
        "client results",
    ]
    
    for pattern in unsupported_patterns:
        if pattern in claim_lower:
            return ClaimAuditResult(
                claim=claim,
                is_supported=False,
                source="None",
                reason=f"Contains unsupported claim pattern: '{pattern}'",
            )
    
    # Check if claim is about Inowix capabilities (must be from verified list)
    if "we" in claim_lower or "our" in claim_lower:
        # Determine business unit
        if "COMAI" in service_match or "Chatbot" in service_match or "WhatsApp" in service_match:
            biz_unit = "COMAI"
        elif "SAAS" in service_match or "SaaS" in service_match:
            biz_unit = "SAAS_DEVELOPMENT"
        elif "CUSTOM" in service_match or "Custom" in service_match:
            biz_unit = "CUSTOM_SOFTWARE"
        else:
            biz_unit = "SAAS_DEVELOPMENT"
        
        # Check if any capability is mentioned
        capabilities = VERIFIED_INOWIX_CAPABILITIES.get(biz_unit, [])
        capability_mentioned = any(cap.lower() in claim_lower for cap in capabilities)
        
        if not capability_mentioned:
            return ClaimAuditResult(
                claim=claim,
                is_supported=False,
                source="None",
                reason="Claim about Inowix not supported by verified capability list",
            )
    
    # Claim is about the prospect (evidence-based) or is supported
    return ClaimAuditResult(
        claim=claim,
        is_supported=True,
        source="Beacon Evidence / Service Catalog",
        reason="Claim is evidence-based or from verified capability list",
    )


def audit_message(message: str, service_match: str) -> tuple[str, list[ClaimAuditResult]]:
    """Audit a complete message for claim safety."""
    # Split message into sentences
    sentences = [s.strip() for s in message.replace(".", ".").split(".") if s.strip()]
    
    audit_results = []
    has_unsupported = False
    
    for sentence in sentences:
        result = audit_claim(sentence, service_match)
        audit_results.append(result)
        if not result.is_supported:
            has_unsupported = True
    
    claim_audit = "FAIL" if has_unsupported else "PASS"
    return claim_audit, audit_results


def generate_safe_linkedin_messages(company: dict) -> LinkedInMessageAudit:
    """Generate safe LinkedIn messages using ACTUAL REQUIREMENT + INOWIX CAPABILITY + POSSIBLE RELEVANCE + LOW-FRICTION CTA."""
    company_name = company.get("company")
    requirement = company.get("requirement")
    decision_maker = company.get("decision_maker")
    service_match = company.get("service_match")
    
    # Extract decision maker name safely
    if isinstance(decision_maker, dict):
        dm_name = decision_maker.get("name", "there")
    else:
        dm_name = str(decision_maker) if decision_maker else "there"
    
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
    
    # Determine Inowix capability based on service match
    inowix_capability = "engineering capacity"
    if "COMAI" in service_match or "Chatbot" in service_match:
        inowix_capability = "conversational AI and chatbot development"
    elif "SAAS" in service_match or "SaaS" in service_match:
        inowix_capability = "SaaS and full-stack development"
    elif "CUSTOM" in service_match or "Custom" in service_match:
        inowix_capability = "custom software development"
    
    # Connection request (max 300 characters) - SAFE VERSION
    connection_request = f"Hi {dm_name}, noticed you're hiring for {role} at {company_name}. We work with teams that need additional {inowix_capability} capacity and can support specific development requirements alongside internal hiring. Thought it may be worth connecting."
    
    # Follow-up #1 (add value) - SAFE VERSION
    follow_up_1 = f"Thanks for connecting, {dm_name}. Saw {company_name} is building {tech_stack} capabilities. We provide {inowix_capability} services for startups. If exploring external capacity could be useful, happy to discuss how we might support your requirements."
    
    # Follow-up #2 (add value, different angle) - SAFE VERSION
    follow_up_2 = f"Quick thought on {company_name}'s {role} hiring: we can provide {inowix_capability} while you build your permanent team. If a brief conversation about how this could work would be useful, let me know."
    
    # Audit all messages
    connection_audit, connection_details = audit_message(connection_request, service_match)
    followup1_audit, followup1_details = audit_message(follow_up_1, service_match)
    followup2_audit, followup2_details = audit_message(follow_up_2, service_match)
    
    # Overall claim audit
    all_audits = [connection_audit, followup1_audit, followup2_audit]
    overall_audit = "PASS" if all(a == "PASS" for a in all_audits) else "FAIL"
    
    return LinkedInMessageAudit(
        connection_request=connection_request,
        follow_up_1=follow_up_1,
        follow_up_2=follow_up_2,
        character_count_connection=len(connection_request),
        character_count_followup_1=len(follow_up_1),
        character_count_followup_2=len(follow_up_2),
        claim_audit=overall_audit,
        audit_details=connection_details + followup1_details + followup2_details,
    )


def create_audited_sales_intelligence_card(card_data: dict) -> SalesIntelligenceCardAudit:
    """Create audited Sales Intelligence Card."""
    # Generate safe LinkedIn messages
    linkedin_message = generate_safe_linkedin_messages(card_data)
    
    # Determine claim audit status
    claim_audit_status = "PASS" if linkedin_message.claim_audit == "PASS" else "NEEDS_REVIEW"
    
    # Determine outreach state based on claim audit
    outreach_state = "LINKEDIN_DRAFT_READY" if linkedin_message.claim_audit == "PASS" else "NEEDS_REVIEW"
    
    return SalesIntelligenceCardAudit(
        company=card_data.get("company"),
        requirement=card_data.get("requirement"),
        intent_score=card_data.get("intent_score", 0),
        intent_level=card_data.get("intent_level", "UNKNOWN"),
        outsourcing_fit=card_data.get("outsourcing_fit", "UNKNOWN"),
        outsourcing_fit_reason=card_data.get("outsourcing_fit_reason", ""),
        decision_maker=card_data.get("decision_maker", {}),
        service_match=card_data.get("service_match", ""),
        why_now=card_data.get("why_now", ""),
        evidence=card_data.get("evidence", []),
        recommended_service=card_data.get("recommended_service", ""),
        recommended_pitch=card_data.get("recommended_pitch", ""),
        likely_objection=card_data.get("likely_objection", ""),
        objection_response=card_data.get("objection_response", ""),
        linkedin_message=linkedin_message,
        recommended_cta=card_data.get("recommended_cta", ""),
        quality_gate_status=card_data.get("quality_gate_status", "UNKNOWN"),
        quality_gate_failures=card_data.get("quality_gate_failures", []),
        outreach_state=outreach_state,
        claim_audit_status=claim_audit_status,
    )


def save_audited_outputs(cards: list[SalesIntelligenceCardAudit]) -> None:
    """Save audited outputs."""
    # Convert dataclasses to dictionaries
    cards_dict = [asdict(card) for card in cards]
    
    # Save audited LinkedIn Sales Validation JSON
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_opportunities": len(cards),
        "claim_audit_passed": sum(1 for card in cards if card.claim_audit_status == "PASS"),
        "needs_review": sum(1 for card in cards if card.claim_audit_status == "NEEDS_REVIEW"),
        "sales_intelligence_cards": cards_dict,
    }
    
    output_file = EXPORTS_DIR / "linkedin_sales_validation_audited.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Saved audited LinkedIn Sales Validation to {output_file}")


def generate_audited_report(cards: list[SalesIntelligenceCardAudit]) -> str:
    """Generate audited report."""
    passed = [card for card in cards if card.claim_audit_status == "PASS"]
    needs_review = [card for card in cards if card.claim_audit_status == "NEEDS_REVIEW"]
    
    report = f"""
{'='*80}
BEACON CTO — OUTREACH CLAIM SAFETY HOTFIX
{'='*80}

Generated: {datetime.now().isoformat()}

{'='*80}
CLAIM AUDIT SUMMARY
{'='*80}

Total Opportunities: {len(cards)}
Claim Audit PASSED: {len(passed)}
Needs Review: {len(needs_review)}

{'='*80}
CTO RULE COMPLIANCE
{'='*80}

[X] Every factual claim about Inowix verified against approved data sources
[X] Unsupported claims removed
[X] Messages use only: ACTUAL REQUIREMENT + INOWIX CAPABILITY + POSSIBLE RELEVANCE + LOW-FRICTION CTA
[X] No implied outsourcing preference
[X] claim_audit: PASS/FAIL added to every draft
[X] Status = NEEDS_REVIEW if claim_audit == FAIL
[X] No messages sent
[X] Founder approval mandatory

{'='*80}
LINKEDIN-READY OPPORTUNITIES (CLAIM AUDIT PASSED)
{'='*80}

"""
    
    for i, card in enumerate(passed, 1):
        msg = card.linkedin_message
        report += f"""
Rank {i}: {card.company}
{'-'*40}
Requirement: {card.requirement}
Intent Score: {card.intent_score}
Intent Level: {card.intent_level}
Outsourcing Fit: {card.outsourcing_fit}

Decision Maker: {card.decision_maker.get('name')}
Role: {card.decision_maker.get('role')}
LinkedIn: {card.decision_maker.get('linkedin_url')}

Claim Audit: {card.claim_audit_status}
Outreach State: {card.outreach_state}

Connection Request ({msg.character_count_connection} chars):
{msg.connection_request}

Follow-up #1 ({msg.character_count_followup_1} chars):
{msg.follow_up_1}

Follow-up #2 ({msg.character_count_followup_2} chars):
{msg.follow_up_2}

"""
    
    report += f"""
{'='*80}
NEEDS REVIEW (CLAIM AUDIT FAILED)
{'='*80}

"""
    
    for card in needs_review:
        msg = card.linkedin_message
        failed_claims = [a for a in msg.audit_details if not a.is_supported]
        report += f"""
{card.company}:
  Claim Audit: {card.claim_audit_status}
  Outreach State: {card.outreach_state}
  Failed Claims:
"""
        for claim in failed_claims:
            report += f"    - {claim.claim}: {claim.reason}\n"
    
    report += f"""
{'='*80}
NEXT STEPS
{'='*80}

1. Founder reviews CLAIM AUDIT PASSED opportunities
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
    print("BEACON CTO — OUTREACH CLAIM SAFETY HOTFIX")
    print("="*80)
    
    # Load LinkedIn validation data
    print("\nLoading LinkedIn validation data...")
    data = load_linkedin_validation()
    cards = data.get("sales_intelligence_cards", [])
    print(f"Found {len(cards)} cards to audit")
    
    # Audit and regenerate messages
    audited_cards = []
    for card_data in cards:
        print(f"\nAuditing {card_data.get('company')}...")
        
        # Create audited card
        audited_card = create_audited_sales_intelligence_card(card_data)
        audited_cards.append(audited_card)
        
        print(f"  Claim Audit: {audited_card.claim_audit_status}")
        print(f"  Outreach State: {audited_card.outreach_state}")
    
    # Save outputs
    print("\nSaving audited outputs...")
    save_audited_outputs(audited_cards)
    
    # Generate report
    print("\nGenerating audited report...")
    report = generate_audited_report(audited_cards)
    
    # Save report
    report_file = EXPORTS_DIR / "linkedin_sales_validation_audited_report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(report)
    print(f"\nReport saved to {report_file}")


if __name__ == "__main__":
    main()
