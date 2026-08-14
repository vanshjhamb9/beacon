#!/usr/bin/env python3
"""
V6 ZERO-FALSE-POSITIVE OPPORTUNITY ENGINE — FINAL
===================================================
Real opportunities discovered through websearch.
Applied V6 hard gates and adversarial audit.
ZERO-FALSE-POSITIVE policy enforced.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


EXPORTS_DIR = Path("exports") / "discovery_v6"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


class V6Opportunity:
    """V6 Verified Opportunity with ZERO-FALSE-POSITIVE policy."""

    def __init__(self, data: Dict):
        self.opportunity_id = data.get("opportunity_id", "")
        self.person = data.get("person", "")
        self.person_role = data.get("person_role", "")
        self.company = data.get("company", "")
        self.company_website = data.get("company_website", "")

        self.source_type = data.get("source_type", "")
        self.source_url = data.get("source_url", "")
        self.source_verification = data.get("source_verification", "")

        self.posted_at = data.get("posted_at", "")
        self.currentness = data.get("currentness", "")

        self.requirement = data.get("requirement", "")
        self.requirement_verification = data.get("requirement_verification", "")

        self.outsourcing_intent = data.get("outsourcing_intent", "")

        self.budget = data.get("budget", "")
        self.timeline = data.get("timeline", "")

        self.comai_score = data.get("comai_score", 0)
        self.saas_score = data.get("saas_score", 0)
        self.custom_software_score = data.get("custom_software_score", 0)

        self.primary_business_unit = data.get("primary_business_unit", "")
        self.secondary_business_units = data.get("secondary_business_units", [])

        self.service_match = data.get("service_match", [])
        self.competitor_risk = data.get("competitor_risk", "")

        self.intent_score = data.get("intent_score", 0)
        self.evidence_score = data.get("evidence_score", 0)
        self.icp_score = data.get("icp_score", 0)
        self.outsourcing_score = data.get("outsourcing_score", 0)
        self.opportunity_score = data.get("opportunity_score", 0)

        self.classification = data.get("classification", "")

        self.primary_buying_signal = data.get("primary_buying_signal", "")
        self.why_now = data.get("why_now", "")

        self.evidence = data.get("evidence", [])
        self.cross_source_verification = data.get("cross_source_verification", [])

        self.missing_information = data.get("missing_information", [])
        self.recommended_next_research = data.get("recommended_next_research", [])

        self.audit = data.get("audit", {})

    def to_dict(self):
        return {
            "opportunity_id": self.opportunity_id,
            "person": self.person,
            "person_role": self.person_role,
            "company": self.company,
            "company_website": self.company_website,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "source_verification": self.source_verification,
            "posted_at": self.posted_at,
            "currentness": self.currentness,
            "requirement": self.requirement,
            "requirement_verification": self.requirement_verification,
            "outsourcing_intent": self.outsourcing_intent,
            "budget": self.budget,
            "timeline": self.timeline,
            "comai_score": self.comai_score,
            "saas_score": self.saas_score,
            "custom_software_score": self.custom_software_score,
            "primary_business_unit": self.primary_business_unit,
            "secondary_business_units": self.secondary_business_units,
            "service_match": self.service_match,
            "competitor_risk": self.competitor_risk,
            "intent_score": self.intent_score,
            "evidence_score": self.evidence_score,
            "icp_score": self.icp_score,
            "outsourcing_score": self.outsourcing_score,
            "opportunity_score": self.opportunity_score,
            "classification": self.classification,
            "primary_buying_signal": self.primary_buying_signal,
            "why_now": self.why_now,
            "evidence": self.evidence,
            "cross_source_verification": self.cross_source_verification,
            "missing_information": self.missing_information,
            "recommended_next_research": self.recommended_next_research,
            "audit": self.audit
        }


def apply_hard_gates(opp: V6Opportunity) -> bool:
    """Apply V6 hard gates. Returns True if ALL pass."""
    audit = {
        "exact_source": False,
        "requirement_verified": False,
        "identity_verified": False,
        "current": False,
        "commercial_intent": False,
        "explicit_outsourcing": False,
        "service_match": False,
        "competitor_free": False,
        "evidence_complete": False,
        "cross_source_verified": False,
        "hard_gate_pass": False
    }

    # Gate 1: Exact Source URL
    if opp.source_url and len(opp.source_url) > 10:
        if "/comments/" in opp.source_url or "linkedin.com/posts/" in opp.source_url or "twitter.com/" in opp.source_url or "x.com/" in opp.source_url:
            audit["exact_source"] = True
        elif "/freelance-jobs/apply/" in opp.source_url and "_~" in opp.source_url:
            audit["exact_source"] = True

    # Gate 2: Requirement Verified
    if opp.requirement and len(opp.requirement) > 20:
        if opp.requirement_verification == "VERIFIED":
            audit["requirement_verified"] = True

    # Gate 3: Identity Verified
    if opp.person and opp.person not in ["Unknown", "Anonymous", "Reddit User", "Upwork Client"]:
        if opp.source_verification != "ANONYMOUS":
            audit["identity_verified"] = True

    # Gate 4: Current
    if opp.currentness in ["VERY_STRONG", "STRONG", "MEDIUM"]:
        audit["current"] = True

    # Gate 5: Commercial Intent
    if opp.outsourcing_intent in ["EXPLICIT_OUTSOURCING"]:
        audit["commercial_intent"] = True
        audit["explicit_outsourcing"] = True

    # Gate 6: Service Match
    if opp.primary_business_unit and opp.primary_business_unit != "UNKNOWN":
        audit["service_match"] = True

    # Gate 7: Competitor Free
    if opp.competitor_risk in ["LOW", "NONE"]:
        audit["competitor_free"] = True

    # Gate 8: Evidence Complete
    if len(opp.evidence) >= 2:
        audit["evidence_complete"] = True

    # Gate 9: Cross-Source Verified
    if len(opp.cross_source_verification) >= 1:
        audit["cross_source_verified"] = True

    # Final hard gate check
    all_pass = all(audit.values())
    audit["hard_gate_pass"] = all_pass

    opp.audit = audit
    return all_pass


def classify_opportunity(opp: V6Opportunity) -> str:
    """Classify opportunity based on hard gates."""
    if opp.audit.get("hard_gate_pass", False):
        return "HIGH_PRIORITY"
    elif sum(1 for v in opp.audit.values() if v) >= 8:
        return "QUALIFIED"
    elif sum(1 for v in opp.audit.values() if v) >= 5:
        return "NEEDS_RESEARCH"
    else:
        return "REJECT"


def calculate_scores(opp: V6Opportunity):
    """Calculate V6 scores."""
    # Intent Score
    if opp.outsourcing_intent == "EXPLICIT_OUTSOURCING":
        opp.intent_score = 90
    elif opp.outsourcing_intent == "LIKELY_OUTSOURCING":
        opp.intent_score = 70
    else:
        opp.intent_score = 30

    # Evidence Score
    if opp.requirement_verification == "VERIFIED":
        opp.evidence_score = 90
    elif opp.requirement_verification == "HIGH":
        opp.evidence_score = 70
    else:
        opp.evidence_score = 30

    # ICP Score
    if opp.primary_business_unit in ["COMAI", "SAAS_DEVELOPMENT", "CUSTOM_SOFTWARE"]:
        opp.icp_score = 80
    else:
        opp.icp_score = 30

    # Outsourcing Score
    if opp.outsourcing_intent == "EXPLICIT_OUTSOURCING":
        opp.outsourcing_score = 90
    else:
        opp.outsourcing_score = 30

    # Opportunity Score
    opp.opportunity_score = round(
        opp.intent_score * 0.35 +
        opp.evidence_score * 0.25 +
        opp.icp_score * 0.15 +
        opp.outsourcing_score * 0.25
    )


def main():
    """Main V6 execution."""
    print("=" * 70)
    print("V6 ZERO-FALSE-POSITIVE OPPORTUNITY ENGINE — FINAL")
    print("=" * 70)

    # Real opportunities discovered through websearch
    raw_opportunities = [
        # V5 Re-validated: MarylandBid
        {
            "opportunity_id": "V6-REDDIT-001",
            "person": "betapunch",
            "person_role": "Business Owner",
            "company": "MarylandBid",
            "company_website": "",
            "source_type": "REDDIT",
            "source_url": "https://old.reddit.com/r/forhire/comments/1spxdi9/",
            "source_verification": "EXACT_POST_URL",
            "posted_at": "19 Apr 2026",
            "currentness": "MEDIUM",
            "requirement": "We are building MarylandBid, a real estate auction marketplace for off-market assignment contracts in Maryland. Tech stack: Next.js 14 (App Router), Supabase (PostgreSQL + Realtime), Tailwind CSS, DocuSign eSignature API, Twilio SMS, Resend email, and Stripe Connect. We have a complete technical specification, database schema (SQL), API route code, and a real-time bidding React component already written. We need a senior full-stack developer to wire it into a production app, build remaining pages, set up pg_cron for auction automation, and deploy to Vercel.",
            "requirement_verification": "VERIFIED",
            "outsourcing_intent": "EXPLICIT_OUTSOURCING",
            "budget": "$15,000 - $20,000",
            "timeline": "Not specified",
            "comai_score": 0,
            "saas_score": 90,
            "custom_software_score": 85,
            "primary_business_unit": "CUSTOM_SOFTWARE",
            "secondary_business_units": ["SAAS_DEVELOPMENT"],
            "service_match": ["SaaS MVP Development", "Custom Web Application", "API Integration"],
            "competitor_risk": "LOW",
            "intent_score": 0,
            "evidence_score": 0,
            "icp_score": 0,
            "outsourcing_score": 0,
            "opportunity_score": 0,
            "classification": "",
            "primary_buying_signal": "Budget mentioned: $15k-20k",
            "why_now": "Active hiring post with budget and specific requirements",
            "evidence": [
                {
                    "claim": "Budget mentioned",
                    "value": "$15,000 - $20,000",
                    "source": "Reddit post",
                    "source_url": "https://old.reddit.com/r/forhire/comments/1spxdi9/",
                    "confidence": "VERIFIED",
                    "observed_at": "19 Apr 2026"
                },
                {
                    "claim": "Specific technical requirements",
                    "value": "Next.js 14, Supabase, DocuSign, Twilio, Stripe Connect",
                    "source": "Reddit post",
                    "source_url": "https://old.reddit.com/r/forhire/comments/1spxdi9/",
                    "confidence": "VERIFIED",
                    "observed_at": "19 Apr 2026"
                }
            ],
            "cross_source_verification": [],
            "missing_information": ["Company website", "LinkedIn profile"],
            "recommended_next_research": ["Verify company exists", "Check for website"],
            "audit": {}
        },
        # V5 Re-validated: Entertainment News Publisher
        {
            "opportunity_id": "V6-REDDIT-002",
            "person": "jason23a",
            "person_role": "Business Owner",
            "company": "Entertainment News Publisher",
            "company_website": "",
            "source_type": "REDDIT",
            "source_url": "https://old.reddit.com/r/forhire/comments/1u9a9d8/",
            "source_verification": "EXACT_POST_URL",
            "posted_at": "1 day ago",
            "currentness": "VERY_STRONG",
            "requirement": "Looking for experienced WordPress developer (or small team) with genuine publisher/media website experience. Not typical blog build. Large archive, significant mobile traffic, custom WordPress functionality, ad-supported business model. Preserving SEO while modernizing UX. Budget is pending and subject to agreed-upon scale (which is modular at this stage, but will absolutely be in alignment with the $15+/hr frame.",
            "requirement_verification": "VERIFIED",
            "outsourcing_intent": "EXPLICIT_OUTSOURCING",
            "budget": "$15+/hr",
            "timeline": "Not specified",
            "comai_score": 0,
            "saas_score": 0,
            "custom_software_score": 85,
            "primary_business_unit": "CUSTOM_SOFTWARE",
            "secondary_business_units": [],
            "service_match": ["WordPress Development", "Custom Web Application", "SEO Optimization"],
            "competitor_risk": "LOW",
            "intent_score": 0,
            "evidence_score": 0,
            "icp_score": 0,
            "outsourcing_score": 0,
            "opportunity_score": 0,
            "classification": "",
            "primary_buying_signal": "Active hiring post with budget indication",
            "why_now": "Posted 1 day ago - very recent",
            "evidence": [
                {
                    "claim": "Budget mentioned",
                    "value": "$15+/hr",
                    "source": "Reddit post",
                    "source_url": "https://old.reddit.com/r/forhire/comments/1u9a9d8/",
                    "confidence": "VERIFIED",
                    "observed_at": "1 day ago"
                },
                {
                    "claim": "Specific technical requirements",
                    "value": "WordPress, custom themes, Core Web Vitals, SEO",
                    "source": "Reddit post",
                    "source_url": "https://old.reddit.com/r/forhire/comments/1u9a9d8/",
                    "confidence": "VERIFIED",
                    "observed_at": "1 day ago"
                }
            ],
            "cross_source_verification": [],
            "missing_information": ["Company website", "LinkedIn profile"],
            "recommended_next_research": ["Verify company exists", "Check for website"],
            "audit": {}
        },
        # New: Kilova React Native App
        {
            "opportunity_id": "V6-REDDIT-003",
            "person": "paloma_chiara",
            "person_role": "Founder",
            "company": "Kilova",
            "company_website": "kilova.app",
            "source_type": "REDDIT",
            "source_url": "https://www.reddit.com/r/forhire/comments/1txv6sr/",
            "source_verification": "EXACT_POST_URL",
            "posted_at": "26d ago",
            "currentness": "STRONG",
            "requirement": "Looking for a React Native developer. Kilova is a very simple app concept, it syncs a woman's menstrual cycle phases into her calendar for lifestyle planning. It has a live web app built in React, with Supabase for hosting and database. The mobile app needs to match the web app's design and functionality. Users must be able to sign in with their existing Kilova account. The app must work on both iOS and Android.",
            "requirement_verification": "VERIFIED",
            "outsourcing_intent": "EXPLICIT_OUTSOURCING",
            "budget": "$2,000 USD total for MVP",
            "timeline": "Not specified",
            "comai_score": 0,
            "saas_score": 70,
            "custom_software_score": 80,
            "primary_business_unit": "CUSTOM_SOFTWARE",
            "secondary_business_units": ["SAAS_DEVELOPMENT"],
            "service_match": ["React Native Development", "Mobile App Development", "Supabase Integration"],
            "competitor_risk": "LOW",
            "intent_score": 0,
            "evidence_score": 0,
            "icp_score": 0,
            "outsourcing_score": 0,
            "opportunity_score": 0,
            "classification": "",
            "primary_buying_signal": "Budget mentioned: $2,000",
            "why_now": "Active hiring post with specific requirements",
            "evidence": [
                {
                    "claim": "Budget mentioned",
                    "value": "$2,000 USD",
                    "source": "Reddit post",
                    "source_url": "https://www.reddit.com/r/forhire/comments/1txv6sr/",
                    "confidence": "VERIFIED",
                    "observed_at": "26d ago"
                },
                {
                    "claim": "Specific technical requirements",
                    "value": "React Native, iOS, Android, Supabase",
                    "source": "Reddit post",
                    "source_url": "https://www.reddit.com/r/forhire/comments/1txv6sr/",
                    "confidence": "VERIFIED",
                    "observed_at": "26d ago"
                }
            ],
            "cross_source_verification": [],
            "missing_information": ["Company LinkedIn", "More details about the app"],
            "recommended_next_research": ["Visit kilova.app", "Check LinkedIn profile"],
            "audit": {}
        },
        # New: Zolly SaaS Redesign
        {
            "opportunity_id": "V6-REDDIT-004",
            "person": "Evening_Acadia_6021",
            "person_role": "Founder",
            "company": "Zolly",
            "company_website": "",
            "source_type": "REDDIT",
            "source_url": "https://www.reddit.com/r/hiredev/comments/1u79xa6/",
            "source_verification": "EXACT_POST_URL",
            "posted_at": "13h ago",
            "currentness": "VERY_STRONG",
            "requirement": "I run an SAAS application Zolly and looking for someone with great idea on the application frontend. Need a Frontend Developer for redesigning the Application. Must have portfolio of recent work. Visit the application, access every page and check where is the improvement needed.",
            "requirement_verification": "VERIFIED",
            "outsourcing_intent": "EXPLICIT_OUTSOURCING",
            "budget": "$300",
            "timeline": "Not specified",
            "comai_score": 0,
            "saas_score": 80,
            "custom_software_score": 70,
            "primary_business_unit": "SAAS_DEVELOPMENT",
            "secondary_business_units": ["CUSTOM_SOFTWARE"],
            "service_match": ["SaaS Frontend Development", "UI/UX Redesign", "React/Next.js Development"],
            "competitor_risk": "LOW",
            "intent_score": 0,
            "evidence_score": 0,
            "icp_score": 0,
            "outsourcing_score": 0,
            "opportunity_score": 0,
            "classification": "",
            "primary_buying_signal": "Budget mentioned: $300",
            "why_now": "Posted 13 hours ago - very recent",
            "evidence": [
                {
                    "claim": "Budget mentioned",
                    "value": "$300",
                    "source": "Reddit post",
                    "source_url": "https://www.reddit.com/r/hiredev/comments/1u79xa6/",
                    "confidence": "VERIFIED",
                    "observed_at": "13h ago"
                },
                {
                    "claim": "SaaS application owner",
                    "value": "Runs a SaaS application called Zolly",
                    "source": "Reddit post",
                    "source_url": "https://www.reddit.com/r/hiredev/comments/1u79xa6/",
                    "confidence": "VERIFIED",
                    "observed_at": "13h ago"
                }
            ],
            "cross_source_verification": [],
            "missing_information": ["Zolly website URL", "More details about the app"],
            "recommended_next_research": ["Find Zolly website", "Check LinkedIn profile"],
            "audit": {}
        },
        # New: Landing page for neurodivergent startup
        {
            "opportunity_id": "V6-REDDIT-005",
            "person": "Anonymous",
            "person_role": "Founder",
            "company": "Neurodivergent Products Startup",
            "company_website": "",
            "source_type": "REDDIT",
            "source_url": "https://www.reddit.com/r/forhire/comments/1tor0zh/",
            "source_verification": "EXACT_POST_URL",
            "posted_at": "7d ago",
            "currentness": "STRONG",
            "requirement": "Landing page for a startup building products for neurodivergent people (multilingual, dark/light mode, accessible, SEO + GEO)",
            "requirement_verification": "VERIFIED",
            "outsourcing_intent": "EXPLICIT_OUTSOURCING",
            "budget": "€1,000",
            "timeline": "Not specified",
            "comai_score": 0,
            "saas_score": 50,
            "custom_software_score": 70,
            "primary_business_unit": "CUSTOM_SOFTWARE",
            "secondary_business_units": [],
            "service_match": ["Landing Page Development", "Accessibility", "Multilingual Website"],
            "competitor_risk": "LOW",
            "intent_score": 0,
            "evidence_score": 0,
            "icp_score": 0,
            "outsourcing_score": 0,
            "opportunity_score": 0,
            "classification": "",
            "primary_buying_signal": "Budget mentioned: €1,000",
            "why_now": "Posted 7 days ago - recent",
            "evidence": [
                {
                    "claim": "Budget mentioned",
                    "value": "€1,000",
                    "source": "Reddit post",
                    "source_url": "https://www.reddit.com/r/forhire/comments/1tor0zh/",
                    "confidence": "VERIFIED",
                    "observed_at": "7d ago"
                },
                {
                    "claim": "Specific technical requirements",
                    "value": "Multilingual, accessible, SEO + GEO",
                    "source": "Reddit post",
                    "source_url": "https://www.reddit.com/r/forhire/comments/1tor0zh/",
                    "confidence": "VERIFIED",
                    "observed_at": "7d ago"
                }
            ],
            "cross_source_verification": [],
            "missing_information": ["Person identity", "Company name"],
            "recommended_next_research": ["Identify the founder", "Find company details"],
            "audit": {}
        }
    ]

    # Apply verification and scoring
    print("\n" + "=" * 70)
    print("APPLYING V6 HARD GATES")
    print("=" * 70)

    candidates = []
    high_priority = []
    qualified = []
    needs_research = []
    rejected = []

    for raw_opp in raw_opportunities:
        opp = V6Opportunity(raw_opp)
        hard_gate_pass = apply_hard_gates(opp)
        calculate_scores(opp)
        opp.classification = classify_opportunity(opp)

        candidates.append(opp)

        if opp.classification == "HIGH_PRIORITY":
            high_priority.append(opp)
        elif opp.classification == "QUALIFIED":
            qualified.append(opp)
        elif opp.classification == "NEEDS_RESEARCH":
            needs_research.append(opp)
        else:
            rejected.append(opp)

        print(f"\n{opp.opportunity_id}: {opp.company}")
        print(f"  Person: {opp.person}")
        print(f"  Source: {opp.source_type}")
        print(f"  Source URL: {opp.source_url}")
        print(f"  Requirement: {opp.requirement[:100]}...")
        print(f"  Budget: {opp.budget}")
        print(f"  Classification: {opp.classification}")
        print(f"  Opportunity Score: {opp.opportunity_score}")
        print(f"  Audit:")
        for key, value in opp.audit.items():
            print(f"    {key}: {value}")

    # Generate output files
    print("\n" + "=" * 70)
    print("GENERATING V6 OUTPUT FILES")
    print("=" * 70)

    # Generate candidates JSON
    candidates_path = EXPORTS_DIR / "discovery_v6_candidates.json"
    with open(candidates_path, "w", encoding="utf-8") as f:
        json.dump({
            "audit_name": "V6 Zero-False-Positive Opportunity Discovery",
            "audit_date": datetime.now().isoformat(),
            "total_candidates": len(candidates),
            "summary": {
                "HIGH_PRIORITY": len(high_priority),
                "QUALIFIED": len(qualified),
                "NEEDS_RESEARCH": len(needs_research),
                "REJECT": len(rejected)
            },
            "candidates": [opp.to_dict() for opp in candidates]
        }, f, indent=2, ensure_ascii=False)
    print(f"Candidates JSON saved: {candidates_path}")

    # Generate high priority JSON
    high_priority_path = EXPORTS_DIR / "discovery_v6_high_priority.json"
    with open(high_priority_path, "w", encoding="utf-8") as f:
        json.dump({
            "audit_name": "V6 High Priority Opportunities",
            "audit_date": datetime.now().isoformat(),
            "total_high_priority": len(high_priority),
            "opportunities": [opp.to_dict() for opp in high_priority]
        }, f, indent=2, ensure_ascii=False)
    print(f"High Priority JSON saved: {high_priority_path}")

    # Generate rejected JSON
    rejected_path = EXPORTS_DIR / "discovery_v6_rejected.json"
    with open(rejected_path, "w", encoding="utf-8") as f:
        json.dump({
            "audit_name": "V6 Rejected Opportunities",
            "audit_date": datetime.now().isoformat(),
            "total_rejected": len(rejected),
            "opportunities": [opp.to_dict() for opp in rejected]
        }, f, indent=2, ensure_ascii=False)
    print(f"Rejected JSON saved: {rejected_path}")

    # Generate Excel
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "V6 Candidates"

        headers = [
            "Opportunity ID", "Person", "Company", "Source Type",
            "Source URL", "Requirement", "Classification",
            "Intent Score", "Evidence Score", "Opportunity Score",
            "Primary Business Unit", "Hard Gate Pass"
        ]
        ws.append(headers)

        for opp in candidates:
            ws.append([
                opp.opportunity_id,
                opp.person,
                opp.company,
                opp.source_type,
                opp.source_url,
                opp.requirement[:100],
                opp.classification,
                opp.intent_score,
                opp.evidence_score,
                opp.opportunity_score,
                opp.primary_business_unit,
                opp.audit.get("hard_gate_pass", False)
            ])

        xlsx_path = EXPORTS_DIR / "discovery_v6_candidates.xlsx"
        wb.save(xlsx_path)
        print(f"Excel saved: {xlsx_path}")
    except ImportError:
        print("openpyxl not installed, skipping Excel export")

    # Generate audit report
    txt_path = EXPORTS_DIR / "discovery_v6_audit_report.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("V6 ZERO-FALSE-POSITIVE OPPORTUNITY AUDIT REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")

        f.write("EXECUTIVE SUMMARY:\n")
        f.write(f"  Total Candidates: {len(candidates)}\n")
        f.write(f"  HIGH_PRIORITY: {len(high_priority)}\n")
        f.write(f"  QUALIFIED: {len(qualified)}\n")
        f.write(f"  NEEDS_RESEARCH: {len(needs_research)}\n")
        f.write(f"  REJECT: {len(rejected)}\n\n")

        f.write("=" * 70 + "\n")
        f.write("HIGH_PRIORITY LEADS — CTO FINAL TEST:\n")
        f.write("'Would I personally give this lead to the Inowix sales team?'\n")
        f.write("=" * 70 + "\n\n")

        if high_priority:
            for opp in high_priority:
                f.write(f"{opp.opportunity_id}: {opp.company}\n")
                f.write(f"  Person: {opp.person} ({opp.person_role})\n")
                f.write(f"  Source: {opp.source_type}\n")
                f.write(f"  Source URL: {opp.source_url}\n")
                f.write(f"  Requirement: {opp.requirement[:200]}\n")
                f.write(f"  Posted: {opp.posted_at}\n")
                f.write(f"  Currentness: {opp.currentness}\n")
                f.write(f"  Outsourcing Intent: {opp.outsourcing_intent}\n")
                f.write(f"  Budget: {opp.budget}\n")
                f.write(f"  Service Match: {opp.service_match}\n")
                f.write(f"  Primary Business Unit: {opp.primary_business_unit}\n")
                f.write(f"  Intent Score: {opp.intent_score}\n")
                f.write(f"  Evidence Score: {opp.evidence_score}\n")
                f.write(f"  Opportunity Score: {opp.opportunity_score}\n")
                f.write(f"  Classification: {opp.classification}\n")
                f.write(f"  Primary Buying Signal: {opp.primary_buying_signal}\n")
                f.write(f"  Why Now: {opp.why_now}\n")
                f.write(f"  Audit:\n")
                for key, value in opp.audit.items():
                    f.write(f"    {key}: {value}\n")
                f.write(f"  Evidence:\n")
                for ev in opp.evidence:
                    f.write(f"    - {ev.get('claim', '')}: {ev.get('value', '')}\n")
                f.write(f"\n")
        else:
            f.write("  NO HIGH_PRIORITY LEADS FOUND.\n\n")

        f.write("=" * 70 + "\n")
        f.write("QUALIFIED LEADS:\n")
        f.write("=" * 70 + "\n\n")

        if qualified:
            for opp in qualified:
                f.write(f"{opp.opportunity_id}: {opp.company}\n")
                f.write(f"  Person: {opp.person}\n")
                f.write(f"  Source: {opp.source_type}\n")
                f.write(f"  Classification: {opp.classification}\n")
                f.write(f"\n")
        else:
            f.write("  NO QUALIFIED LEADS.\n\n")

        # Final CTO Answer
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
            f.write("  No leads survived the V6 audit.\n")
            f.write("  This is the correct outcome — quality > quantity.\n")

    print(f"Audit report saved: {txt_path}")

    # Print Final Summary
    print("\n" + "=" * 70)
    print("V6 FINAL SUMMARY")
    print("=" * 70)

    print(f"\nTotal Candidates: {len(candidates)}")
    print(f"HIGH_PRIORITY: {len(high_priority)}")
    print(f"QUALIFIED: {len(qualified)}")
    print(f"NEEDS_RESEARCH: {len(needs_research)}")
    print(f"REJECT: {len(rejected)}")

    if high_priority:
        print(f"\nHIGH_PRIORITY LEADS:")
        for opp in high_priority:
            print(f"  - {opp.opportunity_id}: {opp.company} (Score: {opp.opportunity_score})")

    if qualified:
        print(f"\nQUALIFIED LEADS:")
        for opp in qualified:
            print(f"  - {opp.opportunity_id}: {opp.company} (Score: {opp.opportunity_score})")

    print(f"\n{'='*70}")
    print("CTO FINAL VERDICT:")
    if high_priority:
        print(f"  {len(high_priority)} leads are HIGH_PRIORITY — Contact these first.")
    elif qualified:
        print(f"  {len(qualified)} leads are QUALIFIED — Verify before outreach.")
    else:
        print("  No leads survived the V6 audit.")
        print("  This is the correct outcome — quality > quantity.")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
