#!/usr/bin/env python3
"""
V5 FINAL OPPORTUNITY DISCOVERY & VERIFICATION
=============================================
Real opportunities discovered through websearch.
Applied V5 hard gates and adversarial audit.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import re

EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)


class V5Opportunity:
    """V5 Verified Opportunity."""

    def __init__(self, data: Dict):
        self.opportunity_id = data.get("opportunity_id", "")
        self.source_type = data.get("source_type", "")
        self.source_url = data.get("source_url", "")
        self.source_title = data.get("source_title", "")
        self.source_access_status = data.get("source_access_status", "")
        self.source_verification_method = data.get("source_verification_method", "")
        self.source_discovered_at = datetime.now().isoformat()
        self.source_published_at = data.get("source_date", "")

        self.person_name = data.get("person_name", "")
        self.person_role = data.get("person_role", "")
        self.person_profile_url = data.get("person_profile_url", "")
        self.person_identity_confidence = data.get("person_identity_confidence", "")

        self.company_name = data.get("company_name", "")
        self.company_domain = data.get("company_domain", "")
        self.company_linkedin = data.get("company_linkedin", "")
        self.company_description = data.get("company_description", "")
        self.company_stage = data.get("company_stage", "")
        self.company_size = data.get("company_size", "")
        self.industry = data.get("industry", "")
        self.country = data.get("country", "")
        self.prospect_type = data.get("prospect_type", "")

        self.requirement_text = data.get("requirement", "")
        self.requirement_source_url = data.get("source_url", "")
        self.requirement_confidence = data.get("requirement_confidence", "")
        self.requirement_observed_at = data.get("source_date", "")

        self.outsourcing_intent = data.get("outsourcing_intent", "")
        self.outsourcing_fit = data.get("outsourcing_fit", 0)

        self.intent_level = data.get("intent_level", "")
        self.intent_score = data.get("intent_score", 0)

        self.icp_fit = data.get("icp_fit", 0)
        self.buyability = data.get("buyability", 0)
        self.evidence_quality = data.get("evidence_quality", 0)
        self.service_match = data.get("service_match", 0)

        self.comai_score = data.get("comai_score", 0)
        self.saas_score = data.get("saas_score", 0)
        self.custom_software_score = data.get("custom_software_score", 0)

        self.primary_business_unit = data.get("primary_business_unit", "")
        self.secondary_business_units = data.get("secondary_business_units", [])

        self.budget_status = data.get("budget_status", "")

        self.evidence = data.get("evidence", [])
        self.cross_source_validation = data.get("cross_source_validation", [])
        self.missing_information = data.get("missing_information", [])
        self.next_research = data.get("next_research", [])

        self.currentness = data.get("currentness", "")

        self.qualification_status = data.get("qualification_status", "")
        self.v5_audit_score = data.get("v5_audit_score", 0)
        self.audit_verdict = data.get("audit_verdict", "")
        self.audit_reasons = data.get("audit_reasons", [])

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "opportunity_id": self.opportunity_id,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "source_title": self.source_title,
            "source_access_status": self.source_access_status,
            "source_verification_method": self.source_verification_method,
            "source_discovered_at": self.source_discovered_at,
            "source_published_at": self.source_published_at,
            "person_name": self.person_name,
            "person_role": self.person_role,
            "person_profile_url": self.person_profile_url,
            "person_identity_confidence": self.person_identity_confidence,
            "company_name": self.company_name,
            "company_domain": self.company_domain,
            "company_linkedin": self.company_linkedin,
            "company_description": self.company_description,
            "company_stage": self.company_stage,
            "company_size": self.company_size,
            "industry": self.industry,
            "country": self.country,
            "prospect_type": self.prospect_type,
            "requirement_text": self.requirement_text,
            "requirement_source_url": self.requirement_source_url,
            "requirement_confidence": self.requirement_confidence,
            "requirement_observed_at": self.requirement_observed_at,
            "outsourcing_intent": self.outsourcing_intent,
            "outsourcing_fit": self.outsourcing_fit,
            "intent_level": self.intent_level,
            "intent_score": self.intent_score,
            "icp_fit": self.icp_fit,
            "buyability": self.buyability,
            "evidence_quality": self.evidence_quality,
            "service_match": self.service_match,
            "comai_score": self.comai_score,
            "saas_score": self.saas_score,
            "custom_software_score": self.custom_software_score,
            "primary_business_unit": self.primary_business_unit,
            "secondary_business_units": self.secondary_business_units,
            "budget_status": self.budget_status,
            "evidence": self.evidence,
            "cross_source_validation": self.cross_source_validation,
            "missing_information": self.missing_information,
            "next_research": self.next_research,
            "currentness": self.currentness,
            "qualification_status": self.qualification_status,
            "v5_audit_score": self.v5_audit_score,
            "audit_verdict": self.audit_verdict,
            "audit_reasons": self.audit_reasons
        }


def apply_hard_gates(opp: V5Opportunity) -> List[str]:
    """Apply V5 hard gates to an opportunity."""
    failures = []

    # Gate 1: Source Verification
    if not opp.source_url or len(opp.source_url) < 10:
        failures.append("SOURCE: No valid source URL")
    elif opp.source_access_status == "BLOCKED_BUT_URL_VALID":
        failures.append("SOURCE: Upwork blocks access, cannot verify content")
    elif opp.source_access_status == "CATEGORY_PAGE":
        failures.append("SOURCE: Category page, not exact job posting")

    # Gate 2: Requirement Verification
    if not opp.requirement_text or len(opp.requirement_text) < 20:
        failures.append("REQUIREMENT: No specific requirement")

    # Gate 3: Identity Verification
    if opp.person_name in ["Unknown", "Anonymous", "Reddit User", "Upwork Client"]:
        failures.append("IDENTITY: No named person")

    # Gate 4: Currentness Verification
    if opp.currentness in ["STALE", "OLD"]:
        failures.append(f"CURRENTNESS: {opp.currentness}")

    # Gate 5: Commercial Intent Verification
    if opp.outsourcing_intent not in ["EXPLICIT_OUTSOURCING", "LIKELY_OUTSOURCING"]:
        failures.append(f"COMMERCIAL: Not explicit outsourcing: {opp.outsourcing_intent}")

    # Gate 6: Competitor Detection
    competitor_keywords = ["development agency", "software agency", "web development", "app development"]
    if any(kw in opp.company_description.lower() for kw in competitor_keywords):
        failures.append("COMPETITOR: Company appears to be a development agency")

    # Gate 7: Service Match
    if opp.service_match == 0:
        failures.append("SERVICE: No service match")

    return failures


def calculate_v5_score(opp: V5Opportunity, hard_gate_failures: List[str]) -> float:
    """Calculate V5 audit score."""
    evidence_score = opp.evidence_quality
    intent_score = opp.intent_score
    icp_score = opp.icp_fit
    outsourcing_score = opp.outsourcing_fit
    service_score = opp.service_match

    penalty = len(hard_gate_failures) * 10

    raw_score = (
        evidence_score * 0.20 +
        intent_score * 0.35 +
        icp_score * 0.15 +
        outsourcing_score * 0.20 +
        service_score * 0.05
    )

    final_score = max(0, raw_score - penalty)
    return round(final_score, 1)


def main():
    """Main execution."""
    print("=" * 70)
    print("V5 FINAL OPPORTUNITY DISCOVERY & VERIFICATION")
    print("=" * 70)

    # Real opportunities discovered through websearch
    raw_opportunities = [
        # Reddit Opportunities
        {
            "opportunity_id": "V5-REDDIT-001",
            "source_type": "REDDIT",
            "source_url": "https://old.reddit.com/r/forhire/comments/1spxdi9/",
            "source_title": "[Hiring] Launch auction website with frameworks already built with AI. Budget 15k - 20k",
            "source_access_status": "ACCESSIBLE",
            "source_verification_method": "EXACT_POST_URL",
            "source_date": "3 months ago",
            "person_name": "betapunch",
            "person_role": "Business Owner",
            "person_profile_url": "https://www.reddit.com/user/betapunch",
            "person_identity_confidence": "MEDIUM",
            "company_name": "MarylandBid",
            "company_domain": "",
            "company_linkedin": "",
            "company_description": "Real estate auction marketplace for off-market assignment contracts in Maryland",
            "company_stage": "MVP Development",
            "company_size": "1-5",
            "industry": "Real Estate",
            "country": "USA",
            "prospect_type": "BUSINESS_OWNER",
            "requirement": "We are building MarylandBid, a real estate auction marketplace. Tech stack: Next.js 14, Supabase, Tailwind CSS, DocuSign API, Twilio SMS, Resend email, Stripe Connect. Need senior full-stack developer to wire it into production app, build remaining pages, set up pg_cron for auction automation, deploy to Vercel.",
            "requirement_confidence": "VERIFIED",
            "outsourcing_intent": "EXPLICIT_OUTSOURCING",
            "outsourcing_fit": 90,
            "intent_level": "ACTIVE_REQUIREMENT",
            "intent_score": 90,
            "icp_fit": 80,
            "buyability": 85,
            "evidence_quality": 95,
            "service_match": 85,
            "comai_score": 0,
            "saas_score": 90,
            "custom_software_score": 85,
            "primary_business_unit": "CUSTOM_SOFTWARE",
            "secondary_business_units": ["SAAS_DEVELOPMENT"],
            "budget_status": "VERIFIED",
            "budget": "$15,000 - $20,000",
            "evidence": [
                {
                    "claim": "Budget mentioned",
                    "value": "$15,000 - $20,000",
                    "source": "Reddit post",
                    "source_url": "https://old.reddit.com/r/forhire/comments/1spxdi9/",
                    "confidence": "VERIFIED",
                    "observed_at": "3 months ago"
                }
            ],
            "cross_source_validation": [],
            "missing_information": ["Company website", "LinkedIn profile"],
            "next_research": ["Verify company exists", "Check for website"],
            "currentness": "RECENT",
            "qualification_status": "NEEDS_RESEARCH",
            "v5_audit_score": 0,
            "audit_verdict": "UNKNOWN",
            "audit_reasons": []
        },
        {
            "opportunity_id": "V5-REDDIT-002",
            "source_type": "REDDIT",
            "source_url": "https://old.reddit.com/r/forhire/comments/1u9a9d8/",
            "source_title": "[HIRING] WordPress Developer for Entertainment News Publisher Redesign",
            "source_access_status": "ACCESSIBLE",
            "source_verification_method": "EXACT_POST_URL",
            "source_date": "1 day ago",
            "person_name": "jason23a",
            "person_role": "Business Owner",
            "person_profile_url": "https://www.reddit.com/user/jason23a",
            "person_identity_confidence": "MEDIUM",
            "company_name": "Entertainment News Publisher",
            "company_domain": "",
            "company_linkedin": "",
            "company_description": "Long-running entertainment news publisher planning major redesign",
            "company_stage": "Redesign",
            "company_size": "10-50",
            "industry": "Media & Entertainment",
            "country": "USA",
            "prospect_type": "BUSINESS_OWNER",
            "requirement": "Looking for experienced WordPress developer (or small team) with genuine publisher/media website experience. Not typical blog build. Large archive, significant mobile traffic, custom WordPress functionality, ad-supported business model. Preserving SEO while modernizing UX.",
            "requirement_confidence": "VERIFIED",
            "outsourcing_intent": "EXPLICIT_OUTSOURCING",
            "outsourcing_fit": 85,
            "intent_level": "ACTIVE_REQUIREMENT",
            "intent_score": 85,
            "icp_fit": 75,
            "buyability": 80,
            "evidence_quality": 90,
            "service_match": 80,
            "comai_score": 0,
            "saas_score": 0,
            "custom_software_score": 85,
            "primary_business_unit": "CUSTOM_SOFTWARE",
            "secondary_business_units": [],
            "budget_status": "INDICATED",
            "budget": "$15+/hr (subject to scale)",
            "evidence": [
                {
                    "claim": "Budget mentioned",
                    "value": "$15+/hr",
                    "source": "Reddit post",
                    "source_url": "https://old.reddit.com/r/forhire/comments/1u9a9d8/",
                    "confidence": "INDICATED",
                    "observed_at": "1 day ago"
                }
            ],
            "cross_source_validation": [],
            "missing_information": ["Company website", "LinkedIn profile"],
            "next_research": ["Verify company exists", "Check for website"],
            "currentness": "CURRENT",
            "qualification_status": "NEEDS_RESEARCH",
            "v5_audit_score": 0,
            "audit_verdict": "UNKNOWN",
            "audit_reasons": []
        },
        # Upwork Opportunities
        {
            "opportunity_id": "V5-UPWORK-001",
            "source_type": "UPWORK",
            "source_url": "https://www.upwork.com/freelance-jobs/apply/WhatsApp-Messaging-Automation-Bot-Development_~022031402836105408559/",
            "source_title": "WhatsApp Messaging Automation Bot Development",
            "source_access_status": "BLOCKED_BUT_URL_VALID",
            "source_verification_method": "EXACT_JOB_URL",
            "source_date": "UNKNOWN",
            "person_name": "Anonymous Upwork Client",
            "person_role": "Client",
            "person_profile_url": "",
            "person_identity_confidence": "ANONYMOUS",
            "company_name": "UNKNOWN",
            "company_domain": "",
            "company_linkedin": "",
            "company_description": "",
            "company_stage": "",
            "company_size": "",
            "industry": "",
            "country": "",
            "prospect_type": "UNKNOWN",
            "requirement": "We are looking for a skilled developer to create a WhatsApp messaging automation program that follows a predefined 5-message script. This bot should efficiently send messages in a timely manner and handle responses appropriately.",
            "requirement_confidence": "UNVERIFIED",
            "outsourcing_intent": "EXPLICIT_OUTSOURCING",
            "outsourcing_fit": 80,
            "intent_level": "ACTIVE_REQUIREMENT",
            "intent_score": 70,
            "icp_fit": 70,
            "buyability": 60,
            "evidence_quality": 50,
            "service_match": 70,
            "comai_score": 70,
            "saas_score": 0,
            "custom_software_score": 50,
            "primary_business_unit": "COMAI",
            "secondary_business_units": ["CUSTOM_SOFTWARE"],
            "budget_status": "UNKNOWN",
            "budget": "",
            "evidence": [
                {
                    "claim": "Job posting exists",
                    "value": "Exact URL with job ID",
                    "source": "Upwork",
                    "source_url": "https://www.upwork.com/freelance-jobs/apply/WhatsApp-Messaging-Automation-Bot-Development_~022031402836105408559/",
                    "confidence": "MEDIUM",
                    "observed_at": "UNKNOWN"
                }
            ],
            "cross_source_validation": [],
            "missing_information": ["Person name", "Company", "Budget", "Timeline"],
            "next_research": ["Verify job content via human", "Verify client identity"],
            "currentness": "UNKNOWN",
            "qualification_status": "NEEDS_RESEARCH",
            "v5_audit_score": 0,
            "audit_verdict": "UNKNOWN",
            "audit_reasons": []
        },
        # Freelancer.com Opportunities (from search results)
        {
            "opportunity_id": "V5-FREELANCER-001",
            "source_type": "FREELANCER",
            "source_url": "https://www.freelancer.com/jobs/chatbot/",
            "source_title": "WhatsApp Advisor Chatbot Dashboard",
            "source_access_status": "CATEGORY_PAGE",
            "source_verification_method": "CATEGORY_PAGE",
            "source_date": "6 days left",
            "person_name": "Anonymous Client",
            "person_role": "Client",
            "person_profile_url": "",
            "person_identity_confidence": "ANONYMOUS",
            "company_name": "UNKNOWN",
            "company_domain": "",
            "company_linkedin": "",
            "company_description": "",
            "company_stage": "",
            "company_size": "",
            "industry": "",
            "country": "",
            "prospect_type": "UNKNOWN",
            "requirement": "I need a full-stack solution that brings together a WhatsApp-based advisory chatbot and a web dashboard. The bot will live on the WhatsApp Business API and deliver real-time advice to my users; the dashboard will let me control everything that happens behind the scenes.",
            "requirement_confidence": "UNVERIFIED",
            "outsourcing_intent": "EXPLICIT_OUTSOURCING",
            "outsourcing_fit": 80,
            "intent_level": "ACTIVE_REQUIREMENT",
            "intent_score": 70,
            "icp_fit": 70,
            "buyability": 60,
            "evidence_quality": 50,
            "service_match": 70,
            "comai_score": 70,
            "saas_score": 50,
            "custom_software_score": 50,
            "primary_business_unit": "COMAI",
            "secondary_business_units": ["CUSTOM_SOFTWARE"],
            "budget_status": "INDICATED",
            "budget": "$23/hr average bid",
            "evidence": [
                {
                    "claim": "Job listing exists",
                    "value": "Category page with job listings",
                    "source": "Freelancer.com",
                    "source_url": "https://www.freelancer.com/jobs/chatbot/",
                    "confidence": "LOW",
                    "observed_at": "6 days left"
                }
            ],
            "cross_source_validation": [],
            "missing_information": ["Exact job URL", "Person name", "Company", "Budget"],
            "next_research": ["Find exact job URL", "Verify job content"],
            "currentness": "CURRENT",
            "qualification_status": "NEEDS_RESEARCH",
            "v5_audit_score": 0,
            "audit_verdict": "UNKNOWN",
            "audit_reasons": []
        }
    ]

    # Apply verification and scoring
    print("\n" + "=" * 70)
    print("APPLYING V5 HARD GATES")
    print("=" * 70)

    verified_opportunities = []
    for raw_opp in raw_opportunities:
        opp = V5Opportunity(raw_opp)
        hard_gate_failures = apply_hard_gates(opp)
        v5_score = calculate_v5_score(opp, hard_gate_failures)

        opp.v5_audit_score = v5_score
        opp.audit_reasons = hard_gate_failures

        if len(hard_gate_failures) == 0:
            opp.qualification_status = "HIGH_PRIORITY"
            opp.audit_verdict = "PASS"
        elif len(hard_gate_failures) <= 2:
            opp.qualification_status = "QUALIFIED"
            opp.audit_verdict = "CONDITIONAL"
        elif len(hard_gate_failures) <= 4:
            opp.qualification_status = "NEEDS_RESEARCH"
            opp.audit_verdict = "RESEARCH"
        else:
            opp.qualification_status = "REJECT"
            opp.audit_verdict = "FAIL"

        verified_opportunities.append(opp)

        print(f"\n{opp.opportunity_id}: {opp.company_name}")
        print(f"  Classification: {opp.qualification_status}")
        print(f"  V5 Score: {opp.v5_audit_score}")
        print(f"  Audit Verdict: {opp.audit_verdict}")
        if hard_gate_failures:
            print(f"  Hard Gate Failures:")
            for failure in hard_gate_failures:
                print(f"    - {failure}")

    # Generate output files
    print("\n" + "=" * 70)
    print("GENERATING OUTPUT FILES")
    print("=" * 70)

    # Generate JSON
    json_path = EXPORTS_DIR / "v5_verified_opportunities.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "audit_name": "V5 Verified Opportunity Discovery",
            "audit_date": datetime.now().isoformat(),
            "total_opportunities": len(verified_opportunities),
            "summary": {
                "HIGH_PRIORITY": len([o for o in verified_opportunities if o.qualification_status == "HIGH_PRIORITY"]),
                "QUALIFIED": len([o for o in verified_opportunities if o.qualification_status == "QUALIFIED"]),
                "NEEDS_RESEARCH": len([o for o in verified_opportunities if o.qualification_status == "NEEDS_RESEARCH"]),
                "REJECT": len([o for o in verified_opportunities if o.qualification_status == "REJECT"])
            },
            "opportunities": [opp.to_dict() for opp in verified_opportunities]
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

        for opp in verified_opportunities:
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

    # Generate Report
    txt_path = EXPORTS_DIR / "v5_adversarial_audit_report.txt"
    high_priority = [o for o in verified_opportunities if o.qualification_status == "HIGH_PRIORITY"]
    qualified = [o for o in verified_opportunities if o.qualification_status == "QUALIFIED"]
    needs_research = [o for o in verified_opportunities if o.qualification_status == "NEEDS_RESEARCH"]
    reject = [o for o in verified_opportunities if o.qualification_status == "REJECT"]

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("V5 ADVERSARIAL AUDIT — FINAL REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")

        f.write("EXECUTIVE SUMMARY:\n")
        f.write(f"  Total audited: {len(verified_opportunities)}\n")
        f.write(f"  HIGH_PRIORITY: {len(high_priority)}\n")
        f.write(f"  QUALIFIED: {len(qualified)}\n")
        f.write(f"  NEEDS_RESEARCH: {len(needs_research)}\n")
        f.write(f"  REJECT: {len(reject)}\n\n")

        f.write("=" * 70 + "\n")
        f.write("ALL LEADS — DETAILED ANALYSIS:\n")
        f.write("=" * 70 + "\n\n")

        for opp in verified_opportunities:
            f.write(f"{opp.opportunity_id}: {opp.company_name}\n")
            f.write(f"  Person: {opp.person_name} ({opp.person_role})\n")
            f.write(f"  Source: {opp.source_type}\n")
            f.write(f"  Source URL: {opp.source_url}\n")
            f.write(f"  Requirement: {opp.requirement_text[:100]}\n")
            f.write(f"  Outsourcing Intent: {opp.outsourcing_intent}\n")
            f.write(f"  Service Match: {opp.service_match}\n")
            f.write(f"  V5 Audit Score: {opp.v5_audit_score}\n")
            f.write(f"  Classification: {opp.qualification_status}\n")
            f.write(f"  Audit Verdict: {opp.audit_verdict}\n")
            if opp.audit_reasons:
                f.write(f"  Hard Gate Failures:\n")
                for reason in opp.audit_reasons:
                    f.write(f"    - {reason}\n")
            f.write("\n")

        # CTO Final Test
        f.write("=" * 70 + "\n")
        f.write("CTO FINAL TEST:\n")
        f.write("=" * 70 + "\n\n")

        if high_priority:
            f.write("HIGH_PRIORITY leads — 'Would I personally give this lead to the Inowix sales team?'\n\n")
            for opp in high_priority:
                f.write(f"  {opp.opportunity_id}: {opp.company_name}\n")
                f.write(f"    VERDICT: {opp.audit_verdict}\n")
                f.write(f"    SCORE: {opp.v5_audit_score}\n\n")
        else:
            f.write("  NO HIGH_PRIORITY LEADS FOUND.\n\n")

        if qualified:
            f.write("QUALIFIED leads — 'Would I personally give this lead to the Inowix sales team?'\n\n")
            for opp in qualified:
                f.write(f"  {opp.opportunity_id}: {opp.company_name}\n")
                f.write(f"    VERDICT: {opp.audit_verdict}\n")
                f.write(f"    SCORE: {opp.v5_audit_score}\n\n")

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

    # Print Final Summary
    print("\n" + "=" * 70)
    print("V5 FINAL SUMMARY")
    print("=" * 70)

    print(f"\nTotal Audited: {len(verified_opportunities)}")
    print(f"HIGH_PRIORITY: {len(high_priority)}")
    print(f"QUALIFIED: {len(qualified)}")
    print(f"NEEDS_RESEARCH: {len(needs_research)}")
    print(f"REJECT: {len(reject)}")

    if high_priority:
        print(f"\nHIGH_PRIORITY LEADS:")
        for opp in high_priority:
            print(f"  - {opp.opportunity_id}: {opp.company_name} (Score: {opp.v5_audit_score})")

    if qualified:
        print(f"\nQUALIFIED LEADS:")
        for opp in qualified:
            print(f"  - {opp.opportunity_id}: {opp.company_name} (Score: {opp.v5_audit_score})")

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


if __name__ == "__main__":
    main()
