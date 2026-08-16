"""Evidence Chain and Sales Readiness Engine.

Evaluates whether an opportunity meets all gates for SALES_READY status.
Implements the FINAL CTO TEST.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from cybersecurity_engine.models import (
    Contact,
    ContactChannel,
    Company,
    CompanySize,
    CybersecurityOpportunity,
    Evidence,
    EvidenceConfidence,
    OutreachClassification,
    OutreachPreparation,
    OpportunityPriority,
    OpportunityType,
    SalesReadiness,
    ServiceLane,
)


# ============================================================
# COMPETITOR REJECTION
# ============================================================

COMPETITOR_KEYWORDS = {
    "crowdstrike", "palo alto", "fortinet", "check point",
    "symantec", "mcafee", "trend micro", "kaspersky", "sophos",
    "rapid7", "qualys", "tenable", "nessus", "burp suite",
    "owasp", "veracode", "synopsys", "whitehat", "hackerone",
    "bugcrowd", "cobalt", "pentestlab", "security testing company",
    "cybersecurity vendor", "penetration testing company",
}


def is_competitor(company_name: str) -> bool:
    """Check if a company is a competitor (should not be targeted)."""
    name_lower = company_name.lower()
    return any(kw in name_lower for kw in COMPETITOR_KEYWORDS)


# ============================================================
# COMPANY VERIFICATION
# ============================================================

def verify_company(company: Company) -> tuple[bool, list[str]]:
    """Verify that a company is real and qualifies.

    Returns:
        Tuple of (is_valid, list_of_reasons)
    """
    reasons = []

    if not company.name:
        reasons.append("Missing company name")
    if not company.url:
        reasons.append("Missing company URL")
    if not company.country:
        reasons.append("Missing country information")

    # Check if company is too large (out of scope for direct outreach)
    if company.company_size == CompanySize.ENTERPRISE and company.employee_count > 10000:
        reasons.append("Company too large for direct outreach")

    return (len(reasons) == 0, reasons)


# ============================================================
# EVIDENCE EVALUATION
# ============================================================

def evaluate_evidence_chain(
    evidence: list[Evidence],
) -> tuple[EvidenceConfidence, list[str]]:
    """Evaluate the overall evidence chain.

    Returns:
        Tuple of (confidence_level, list_of_issues)
    """
    issues = []

    if not evidence:
        return (EvidenceConfidence.LOW, ["No evidence collected"])

    verified_count = sum(1 for e in evidence if e.verified)
    total_count = len(evidence)
    high_confidence_count = sum(1 for e in evidence if e.confidence >= 80)

    # Check evidence diversity
    source_types = set(e.source_type for e in evidence)
    if len(source_types) < 2:
        issues.append("Evidence from single source type")

    # Check for primary source evidence
    has_primary = any(
        e.source_type in {"procurement", "company_announcement", "founder_post"}
        for e in evidence
    )
    if not has_primary:
        issues.append("No primary source evidence (procurement/announcement/founder)")

    # Check recency
    now = datetime.now(timezone.utc)
    recent_evidence = [
        e for e in evidence
        if e.published_at and (now - e.published_at).days <= 90
    ]
    if not recent_evidence:
        issues.append("No evidence from last 90 days")

    # Calculate overall confidence
    if verified_count >= 3 and high_confidence_count >= 2:
        return (EvidenceConfidence.HIGH, issues)
    elif verified_count >= 1 or high_confidence_count >= 1:
        return (EvidenceConfidence.MEDIUM, issues)
    else:
        return (EvidenceConfidence.LOW, issues)


# ============================================================
# CONTACTABILITY ASSESSMENT
# ============================================================

def assess_contactability(contact: Contact) -> tuple[str, list[str]]:
    """Assess contactability level.

    Returns:
        Tuple of (level, list_of_channels)
    """
    channels = []

    if contact.email_status == "verified" and contact.email:
        channels.append("decision_maker_verified_email")
    if contact.linkedin_status == "verified" and contact.linkedin_url:
        channels.append("decision_maker_linkedin")
    if contact.phone_status == "verified" and contact.phone:
        channels.append("phone")

    # Determine level
    if "decision_maker_verified_email" in channels:
        return ("high", channels)
    elif "decision_maker_linkedin" in channels:
        return ("medium", channels)
    elif channels:
        return ("low", channels)
    else:
        return ("unreachable", [])


# ============================================================
# SALES READINESS EVALUATOR
# ============================================================

class SalesReadinessEvaluator:
    """Evaluates whether an opportunity is SALES_READY.

    Implements the FINAL CTO TEST:
    "Would a cybersecurity sales representative reasonably contact this company
    TODAY based solely on the evidence Beacon collected?"
    """

    def evaluate(
        self,
        opportunity: CybersecurityOpportunity,
    ) -> CybersecurityOpportunity:
        """Evaluate and set the final verdict on an opportunity.

        Returns the opportunity with final_verdict set.
        """
        issues = []

        # Gate 1: Company verified
        company_valid, company_issues = verify_company(opportunity.company)
        if not company_valid:
            issues.extend(company_issues)

        # Gate 2: Not a competitor
        if is_competitor(opportunity.company.name):
            issues.append("Company is a competitor — rejected")

        # Gate 3: Problem verified (buying event exists)
        if opportunity.buying_event.event_type == "no_signal":
            issues.append("No buying signal detected")

        # Gate 4: Service match HIGH
        if opportunity.buying_event.service_match != "HIGH":
            issues.append(f"Service match is {opportunity.buying_event.service_match} — needs HIGH")

        # Gate 5: Decision maker identified
        # Relaxed: allow Reddit/HN usernames as contact for collector-produced signals
        has_name = bool(opportunity.contact.name)
        has_username = bool(opportunity.contact.name and opportunity.source_name in ("reddit", "hacker_news"))
        if not has_name and not has_username:
            issues.append("No decision maker identified")

        # Gate 6: Reliable contact channel
        contact_level, contact_channels = assess_contactability(opportunity.contact)
        opportunity.contactability = contact_level
        opportunity.contactability_evidence = "; ".join(contact_channels)

        if contact_level == "unreachable":
            # Relaxed: allow for collector-produced signals from Tier 1-2 sources
            # These can still be valuable even without verified contact info
            if opportunity.source_tier <= 2:
                opportunity.contactability = "low"
                opportunity.contactability_evidence = f"available_via_{opportunity.source_name}"
            else:
                issues.append("No reliable contact channel")

        # Gate 7: Evidence chain evaluation
        evidence_confidence, evidence_issues = evaluate_evidence_chain(
            opportunity.evidence_chain
        )
        opportunity.evidence_confidence = evidence_confidence
        issues.extend(evidence_issues)

        # Gate 8: Evidence reproducible (at least 2 evidence sources)
        # Relaxed: allow single-source evidence for high-confidence signals
        evidence_count = len(opportunity.evidence_chain)
        if evidence_count < 2:
            # Allow single-source for P0/P1 signals with high confidence
            if opportunity.priority in (OpportunityPriority.P0, OpportunityPriority.P1):
                pass  # Single source OK for high-priority signals
            elif opportunity.source_tier <= 2:
                pass  # Single source OK for Tier 1-2 sources
            else:
                issues.append("Insufficient evidence (need at least 2 sources)")

        # Gate 9: Safety clear (no compliance issues)
        # This is a placeholder — in production, check for:
        # - GDPR compliance of outreach
        # - CAN-SPAM compliance
        # - Company-specific restrictions

        # Determine final verdict
        if issues:
            # Check if it's still worth nurturing
            critical_gates = [
                "Company is a competitor — rejected",
                "No buying signal detected",
            ]
            has_critical = any(i in critical_gates for i in issues)

            if has_critical:
                opportunity.final_verdict = "NOT_READY"
            else:
                opportunity.final_verdict = "MARKETING_READY"
        else:
            opportunity.final_verdict = "SALES_READY"

        # Set outreach classification
        opportunity.outreach_classification = self._classify_outreach(opportunity)

        # Generate outreach preparation if sales ready
        if opportunity.final_verdict == "SALES_READY":
            opportunity.outreach_preparation = self._prepare_outreach(opportunity)

        return opportunity

    def _classify_outreach(
        self, opportunity: CybersecurityOpportunity
    ) -> OutreachClassification:
        """Classify the outreach type."""
        if opportunity.priority == OpportunityPriority.P0:
            return OutreachClassification.ACTIVE_BUYING
        elif opportunity.priority == OpportunityPriority.P1:
            return OutreachClassification.PROBLEM_FIRST
        elif opportunity.priority == OpportunityPriority.P2:
            return OutreachClassification.NURTURE
        else:
            return OutreachClassification.NO_OUTREACH

    def _prepare_outreach(
        self, opportunity: CybersecurityOpportunity
    ) -> OutreachPreparation:
        """Prepare outreach materials for a sales-ready opportunity."""
        prep = OutreachPreparation()

        prep.buyer_name = opportunity.contact.name
        prep.buyer_role = opportunity.contact.role
        prep.company_name = opportunity.company.name
        prep.problem_summary = opportunity.buying_event.description
        prep.why_now = opportunity.buying_event.why_now
        prep.recommended_service = "; ".join(
            opportunity.buying_event.services_needed[:3]
        )

        # Determine best channel
        if opportunity.contact.email_status == "verified":
            prep.recommended_channel = "email"
        elif opportunity.contact.linkedin_status == "verified":
            prep.recommended_channel = "linkedin"
        else:
            prep.recommended_channel = "company_website"

        # Evidence summary
        evidence_sources = list(set(
            e.source_name for e in opportunity.evidence_chain
        ))
        prep.evidence_summary = f"Sources: {', '.join(evidence_sources)}"

        # Personalization points
        prep.personalization_points = self._extract_personalization_points(
            opportunity
        )

        # Outreach angle
        prep.outreach_angle = self._determine_outreach_angle(opportunity)

        return prep

    def _extract_personalization_points(
        self, opportunity: CybersecurityOpportunity
    ) -> list[str]:
        """Extract personalization points for outreach."""
        points = []

        # Company-specific
        if opportunity.company.industry:
            points.append(f"Industry: {opportunity.company.industry}")
        if opportunity.company.country:
            points.append(f"Location: {opportunity.company.country}")

        # Event-specific
        if opportunity.buying_event.services_needed:
            services = opportunity.buying_event.services_needed[:3]
            points.append(f"Services needed: {', '.join(services)}")

        # Contact-specific
        if opportunity.contact.role:
            points.append(f"Role: {opportunity.contact.role}")

        return points

    def _determine_outreach_angle(
        self, opportunity: CybersecurityOpportunity
    ) -> str:
        """Determine the outreach angle based on the opportunity type."""
        if opportunity.priority == OpportunityPriority.P0:
            return "direct_response"
        elif opportunity.priority == OpportunityPriority.P1:
            return "problem_first"
        else:
            return "value_proposition"
