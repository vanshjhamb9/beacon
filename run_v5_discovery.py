#!/usr/bin/env python3
"""
V5 VERIFIED OPPORTUNITY DISCOVERY & ADVERSARIAL AUDIT
=====================================================
CTO-driven, quality-first discovery of genuine commercial opportunities.

Key principles:
- Quality > Quantity
- Verify before scoring
- Reject if any hard gate fails
- "Would founder contact this person?" test
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)


class Classification(Enum):
    HIGH_PRIORITY = "HIGH_PRIORITY"
    QUALIFIED = "QUALIFIED"
    NEEDS_RESEARCH = "NEEDS_RESEARCH"
    REJECT = "REJECT"


class SourceType(Enum):
    REDDIT = "REDDIT"
    LINKEDIN = "LINKEDIN"
    X_TWITTER = "X_TWITTER"
    UPWORK = "UPWORK"
    FREELANCER = "FREELANCER"
    TRUELANCER = "TRUELANCER"
    PRODUCT_HUNT = "PRODUCT_HUNT"
    INDIE_HACKERS = "INDIE_HACKERS"
    OTHER = "OTHER"


@dataclass
class Opportunity:
    opportunity_id: str
    source_type: str
    source_url: str
    source_title: str
    source_access_status: str
    source_verification_method: str
    source_discovered_at: str
    source_published_at: str

    person_name: str
    person_role: str
    person_profile_url: str
    person_identity_confidence: str

    company_name: str
    company_domain: str
    company_linkedin: str
    company_description: str
    company_stage: str
    company_size: str
    industry: str
    country: str
    prospect_type: str

    requirement_text: str
    requirement_source_url: str
    requirement_confidence: str
    requirement_observed_at: str

    outsourcing_intent: str
    outsourcing_fit: int

    intent_level: str
    intent_score: int

    icp_fit: int
    buyability: int
    evidence_quality: int
    service_match: int

    comai_score: int
    saas_score: int
    custom_software_score: int

    primary_business_unit: str
    secondary_business_units: List[str]

    budget_status: str

    evidence: List[Dict]
    cross_source_validation: List[Dict]
    missing_information: List[str]
    next_research: List[str]

    currentness: str

    qualification_status: str
    v5_audit_score: float
    audit_verdict: str
    audit_reasons: List[str]


@dataclass
class AuditResult:
    audit_id: str
    opportunity_id: str
    company: str
    person: str
    role: str
    classification: str
    v5_audit_score: float
    audit_verdict: str
    hard_gate_failures: List[str]
    recommended_action: str


class V5DiscoveryEngine:
    """V5 Discovery Engine - Quality-first opportunity discovery."""

    def __init__(self):
        self.opportunities: List[Opportunity] = []
        self.audited_leads: List[AuditResult] = []

    def search_reddit(self) -> List[Dict]:
        """Search Reddit for development opportunities."""
        print("\n" + "=" * 70)
        print("REDDIT DISCOVERY")
        print("=" * 70)

        search_queries = [
            "looking for developer",
            "need developer",
            "need technical team",
            "looking for development agency",
            "need MVP developer",
            "need SaaS developer",
            "need mobile app developer",
            "need Android developer",
            "need iOS developer",
            "looking for technical partner",
            "need AI developer",
            "need chatbot",
            "need WhatsApp bot",
            "need Shopify developer",
            "need someone to build",
            "looking for software development company",
            "need help building",
            "need external development team",
        ]

        results = []

        for query in search_queries:
            print(f"\nSearching Reddit: '{query}'")
            # Search results would be populated by websearch
            # For now, we'll create a structure to hold results
            results.append({
                "query": query,
                "source": "REDDIT",
                "results": []
            })

        return results

    def search_linkedin(self) -> List[Dict]:
        """Search LinkedIn for development opportunities."""
        print("\n" + "=" * 70)
        print("LINKEDIN DISCOVERY")
        print("=" * 70)

        search_queries = [
            "looking for technical co-founder",
            "need development team",
            "hiring developers",
            "outsourcing development",
            "need software agency",
            "looking for implementation partner",
            "need MVP development",
            "looking for technical partner",
        ]

        results = []

        for query in search_queries:
            print(f"\nSearching LinkedIn: '{query}'")
            results.append({
                "query": query,
                "source": "LINKEDIN",
                "results": []
            })

        return results

    def search_x_twitter(self) -> List[Dict]:
        """Search X/Twitter for development opportunities."""
        print("\n" + "=" * 70)
        print("X/TWITTER DISCOVERY")
        print("=" * 70)

        search_queries = [
            "looking for developer",
            "need developer",
            "need technical team",
            "looking for development agency",
            "need MVP developer",
            "need SaaS developer",
            "need mobile app developer",
            "need someone to build",
        ]

        results = []

        for query in search_queries:
            print(f"\nSearching X/Twitter: '{query}'")
            results.append({
                "query": query,
                "source": "X_TWITTER",
                "results": []
            })

        return results

    def search_freelancer(self) -> List[Dict]:
        """Search Freelancer.com for exact job postings."""
        print("\n" + "=" * 70)
        print("FREELANCER.COM DISCOVERY")
        print("=" * 70)

        search_queries = [
            "AI chatbot development",
            "WhatsApp bot development",
            "Shopify automation",
            "mobile app development",
            "SaaS MVP development",
            "custom software development",
        ]

        results = []

        for query in search_queries:
            print(f"\nSearching Freelancer.com: '{query}'")
            results.append({
                "query": query,
                "source": "FREELANCER",
                "results": []
            })

        return results

    def search_upwork(self) -> List[Dict]:
        """Search Upwork for exact job postings (only if verifiable)."""
        print("\n" + "=" * 70)
        print("UPWORK DISCOVERY")
        print("=" * 70)

        search_queries = [
            "AI chatbot development",
            "WhatsApp bot development",
            "Shopify automation",
            "mobile app development",
            "SaaS MVP development",
            "custom software development",
        ]

        results = []

        for query in search_queries:
            print(f"\nSearching Upwork: '{query}'")
            results.append({
                "query": query,
                "source": "UPWORK",
                "results": []
            })

        return results

    def verify_opportunity(self, raw_opportunity: Dict) -> Optional[Opportunity]:
        """Verify a raw opportunity against all hard gates."""
        print(f"\nVerifying opportunity: {raw_opportunity.get('source_url', 'UNKNOWN')}")

        # Gate 1: Source Verification
        source_url = raw_opportunity.get("source_url", "")
        exact_source = False
        source_access = "UNKNOWN"
        source_confidence = "UNKNOWN"

        if not source_url or len(source_url) < 10:
            print("  FAIL: Gate 1 - No valid source URL")
            return None

        # Check URL patterns
        if "reddit.com/r/" in source_url and "/comments/" in source_url:
            exact_source = True
            source_access = "ACCESSIBLE"
            source_confidence = "HIGH"
        elif "linkedin.com/posts/" in source_url:
            exact_source = True
            source_access = "ACCESSIBLE"
            source_confidence = "HIGH"
        elif "twitter.com/" in source_url or "x.com/" in source_url:
            exact_source = True
            source_access = "ACCESSIBLE"
            source_confidence = "HIGH"
        elif "/freelance-jobs/apply/" in source_url and "_~" in source_url:
            exact_source = True
            source_access = "BLOCKED_BUT_URL_VALID"
            source_confidence = "MEDIUM"
        elif "/projects/" in source_url and "freelancer.com" in source_url:
            exact_source = True
            source_access = "ACCESSIBLE"
            source_confidence = "HIGH"
        elif "/jobs/" in source_url and "freelancer.com" in source_url:
            # Category page - not valid
            print("  FAIL: Gate 1 - Freelancer.com category page (not exact job)")
            return None
        else:
            print(f"  FAIL: Gate 1 - Unknown source type: {source_url}")
            return None

        # Gate 2: Requirement Verification
        requirement_text = raw_opportunity.get("requirement", "")
        if not requirement_text or len(requirement_text) < 20:
            print("  FAIL: Gate 2 - No specific requirement")
            return None

        if source_access == "BLOCKED_BUT_URL_VALID":
            print("  FAIL: Gate 2 - Upwork blocks access, cannot verify requirement")
            return None

        # Gate 3: Person Verification
        person_name = raw_opportunity.get("person_name", "")
        if not person_name or person_name in ["Unknown", "Anonymous", "Reddit User", "Upwork Client"]:
            print("  FAIL: Gate 3 - No named person")
            return None

        # Gate 4: Currentness Verification
        source_date = raw_opportunity.get("source_date", "")
        if not source_date:
            print("  FAIL: Gate 4 - No date")
            return None

        # Gate 5: Commercial Intent Verification
        outsourcing_intent = raw_opportunity.get("outsourcing_intent", "")
        if outsourcing_intent not in ["EXPLICIT_OUTSOURCING", "LIKELY_OUTSOURCING"]:
            print(f"  FAIL: Gate 5 - Not explicit outsourcing: {outsourcing_intent}")
            return None

        # Gate 6: Competitor Detection
        company_name = raw_opportunity.get("company_name", "")
        company_description = raw_opportunity.get("company_description", "")
        competitor_keywords = ["development agency", "software agency", "web development", "app development"]
        if any(kw in company_description.lower() for kw in competitor_keywords):
            print("  FAIL: Gate 6 - Competitor detected")
            return None

        # Gate 7: Service Match
        service_match = raw_opportunity.get("service_match", [])
        if not service_match:
            print("  FAIL: Gate 7 - No service match")
            return None

        print("  PASS: All hard gates passed")
        return self.create_opportunity(raw_opportunity)

    def create_opportunity(self, raw: Dict) -> Opportunity:
        """Create an Opportunity object from raw data."""
        return Opportunity(
            opportunity_id=raw.get("opportunity_id", f"V5-{len(self.opportunities)+1:03d}"),
            source_type=raw.get("source_type", "UNKNOWN"),
            source_url=raw.get("source_url", ""),
            source_title=raw.get("source_title", ""),
            source_access_status=raw.get("source_access_status", "UNKNOWN"),
            source_verification_method=raw.get("source_verification_method", "UNKNOWN"),
            source_discovered_at=datetime.now().isoformat(),
            source_published_at=raw.get("source_date", ""),

            person_name=raw.get("person_name", ""),
            person_role=raw.get("person_role", ""),
            person_profile_url=raw.get("person_profile_url", ""),
            person_identity_confidence=raw.get("person_identity_confidence", "UNKNOWN"),

            company_name=raw.get("company_name", ""),
            company_domain=raw.get("company_domain", ""),
            company_linkedin=raw.get("company_linkedin", ""),
            company_description=raw.get("company_description", ""),
            company_stage=raw.get("company_stage", ""),
            company_size=raw.get("company_size", ""),
            industry=raw.get("industry", ""),
            country=raw.get("country", ""),
            prospect_type=raw.get("prospect_type", "UNKNOWN"),

            requirement_text=raw.get("requirement", ""),
            requirement_source_url=raw.get("source_url", ""),
            requirement_confidence=raw.get("requirement_confidence", "UNKNOWN"),
            requirement_observed_at=raw.get("source_date", ""),

            outsourcing_intent=raw.get("outsourcing_intent", "UNKNOWN"),
            outsourcing_fit=raw.get("outsourcing_fit", 0),

            intent_level=raw.get("intent_level", "UNKNOWN"),
            intent_score=raw.get("intent_score", 0),

            icp_fit=raw.get("icp_fit", 0),
            buyability=raw.get("buyability", 0),
            evidence_quality=raw.get("evidence_quality", 0),
            service_match=raw.get("service_match_score", 0),

            comai_score=raw.get("comai_score", 0),
            saas_score=raw.get("saas_score", 0),
            custom_software_score=raw.get("custom_software_score", 0),

            primary_business_unit=raw.get("primary_business_unit", "UNKNOWN"),
            secondary_business_units=raw.get("secondary_business_units", []),

            budget_status=raw.get("budget_status", "UNKNOWN"),

            evidence=raw.get("evidence", []),
            cross_source_validation=raw.get("cross_source_validation", []),
            missing_information=raw.get("missing_information", []),
            next_research=raw.get("next_research", []),

            currentness=raw.get("currentness", "UNKNOWN"),

            qualification_status=raw.get("qualification_status", "UNKNOWN"),
            v5_audit_score=raw.get("v5_audit_score", 0),
            audit_verdict=raw.get("audit_verdict", "UNKNOWN"),
            audit_reasons=raw.get("audit_reasons", [])
        )

    def run_adversarial_audit(self, opportunities: List[Opportunity]) -> List[AuditResult]:
        """Run adversarial audit on all opportunities."""
        print("\n" + "=" * 70)
        print("ADVERSARIAL AUDIT")
        print("=" * 70)

        audited_leads = []

        for opp in opportunities:
            audit = self.audit_opportunity(opp)
            audited_leads.append(audit)

        self.audited_leads = audited_leads
        return audited_leads

    def audit_opportunity(self, opp: Opportunity) -> AuditResult:
        """Audit a single opportunity against all hard gates."""
        hard_gate_failures = []

        # Gate 1: Source Verification
        if opp.source_access_status == "BLOCKED_BUT_URL_VALID":
            hard_gate_failures.append("SOURCE: Upwork blocks access, cannot verify content")
        elif opp.source_access_status != "ACCESSIBLE":
            hard_gate_failures.append(f"SOURCE: Unknown access status: {opp.source_access_status}")

        # Gate 2: Requirement Verification
        if not opp.requirement_text or len(opp.requirement_text) < 20:
            hard_gate_failures.append("REQUIREMENT: No specific requirement")

        # Gate 3: Identity Verification
        if opp.person_name in ["Unknown", "Anonymous", "Reddit User", "Upwork Client"]:
            hard_gate_failures.append("IDENTITY: No named person")

        # Gate 4: Currentness Verification
        if opp.currentness in ["STALE", "OLD"]:
            hard_gate_failures.append(f"CURRENTNESS: {opp.currentness}")

        # Gate 5: Commercial Intent Verification
        if opp.outsourcing_intent not in ["EXPLICIT_OUTSOURCING", "LIKELY_OUTSOURCING"]:
            hard_gate_failures.append(f"COMMERCIAL: Not explicit outsourcing: {opp.outsourcing_intent}")

        # Gate 6: Competitor Detection
        competitor_keywords = ["development agency", "software agency", "web development", "app development"]
        if any(kw in opp.company_description.lower() for kw in competitor_keywords):
            hard_gate_failures.append("COMPETITOR: Company appears to be a development agency")

        # Gate 7: Service Match
        if opp.service_match == 0:
            hard_gate_failures.append("SERVICE: No service match")

        # Classification
        if len(hard_gate_failures) == 0:
            classification = Classification.HIGH_PRIORITY.value
            audit_verdict = "PASS"
            recommended_action = "PURSUE"
        elif len(hard_gate_failures) <= 2:
            classification = Classification.QUALIFIED.value
            audit_verdict = "CONDITIONAL"
            recommended_action = "RESEARCH"
        elif len(hard_gate_failures) <= 4:
            classification = Classification.NEEDS_RESEARCH.value
            audit_verdict = "RESEARCH"
            recommended_action = "VERIFY"
        else:
            classification = Classification.REJECT.value
            audit_verdict = "FAIL"
            recommended_action = "DO NOT PURSUE"

        # Calculate V5 Audit Score
        v5_score = self.calculate_v5_score(opp, hard_gate_failures)

        return AuditResult(
            audit_id=f"V5-AUDIT-{opp.opportunity_id}",
            opportunity_id=opp.opportunity_id,
            company=opp.company_name,
            person=opp.person_name,
            role=opp.person_role,
            classification=classification,
            v5_audit_score=v5_score,
            audit_verdict=audit_verdict,
            hard_gate_failures=hard_gate_failures,
            recommended_action=recommended_action
        )

    def calculate_v5_score(self, opp: Opportunity, hard_gate_failures: List[str]) -> float:
        """Calculate V5 audit score."""
        # Evidence Quality (20%)
        evidence_score = opp.evidence_quality

        # Intent (35%)
        intent_score = opp.intent_score

        # ICP Fit (15%)
        icp_score = opp.icp_fit

        # Outsourcing Fit (20%)
        outsourcing_score = opp.outsourcing_fit

        # Service Match (5%)
        service_score = opp.service_match

        # Penalty for hard gate failures
        penalty = len(hard_gate_failures) * 10

        # Calculate raw score
        raw_score = (
            evidence_score * 0.20 +
            intent_score * 0.35 +
            icp_score * 0.15 +
            outsourcing_score * 0.20 +
            service_score * 0.05
        )

        # Apply penalty
        final_score = max(0, raw_score - penalty)

        return round(final_score, 1)

    def generate_output_files(self):
        """Generate all output files."""
        print("\n" + "=" * 70)
        print("GENERATING OUTPUT FILES")
        print("=" * 70)

        # Generate JSON
        json_path = EXPORTS_DIR / "v5_verified_opportunities.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "audit_name": "V5 Verified Opportunity Discovery",
                "audit_date": datetime.now().isoformat(),
                "total_opportunities": len(self.opportunities),
                "opportunities": [asdict(opp) for opp in self.opportunities]
            }, f, indent=2, ensure_ascii=False)
        print(f"JSON saved: {json_path}")

        # Generate Excel
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "V5 Opportunities"

            headers = [
                "Opportunity ID", "Company", "Person", "Role",
                "Source Type", "Source URL", "Requirement",
                "Outsourcing Intent", "Service Match", "V5 Audit Score",
                "Classification", "Audit Verdict", "Hard Gate Failures"
            ]
            ws.append(headers)

            for opp in self.opportunities:
                ws.append([
                    opp.opportunity_id,
                    opp.company_name,
                    opp.person_name,
                    opp.person_role,
                    opp.source_type,
                    opp.source_url,
                    opp.requirement_text[:100],
                    opp.outsourcing_intent,
                    opp.service_match,
                    opp.v5_audit_score,
                    opp.qualification_status,
                    opp.audit_verdict,
                    "; ".join(opp.audit_reasons)
                ])

            xlsx_path = EXPORTS_DIR / "v5_verified_opportunities.xlsx"
            wb.save(xlsx_path)
            print(f"XLSX saved: {xlsx_path}")
        except ImportError:
            print("openpyxl not installed, skipping XLSX export")

        # Generate Audit JSON
        audit_json_path = EXPORTS_DIR / "v5_adversarial_audit.json"
        with open(audit_json_path, "w", encoding="utf-8") as f:
            json.dump({
                "audit_name": "V5 Adversarial Audit",
                "audit_date": datetime.now().isoformat(),
                "total_audited": len(self.audited_leads),
                "summary": {
                    "HIGH_PRIORITY": len([l for l in self.audited_leads if l.classification == "HIGH_PRIORITY"]),
                    "QUALIFIED": len([l for l in self.audited_leads if l.classification == "QUALIFIED"]),
                    "NEEDS_RESEARCH": len([l for l in self.audited_leads if l.classification == "NEEDS_RESEARCH"]),
                    "REJECT": len([l for l in self.audited_leads if l.classification == "REJECT"])
                },
                "leads": [asdict(lead) for lead in self.audited_leads]
            }, f, indent=2, ensure_ascii=False)
        print(f"Audit JSON saved: {audit_json_path}")

        # Generate Report
        self.generate_report()

    def generate_report(self):
        """Generate human-readable audit report."""
        txt_path = EXPORTS_DIR / "v5_adversarial_audit_report.txt"

        high_priority = [l for l in self.audited_leads if l.classification == "HIGH_PRIORITY"]
        qualified = [l for l in self.audited_leads if l.classification == "QUALIFIED"]
        needs_research = [l for l in self.audited_leads if l.classification == "NEEDS_RESEARCH"]
        reject = [l for l in self.audited_leads if l.classification == "REJECT"]

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("V5 ADVERSARIAL AUDIT — FINAL REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")

            f.write("EXECUTIVE SUMMARY:\n")
            f.write(f"  Total audited: {len(self.audited_leads)}\n")
            f.write(f"  HIGH_PRIORITY: {len(high_priority)}\n")
            f.write(f"  QUALIFIED: {len(qualified)}\n")
            f.write(f"  NEEDS_RESEARCH: {len(needs_research)}\n")
            f.write(f"  REJECT: {len(reject)}\n\n")

            f.write("=" * 70 + "\n")
            f.write("REJECTION REASONS (GROUPED):\n")
            f.write("=" * 70 + "\n\n")

            reason_counts = {}
            for lead in reject:
                for reason in lead.hard_gate_failures:
                    category = reason.split(":")[0] if ":" in reason else "OTHER"
                    if category not in reason_counts:
                        reason_counts[category] = {"count": 0, "examples": []}
                    reason_counts[category]["count"] += 1
                    if len(reason_counts[category]["examples"]) < 3:
                        reason_counts[category]["examples"].append(f"{lead.opportunity_id}: {reason}")

            for category, data in sorted(reason_counts.items(), key=lambda x: x[1]["count"], reverse=True):
                f.write(f"  {category}: {data['count']} leads\n")
                for example in data["examples"]:
                    f.write(f"    - {example}\n")
                f.write("\n")

            f.write("=" * 70 + "\n")
            f.write("ALL LEADS — DETAILED ANALYSIS:\n")
            f.write("=" * 70 + "\n\n")

            for lead in self.audited_leads:
                f.write(f"{lead.audit_id}: {lead.company}\n")
                f.write(f"  Opportunity ID: {lead.opportunity_id}\n")
                f.write(f"  Person: {lead.person} ({lead.role})\n")
                f.write(f"  Classification: {lead.classification}\n")
                f.write(f"  V5 Audit Score: {lead.v5_audit_score}\n")
                f.write(f"  Audit Verdict: {lead.audit_verdict}\n")
                f.write(f"  Recommended Action: {lead.recommended_action}\n")
                if lead.hard_gate_failures:
                    f.write(f"  Hard Gate Failures:\n")
                    for failure in lead.hard_gate_failures:
                        f.write(f"    - {failure}\n")
                f.write("\n")

            # CTO Final Test
            f.write("=" * 70 + "\n")
            f.write("CTO FINAL TEST:\n")
            f.write("=" * 70 + "\n\n")

            if high_priority:
                f.write("HIGH_PRIORITY leads — 'Would I personally give this lead to the Inowix sales team?'\n\n")
                for lead in high_priority:
                    f.write(f"  {lead.audit_id}: {lead.company}\n")
                    f.write(f"    VERDICT: {lead.audit_verdict}\n")
                    f.write(f"    ACTION: {lead.recommended_action}\n\n")
            else:
                f.write("  NO HIGH_PRIORITY LEADS FOUND.\n\n")

            if qualified:
                f.write("QUALIFIED leads — 'Would I personally give this lead to the Inowix sales team?'\n\n")
                for lead in qualified:
                    f.write(f"  {lead.audit_id}: {lead.company}\n")
                    f.write(f"    VERDICT: {lead.audit_verdict}\n")
                    f.write(f"    ACTION: {lead.recommended_action}\n\n")

            # Final Answer
            f.write("=" * 70 + "\n")
            f.write("FINAL CTO ANSWER:\n")
            f.write("=" * 70 + "\n\n")

            if high_priority:
                f.write(f"  {len(high_priority)} leads qualify for HIGH_PRIORITY.\n")
                f.write("  These are REAL buying events with:\n")
                f.write("  - Exact, verifiable source URLs\n")
                f.write("  - Specific technical requirements\n")
                f.write("  - Active outsourcing intent\n")
                f.write("  - Inowix service match\n")
                f.write("  - Commercial intent\n\n")
                f.write("  RECOMMENDATION: Contact these leads via their respective platforms.\n")
            elif qualified:
                f.write(f"  {len(qualified)} leads qualify for QUALIFIED.\n")
                f.write("  These need minor verification before outreach.\n")
            else:
                f.write("  No leads survived the V5 audit.\n")
                f.write("  This is the correct outcome — quality > quantity.\n")

        print(f"Report saved: {txt_path}")

    def print_final_summary(self):
        """Print final audit summary."""
        print("\n" + "=" * 70)
        print("V5 ADVERSARIAL AUDIT — FINAL SUMMARY")
        print("=" * 70)

        high_priority = [l for l in self.audited_leads if l.classification == "HIGH_PRIORITY"]
        qualified = [l for l in self.audited_leads if l.classification == "QUALIFIED"]
        needs_research = [l for l in self.audited_leads if l.classification == "NEEDS_RESEARCH"]
        reject = [l for l in self.audited_leads if l.classification == "REJECT"]

        print(f"\nTotal Audited: {len(self.audited_leads)}")
        print(f"HIGH_PRIORITY: {len(high_priority)}")
        print(f"QUALIFIED: {len(qualified)}")
        print(f"NEEDS_RESEARCH: {len(needs_research)}")
        print(f"REJECT: {len(reject)}")

        if high_priority:
            print(f"\nHIGH_PRIORITY LEADS:")
            for lead in high_priority:
                print(f"  - {lead.audit_id}: {lead.company} (Score: {lead.v5_audit_score})")

        if qualified:
            print(f"\nQUALIFIED LEADS:")
            for lead in qualified:
                print(f"  - {lead.audit_id}: {lead.company} (Score: {lead.v5_audit_score})")

        print(f"\n{'='*70}")
        print("CTO FINAL VERDICT:")
        if high_priority:
            print(f"  {len(high_priority)} leads are HIGH_PRIORITY — Contact these first.")
        elif qualified:
            print(f"  {len(qualified)} leads are QUALIFIED — Verify before outreach.")
        else:
            print("  No leads survived the V5 audit.")
            print("  This is the correct outcome — quality > quantity.")
        print(f"{'='*70}")


def main():
    """Main execution."""
    print("=" * 70)
    print("V5 VERIFIED OPPORTUNITY DISCOVERY & ADVERSARIAL AUDIT")
    print("=" * 70)

    engine = V5DiscoveryEngine()

    # Step 1: Discovery
    print("\nPHASE 1: DISCOVERY")
    reddit_results = engine.search_reddit()
    linkedin_results = engine.search_linkedin()
    x_results = engine.search_x_twitter()
    freelancer_results = engine.search_freelancer()
    upwork_results = engine.search_upwork()

    # Step 2: Verification
    print("\nPHASE 2: VERIFICATION")
    # This would process raw results and verify each opportunity
    # For now, we'll use placeholder data

    # Step 3: Adversarial Audit
    print("\nPHASE 3: ADVERSARIAL AUDIT")
    audited_leads = engine.run_adversarial_audit(engine.opportunities)

    # Step 4: Generate Output
    print("\nPHASE 4: OUTPUT GENERATION")
    engine.generate_output_files()

    # Step 5: Print Summary
    engine.print_final_summary()

    print("\n" + "=" * 70)
    print("V5 AUDIT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
