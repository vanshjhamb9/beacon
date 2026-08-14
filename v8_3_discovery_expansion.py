"""
BEACON V8.3 — CONTACTABLE BUYING-EVENT DISCOVERY EXPANSION
============================================================
CTO DIRECTIVE: V8.2 gates working. Do NOT weaken them.
Problem is DISCOVERY SOURCE QUALITY, not verification.
Find new buying events where buyer + business + requirement + contact can be verified.
Quality > quantity. 0 SALES_READY is acceptable.
"""

import json
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path

# ============================================================
# OUTPUT DIRECTORY
# ============================================================
OUTPUT_DIR = Path("exports/discovery_v8_3")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = datetime.now()
TODAY_STR = TODAY.strftime("%Y-%m-%d")

# ============================================================
# V8.2 GATES (DO NOT MODIFY)
# ============================================================
V8_2_GATES = {
    "requirement_verified": "Must be TRUE from public evidence",
    "currentness_status": "Must be CURRENT (0-30 days preferred)",
    "decision_maker_confidence": "Must be HIGH",
    "outsourcing_intent": "Must be EXPLICIT (not hiring, not cofounder)",
    "company_or_project_verified": "Must be TRUE",
    "service_match_confidence": "Must be HIGH",
    "contactability": "Must be HIGH",
    "primary_contact_status": "Must be VERIFIED (not PUBLIC_UNVERIFIED)",
    "contact_owner_match": "Must be VERIFIED",
    "evidence_reproducibility": "Must be TRUE",
    "competitor": "Must be FALSE",
    "safety_clear": "Must be TRUE",
    "cto_15_minute_test": "Must be YES",
}

# ============================================================
# CONTACTABILITY DISCOVERY PRIORITY (NEW IN V8.3)
# ============================================================
CONTACT_PRIORITY = {
    "VERY_HIGH": "Named founder + current buying event + explicit outsourcing + verified business + public direct contact",
    "HIGH": "Named buyer + current buying event + explicit outsourcing + reliable direct/platform contact",
    "MEDIUM": "Named buyer + current requirement + contact route exists but ownership requires verification",
    "LOW": "Anonymous / generic contact / weak identity / stale requirement",
}

# ============================================================
# SEARCH STRATEGY
# ============================================================
SEARCH_TIERS = {
    "TIER_1": [
        "Founder posts requesting developers",
        "Founder personal websites with project requests",
        "Public RFPs with organization/contact information",
        "Startup founder communities with identifiable profiles",
        "Public business-owner requests",
        "Public procurement opportunities",
        "Public project/request pages containing contact information",
        "Founder newsletters/blog posts asking for development help",
        "Startup communities where founder identity is visible",
        "Public technical project requests linked to a real founder/company",
        "Business owners posting explicit agency/developer requirements",
        "Public 'looking for development agency/team' requests",
    ],
    "TIER_2": [
        "Reddit exact posts",
        "LinkedIn public posts",
        "Indie Hackers",
        "Product Hunt founder discussions",
        "GitHub discussions/issues when clearly tied to a commercial project",
        "Public startup communities",
        "Public social posts",
    ],
    "TIER_3": [
        "Google search (discovery only)",
        "Upwork search (discovery only)",
        "Freelancer search (discovery only)",
        "Fiverr (discovery only)",
        "Job boards (discovery only)",
        "LinkedIn search (discovery only)",
        "Product Hunt listings (discovery only)",
    ],
}

# ============================================================
# SEARCH QUERIES
# ============================================================
SEARCH_QUERIES = [
    # Tier 1 - Direct founder requests
    '"looking for development agency"',
    '"need development team"',
    '"looking for software agency"',
    '"need React Native developer agency"',
    '"looking for SaaS development team"',
    '"need MVP development team"',
    '"looking for technical team"',
    '"need external development team"',
    '"looking for contractors"',
    '"need someone to build my SaaS"',
    '"looking for Shopify developer"',
    '"need WhatsApp chatbot"',
    '"need AI automation"',
    '"need mobile app development"',
    # Combined with buyer signals
    'founder "looking for developer"',
    'startup "need agency"',
    'business "looking for development team"',
    # Service-specific
    '"WhatsApp chatbot" founder need',
    '"AI automation" business need',
    '"Shopify" developer need founder',
    '"SaaS MVP" founder need developer',
]

# ============================================================
# CTO 15-MINUTE TEST
# ============================================================
def cto_15_minute_test(candidate: dict) -> tuple:
    """
    "If I were the founder of Inowix, would I personally spend
    15 minutes contacting this buyer today?"
    Returns (YES/NO, reason)
    """
    # Check all V8.2 gates
    failed_gates = []

    if not candidate.get("requirement_verified"):
        failed_gates.append("requirement_verified")
    if candidate.get("currentness_status") not in ["CURRENT"]:
        failed_gates.append("currentness_status")
    if candidate.get("decision_maker_confidence") != "HIGH":
        failed_gates.append("decision_maker_confidence")
    if candidate.get("outsourcing_intent") != "EXPLICIT":
        failed_gates.append("outsourcing_intent")
    if not candidate.get("company_or_project_verified"):
        failed_gates.append("company_or_project_verified")
    if candidate.get("service_match_confidence") != "HIGH":
        failed_gates.append("service_match_confidence")
    if candidate.get("contactability") != "HIGH":
        failed_gates.append("contactability")
    if candidate.get("primary_contact_status") != "VERIFIED":
        failed_gates.append("primary_contact_status")
    if candidate.get("contact_owner_match") != "VERIFIED":
        failed_gates.append("contact_owner_match")
    if not candidate.get("evidence_reproducibility"):
        failed_gates.append("evidence_reproducibility")
    if candidate.get("competitor"):
        failed_gates.append("competitor")
    if not candidate.get("safety_clear"):
        failed_gates.append("safety_clear")

    if failed_gates:
        return "NO", f"Failed gates: {', '.join(failed_gates)}"
    return "YES", "All V8.2 gates passed"

# ============================================================
# RESEARCH FINDINGS
# ============================================================
"""
SEARCH RESULTS ANALYSIS (V8.3 Discovery Run)

Searches performed:
1. "looking for development agency" / "need development team" / etc. → Mostly agency listings, not buying events
2. Reddit r/forhire, r/startups, r/SaaS, r/Entrepreneur → Mostly job seekers and agencies
3. Indie Hackers / Product Hunt → Mostly job seekers and agency promotions
4. Founder + developer need combinations → Mostly articles about how to find developers
5. Service-specific searches (WhatsApp chatbot, AI automation, Shopify) → Mostly vendor comparisons

KEY FINDINGS:
- Public search results are SATURATED with service providers selling development services
- Most "hiring" posts are for full-time employment, not outsourcing
- Most "looking for developer" posts are from job seekers, not buyers
- Cofounder searches are equity-based, not outsourcing
- Reddit blocks direct access to verify post details
- No public RFPs with contact information found in our service areas
- No founder blog posts/newsletters requesting development help found
- No public procurement opportunities matching our services found

PROSPECTIVE CANDIDATES IDENTIFIED (UNVERIFIED - contact details not publicly accessible):
"""

# ============================================================
# CANDIDATES (honestly assessed)
# ============================================================
candidates = []

# Candidate 1: Dubai Textile Business - AI Automation
candidates.append({
    "opportunity_id": "V8-003",
    "person_name": "UNKNOWN (Reddit poster)",
    "person_role": "Business Owner",
    "company_name": "Textile Business (Dubai)",
    "company_url": "UNKNOWN",
    "product_url": "UNKNOWN",

    "requirement": "Need AI/Automation freelancer for textile business accounts, stock & workflow system",
    "requirement_verified": False,  # Cannot verify - Reddit blocks access
    "requirement_evidence": [{
        "claim": "Reddit post title indicates AI automation need",
        "source": "Reddit r/jobsdubai",
        "source_url": "https://www.reddit.com/r/jobsdubai/comments/1u6mewx/",
        "confidence": "UNVERIFIED",
        "observed_at": TODAY_STR,
    }],

    "source_name": "Reddit r/jobsdubai",
    "source_url": "https://www.reddit.com/r/jobsdubai/comments/1u6mewx/",
    "source_status": "ACCESS_BLOCKED",
    "source_post_id": "1u6mewx",
    "published_at": "2026-07-27",  # ~12 days ago from search
    "observed_at": TODAY_STR,

    "identity_confidence": "UNKNOWN",
    "identity_evidence": [],

    "company_status": "UNVERIFIED",
    "company_evidence": [],

    "currentness_status": "CURRENT",
    "age_days": 12,
    "currentness_evidence": [{
        "claim": "Post observed ~12 days old",
        "source": "Search results",
        "confidence": "APPROXIMATE",
    }],

    "outsourcing_intent": "EXPLICIT",
    "outsourcing_confidence": "HIGH",
    "outsourcing_evidence": [{
        "claim": "Post explicitly requests freelancer for business automation",
        "source": "Reddit post title",
        "confidence": "HIGH",
    }],

    "service_match": "AI Automation / Workflow",
    "service_match_confidence": "HIGH",
    "service_match_evidence": [{
        "claim": "Request matches AI automation and workflow system services",
        "source": "Post content",
        "confidence": "HIGH",
    }],

    "email": "UNKNOWN",
    "email_status": "UNKNOWN",
    "email_evidence": [],

    "linkedin_url": "UNKNOWN",
    "linkedin_status": "UNKNOWN",
    "linkedin_evidence": [],

    "platform_contact": "Reddit DM (presumed)",
    "platform_contact_status": "UNKNOWN",

    "contactability": "LOW",
    "contactability_discovery_priority": "MEDIUM",
    "contactability_evidence": [{
        "claim": "Reddit post exists but contact details not publicly visible",
        "source": "Search results",
        "confidence": "LOW",
    }],

    "contact_owner_match": "UNKNOWN",

    "evidence_reproducibility": False,  # Cannot access Reddit to verify

    "competitor": False,
    "safety_clear": True,

    "opportunity_verdict": "NEEDS_RESEARCH",
    "final_salesability": "NEEDS_RESEARCH",

    "cto_15_minute_test": "NO",
    "cto_decision_reason": "Cannot verify requirement details, contact information, or business identity. Reddit blocks access. Contact owner match UNKNOWN.",

    "rejection_reasons": [
        "Failed gate: requirement_verified (cannot access Reddit)",
        "Failed gate: primary_contact_status (contact UNKNOWN)",
        "Failed gate: contact_owner_match (UNKNOWN)",
        "Failed gate: evidence_reproducibility (cannot verify)",
    ],
})

# Candidate 2: SaaS MVP Builder (r/smallbusiness)
candidates.append({
    "opportunity_id": "V8-004",
    "person_name": "UNKNOWN (Reddit poster)",
    "person_role": "Founder",
    "company_name": "UNKNOWN (SaaS startup)",
    "company_url": "UNKNOWN",
    "product_url": "UNKNOWN",

    "requirement": "Need advice on hiring for SaaS MVP - experienced engineer vs freelancers vs interns",
    "requirement_verified": False,
    "requirement_evidence": [{
        "claim": "Reddit post seeking advice on building SaaS MVP",
        "source": "Reddit r/smallbusiness",
        "source_url": "https://www.reddit.com/r/smallbusiness/comments/1uljsrj/",
        "confidence": "UNVERIFIED",
        "observed_at": TODAY_STR,
    }],

    "source_name": "Reddit r/smallbusiness",
    "source_url": "https://www.reddit.com/r/smallbusiness/comments/1uljsrj/",
    "source_status": "ACCESS_BLOCKED",
    "source_post_id": "1uljsrj",
    "published_at": "2026-07-31",  # ~8 days ago
    "observed_at": TODAY_STR,

    "identity_confidence": "UNKNOWN",
    "identity_evidence": [],

    "company_status": "UNVERIFIED",
    "company_evidence": [],

    "currentness_status": "CURRENT",
    "age_days": 8,
    "currentness_evidence": [{
        "claim": "Post observed ~8 days old",
        "source": "Search results",
        "confidence": "APPROXIMATE",
    }],

    "outsourcing_intent": "IMPLICIT",  # Seeking advice, not explicitly requesting agency
    "outsourcing_confidence": "MEDIUM",
    "outsourcing_evidence": [{
        "claim": "Post asks about hiring options including freelancers and agencies",
        "source": "Post title",
        "confidence": "MEDIUM",
    }],

    "service_match": "SaaS MVP Development",
    "service_match_confidence": "HIGH",
    "service_match_evidence": [{
        "claim": "Request is about building a SaaS MVP",
        "source": "Post content",
        "confidence": "HIGH",
    }],

    "email": "UNKNOWN",
    "email_status": "UNKNOWN",
    "email_evidence": [],

    "linkedin_url": "UNKNOWN",
    "linkedin_status": "UNKNOWN",
    "linkedin_evidence": [],

    "platform_contact": "Reddit DM (presumed)",
    "platform_contact_status": "UNKNOWN",

    "contactability": "LOW",
    "contactability_discovery_priority": "LOW",
    "contactability_evidence": [{
        "claim": "Reddit post exists but contact details not publicly visible",
        "source": "Search results",
        "confidence": "LOW",
    }],

    "contact_owner_match": "UNKNOWN",

    "evidence_reproducibility": False,

    "competitor": False,
    "safety_clear": True,

    "opportunity_verdict": "NEEDS_RESEARCH",
    "final_salesability": "NEEDS_RESEARCH",

    "cto_15_minute_test": "NO",
    "cto_decision_reason": "Seeking advice, not explicitly requesting agency. Contact details UNKNOWN. Cannot verify.",

    "rejection_reasons": [
        "Failed gate: outsourcing_intent (IMPLICIT, not EXPLICIT)",
        "Failed gate: primary_contact_status (UNKNOWN)",
        "Failed gate: contact_owner_match (UNKNOWN)",
        "Failed gate: evidence_reproducibility (cannot verify)",
    ],
})

# Candidate 3: Startup Software Development (r/developers_hire)
candidates.append({
    "opportunity_id": "V8-005",
    "person_name": "UNKNOWN (Reddit poster)",
    "person_role": "Founder",
    "company_name": "Startup (unnamed)",
    "company_url": "UNKNOWN",
    "product_url": "UNKNOWN",

    "requirement": "Needing software developed for startup company",
    "requirement_verified": False,
    "requirement_evidence": [{
        "claim": "Reddit post requesting software development for startup",
        "source": "Reddit r/developers_hire",
        "source_url": "https://www.reddit.com/r/developers_hire/comments/1u2fuh2/",
        "confidence": "UNVERIFIED",
        "observed_at": TODAY_STR,
    }],

    "source_name": "Reddit r/developers_hire",
    "source_url": "https://www.reddit.com/r/developers_hire/comments/1u2fuh2/",
    "source_status": "ACCESS_BLOCKED",
    "source_post_id": "1u2fuh2",
    "published_at": "2026-07-25",  # ~14 days ago
    "observed_at": TODAY_STR,

    "identity_confidence": "UNKNOWN",
    "identity_evidence": [],

    "company_status": "UNVERIFIED",
    "company_evidence": [],

    "currentness_status": "CURRENT",
    "age_days": 14,
    "currentness_evidence": [{
        "claim": "Post observed ~14 days old",
        "source": "Search results",
        "confidence": "APPROXIMATE",
    }],

    "outsourcing_intent": "EXPLICIT",
    "outsourcing_confidence": "HIGH",
    "outsourcing_evidence": [{
        "claim": "Post explicitly requests software development for startup",
        "source": "Post title",
        "confidence": "HIGH",
    }],

    "service_match": "Custom Software Development",
    "service_match_confidence": "MEDIUM",  # Unknown what type of software
    "service_match_evidence": [{
        "claim": "Generic software development request - could match custom software services",
        "source": "Post title",
        "confidence": "MEDIUM",
    }],

    "email": "UNKNOWN",
    "email_status": "UNKNOWN",
    "email_evidence": [],

    "linkedin_url": "UNKNOWN",
    "linkedin_status": "UNKNOWN",
    "linkedin_evidence": [],

    "platform_contact": "Reddit DM (presumed)",
    "platform_contact_status": "UNKNOWN",

    "contactability": "LOW",
    "contactability_discovery_priority": "MEDIUM",
    "contactability_evidence": [{
        "claim": "Reddit post exists but contact details not publicly visible",
        "source": "Search results",
        "confidence": "LOW",
    }],

    "contact_owner_match": "UNKNOWN",

    "evidence_reproducibility": False,

    "competitor": False,
    "safety_clear": True,

    "opportunity_verdict": "NEEDS_RESEARCH",
    "final_salesability": "NEEDS_RESEARCH",

    "cto_15_minute_test": "NO",
    "cto_decision_reason": "Requirement too vague - unknown what software is needed. Contact details UNKNOWN. Cannot verify.",

    "rejection_reasons": [
        "Failed gate: service_match_confidence (MEDIUM - unknown software type)",
        "Failed gate: primary_contact_status (UNKNOWN)",
        "Failed gate: contact_owner_match (UNKNOWN)",
        "Failed gate: evidence_reproducibility (cannot verify)",
    ],
})

# Candidate 4: App Designer/Developer (r/AppDevelopers)
candidates.append({
    "opportunity_id": "V8-006",
    "person_name": "UNKNOWN (Reddit poster: T13961876)",
    "person_role": "Founder/Product Owner",
    "company_name": "UNKNOWN (app project)",
    "company_url": "UNKNOWN",
    "product_url": "UNKNOWN",

    "requirement": "Looking for app designer/developer - has prototype, needs design improvement and coding help",
    "requirement_verified": False,
    "requirement_evidence": [{
        "claim": "Reddit post seeking app designer/developer for prototype improvement",
        "source": "Reddit r/AppDevelopers",
        "source_url": "https://www.reddit.com/r/AppDevelopers/comments/1uf84eb/",
        "confidence": "UNVERIFIED",
        "observed_at": TODAY_STR,
    }],

    "source_name": "Reddit r/AppDevelopers",
    "source_url": "https://www.reddit.com/r/AppDevelopers/comments/1uf84eb/",
    "source_status": "ACCESS_BLOCKED",
    "source_post_id": "1uf84eb",
    "published_at": "2026-08-08",  # ~11 hours ago (very fresh)
    "observed_at": TODAY_STR,

    "identity_confidence": "LOW",
    "identity_evidence": [{
        "claim": "Reddit username T13961876 visible but no real name",
        "source": "Search results",
        "confidence": "LOW",
    }],

    "company_status": "UNVERIFIED",
    "company_evidence": [],

    "currentness_status": "CURRENT",
    "age_days": 0,
    "currentness_evidence": [{
        "claim": "Post observed same day",
        "source": "Search results",
        "confidence": "HIGH",
    }],

    "outsourcing_intent": "EXPLICIT",
    "outsourcing_confidence": "HIGH",
    "outsourcing_evidence": [{
        "claim": "Post explicitly requests help with app design and development",
        "source": "Post title and content",
        "confidence": "HIGH",
    }],

    "service_match": "Mobile App Development",
    "service_match_confidence": "MEDIUM",  # Unknown what type of app
    "service_match_evidence": [{
        "claim": "Request is for app design and development - could match mobile app services",
        "source": "Post content",
        "confidence": "MEDIUM",
    }],

    "email": "UNKNOWN",
    "email_status": "UNKNOWN",
    "email_evidence": [],

    "linkedin_url": "UNKNOWN",
    "linkedin_status": "UNKNOWN",
    "linkedin_evidence": [],

    "platform_contact": "Reddit DM (presumed)",
    "platform_contact_status": "UNKNOWN",

    "contactability": "LOW",
    "contactability_discovery_priority": "MEDIUM",
    "contactability_evidence": [{
        "claim": "Reddit post exists but contact details not publicly visible",
        "source": "Search results",
        "confidence": "LOW",
    }],

    "contact_owner_match": "UNKNOWN",

    "evidence_reproducibility": False,

    "competitor": False,
    "safety_clear": True,

    "opportunity_verdict": "NEEDS_RESEARCH",
    "final_salesability": "NEEDS_RESEARCH",

    "cto_15_minute_test": "NO",
    "cto_decision_reason": "Anonymous poster. Unknown app type. No contact details. Cannot verify business or project.",

    "rejection_reasons": [
        "Failed gate: primary_contact_status (UNKNOWN)",
        "Failed gate: contact_owner_match (UNKNOWN)",
        "Failed gate: evidence_reproducibility (cannot verify)",
    ],
})

# Candidate 5: AI Business - Can't Code (r/cofounderhunt)
candidates.append({
    "opportunity_id": "V8-007",
    "person_name": "UNKNOWN (Reddit poster)",
    "person_role": "Founder",
    "company_name": "AI Business (profitable, unnamed)",
    "company_url": "UNKNOWN",
    "product_url": "UNKNOWN",

    "requirement": "Built a profitable AI business. Can't code. Need someone who can.",
    "requirement_verified": False,
    "requirement_evidence": [{
        "claim": "Reddit post from founder with profitable AI business needing technical help",
        "source": "Reddit r/cofounderhunt",
        "source_url": "https://www.reddit.com/r/cofounderhunt/comments/1u9h1bj/",
        "confidence": "UNVERIFIED",
        "observed_at": TODAY_STR,
    }],

    "source_name": "Reddit r/cofounderhunt",
    "source_url": "https://www.reddit.com/r/cofounderhunt/comments/1u9h1bj/",
    "source_status": "ACCESS_BLOCKED",
    "source_post_id": "1u9h1bj",
    "published_at": "2026-08-02",  # ~6 days ago
    "observed_at": TODAY_STR,

    "identity_confidence": "LOW",
    "identity_evidence": [{
        "claim": "Reddit post claims profitable AI business but no verification",
        "source": "Search results",
        "confidence": "LOW",
    }],

    "company_status": "UNVERIFIED",
    "company_evidence": [],

    "currentness_status": "CURRENT",
    "age_days": 6,
    "currentness_evidence": [{
        "claim": "Post observed ~6 days old",
        "source": "Search results",
        "confidence": "APPROXIMATE",
    }],

    "outsourcing_intent": "COFOUNDER_SEARCH",  # Looking for technical co-founder, NOT agency
    "outsourcing_confidence": "LOW",
    "outsourcing_evidence": [{
        "claim": "Posted in r/cofounderhunt - seeking equity-based partnership, not agency services",
        "source": "Subreddit context",
        "confidence": "HIGH",
    }],

    "service_match": "AI Development",
    "service_match_confidence": "LOW",  # Looking for co-founder, not agency
    "service_match_evidence": [{
        "claim": "AI business could match AI development services, but intent is co-founder search",
        "source": "Post context",
        "confidence": "LOW",
    }],

    "email": "UNKNOWN",
    "email_status": "UNKNOWN",
    "email_evidence": [],

    "linkedin_url": "UNKNOWN",
    "linkedin_status": "UNKNOWN",
    "linkedin_evidence": [],

    "platform_contact": "Reddit DM (presumed)",
    "platform_contact_status": "UNKNOWN",

    "contactability": "LOW",
    "contactability_discovery_priority": "LOW",
    "contactability_evidence": [{
        "claim": "Co-founder search, not agency engagement",
        "source": "Subreddit context",
        "confidence": "HIGH",
    }],

    "contact_owner_match": "UNKNOWN",

    "evidence_reproducibility": False,

    "competitor": False,
    "safety_clear": True,

    "opportunity_verdict": "REJECT",
    "final_salesability": "REJECT",

    "cto_15_minute_test": "NO",
    "cto_decision_reason": "Co-founder search, NOT outsourcing. CTO rule: cofounder/equity requests are REJECT.",

    "rejection_reasons": [
        "REJECT: Co-founder search (not outsourcing)",
        "Failed gate: outsourcing_intent (COFOUNDER_SEARCH, not EXPLICIT agency request)",
    ],
})

# ============================================================
# GENERATE OUTPUTS
# ============================================================

# Filter candidates by status
sales_ready = [c for c in candidates if c["final_salesability"] == "SALES_READY"]
needs_research = [c for c in candidates if c["final_salesability"] == "NEEDS_RESEARCH"]
rejected = [c for c in candidates if c["final_salesability"] == "REJECT"]

print("=" * 70)
print("BEACON V8.3 — CONTACTABLE BUYING-EVENT DISCOVERY EXPANSION")
print("=" * 70)

print(f"\n[SEARCH STRATEGY]")
print(f"  Tiers searched: Tier 1 (founder requests), Tier 2 (communities), Tier 3 (discovery)")
print(f"  Search queries: {len(SEARCH_QUERIES)}")
print(f"  Sources attempted: Reddit, Indie Hackers, Product Hunt, Wellfound, Google")

print(f"\n[SEARCH RESULTS]")
print(f"  Total candidates identified: {len(candidates)}")
print(f"  SALES_READY: {len(sales_ready)}")
print(f"  NEEDS_RESEARCH: {len(needs_research)}")
print(f"  REJECTED: {len(rejected)}")

print(f"\n[CRITICAL FINDING]")
print(f"  Public search sources are SATURATED with service providers")
print(f"  Most 'hiring' posts are for full-time employment, not outsourcing")
print(f"  Most 'looking for developer' posts are from job seekers, not buyers")
print(f"  Cofounder searches are equity-based, not outsourcing")
print(f"  Reddit blocks direct access to verify post details")
print(f"  No public RFPs with contact information found")
print(f"  No founder blog posts requesting development help found")

print(f"\n[CONTACT VERIFICATION]")
print(f"  Email Verified: 0")
print(f"  LinkedIn Verified: 0")
print(f"  Platform Contact Verified: 0")
print(f"  All contact details: UNKNOWN (Reddit blocks access)")

print(f"\n[CONTACTABILITY]")
print(f"  HIGH: 0")
print(f"  MEDIUM: 0")
print(f"  LOW: {len([c for c in candidates if c['contactability'] == 'LOW'])}")
print(f"  NONE: 0")

print(f"\n[CTO 15-MINUTE TEST]")
yes_count = len([c for c in candidates if c["cto_15_minute_test"] == "YES"])
no_count = len([c for c in candidates if c["cto_15_minute_test"] == "NO"])
print(f"  YES: {yes_count}")
print(f"  NO: {no_count}")

print(f"\n[PRODUCTION STATUS]")
print(f"  OUTREACH DISABLED")
print(f"  AUTOMATION DISABLED")
print(f"  APPROVAL REQUIRED")

# ============================================================
# SAVE OUTPUTS
# ============================================================

# 1. Candidates JSON
with open(OUTPUT_DIR / "v8_3_candidates.json", "w", encoding="utf-8") as f:
    json.dump({
        "audit_name": "V8.3 Contactable Buying-Event Discovery",
        "audit_date": TODAY_STR,
        "total_candidates": len(candidates),
        "sales_ready": len(sales_ready),
        "needs_research": len(needs_research),
        "rejected": len(rejected),
        "candidates": candidates,
    }, f, indent=2, default=str)

# 2. Report
report_lines = []
report_lines.append("=" * 70)
report_lines.append("BEACON V8.3 — CONTACTABLE BUYING-EVENT DISCOVERY REPORT")
report_lines.append("=" * 70)
report_lines.append(f"\nAudit Date: {TODAY_STR}")
report_lines.append(f"\n{'='*70}")
report_lines.append("SEARCH STRATEGY")
report_lines.append(f"{'='*70}")
report_lines.append(f"  Tiers searched: Tier 1 (founder requests), Tier 2 (communities), Tier 3 (discovery)")
report_lines.append(f"  Search queries executed: {len(SEARCH_QUERIES)}")
report_lines.append(f"  Sources attempted: Reddit, Indie Hackers, Product Hunt, Wellfound, Google")
report_lines.append(f"\n{'='*70}")
report_lines.append("DISCOVERY RESULTS")
report_lines.append(f"{'='*70}")
report_lines.append(f"  Total candidates identified: {len(candidates)}")
report_lines.append(f"  SALES_READY: {len(sales_ready)}")
report_lines.append(f"  NEEDS_RESEARCH: {len(needs_research)}")
report_lines.append(f"  REJECTED: {len(rejected)}")
report_lines.append(f"\n{'='*70}")
report_lines.append("SOURCE QUALITY ANALYSIS")
report_lines.append(f"{'='*70}")
report_lines.append(f"  Reddit r/forhire: Mostly job seekers and agencies, NOT buying events")
report_lines.append(f"  Reddit r/startups: Mostly cofounder searches and advice requests")
report_lines.append(f"  Reddit r/SaaS: Mostly SaaS discussions, few hiring posts")
report_lines.append(f"  Reddit r/Entrepreneur: Mostly business advice, few development requests")
report_lines.append(f"  Reddit r/AppDevelopers: Some hiring posts, but anonymous")
report_lines.append(f"  Reddit r/jobsdubai: One relevant AI automation request")
report_lines.append(f"  Reddit r/developers_hire: Some hiring posts, but vague requirements")
report_lines.append(f"  Reddit r/cofounderhunt: Cofounder searches, NOT outsourcing")
report_lines.append(f"  Indie Hackers: Mostly job seekers and agency promotions")
report_lines.append(f"  Product Hunt: Hiring threads, not buying events")
report_lines.append(f"  Wellfound: Job board for startup hiring, not outsourcing")
report_lines.append(f"  Google: Saturated with agency listings and articles")
report_lines.append(f"\n{'='*70}")
report_lines.append("CRITICAL DISCOVERY BOTTLENECK")
report_lines.append(f"{'='*70}")
report_lines.append(f"  1. Public sources are SATURATED with service providers selling services")
report_lines.append(f"  2. Most 'hiring' posts are for full-time employment, not outsourcing")
report_lines.append(f"  3. Most 'looking for developer' posts are from job seekers, not buyers")
report_lines.append(f"  4. Cofounder searches are equity-based, not outsourcing")
report_lines.append(f"  5. Reddit blocks direct access to verify post details")
report_lines.append(f"  6. No public RFPs with contact information found")
report_lines.append(f"  7. No founder blog posts requesting development help found")
report_lines.append(f"  8. No public procurement opportunities matching services found")
report_lines.append(f"\n{'='*70}")
report_lines.append("CANDIDATES")
report_lines.append(f"{'='*70}")

for c in candidates:
    report_lines.append(f"\n--- {c['opportunity_id']} ---")
    report_lines.append(f"  Person: {c['person_name']}")
    report_lines.append(f"  Role: {c['person_role']}")
    report_lines.append(f"  Company: {c['company_name']}")
    report_lines.append(f"  Requirement: {c['requirement']}")
    report_lines.append(f"  Source: {c['source_name']}")
    report_lines.append(f"  Source URL: {c['source_url']}")
    report_lines.append(f"  Published: {c['published_at']}")
    report_lines.append(f"  Age: {c['age_days']} days")
    report_lines.append(f"  Outsourcing Intent: {c['outsourcing_intent']}")
    report_lines.append(f"  Service Match: {c['service_match']} ({c['service_match_confidence']})")
    report_lines.append(f"  Contactability: {c['contactability']}")
    report_lines.append(f"  Discovery Priority: {c['contactability_discovery_priority']}")
    report_lines.append(f"  Verdict: {c['final_salesability']}")
    report_lines.append(f"  CTO 15-Min Test: {c['cto_15_minute_test']}")
    report_lines.append(f"  Reason: {c['cto_decision_reason']}")

report_lines.append(f"\n{'='*70}")
report_lines.append("FINAL PRINCIPLE")
report_lines.append(f"{'='*70}")
report_lines.append(f"V8.3 found 0 SALES_READY opportunities.")
report_lines.append(f"This is an ACCEPTABLE result.")
report_lines.append(f"")
report_lines.append(f"The problem is NOT verification.")
report_lines.append(f"The problem is DISCOVERY SOURCE QUALITY.")
report_lines.append(f"")
report_lines.append(f"Public search sources are saturated with service providers.")
report_lines.append(f"Finding contactable buying events requires access to")
report_lines.append(f"channels where IDENTIFIABLE BUYERS post EXPLICIT REQUESTS")
report_lines.append(f"with VERIFIED CONTACT INFORMATION.")
report_lines.append(f"")
report_lines.append(f"DO NOT weaken V8.2 gates to increase counts.")
report_lines.append(f"DO NOT fabricate opportunities to reach a quota.")
report_lines.append(f"")
report_lines.append(f"0 SALES_READY is acceptable.")
report_lines.append(f"Only evidence determines the number.")

with open(OUTPUT_DIR / "v8_3_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

# 3. Contactability Report
contactability_report = {
    "audit_name": "V8.3 Contactability Report",
    "audit_date": TODAY_STR,
    "total_candidates": len(candidates),
    "contactability_distribution": {
        "HIGH": len([c for c in candidates if c["contactability"] == "HIGH"]),
        "MEDIUM": len([c for c in candidates if c["contactability"] == "MEDIUM"]),
        "LOW": len([c for c in candidates if c["contactability"] == "LOW"]),
        "NONE": len([c for c in candidates if c["contactability"] == "NONE"]),
    },
    "discovery_priority_distribution": {
        "VERY_HIGH": len([c for c in candidates if c["contactability_discovery_priority"] == "VERY_HIGH"]),
        "HIGH": len([c for c in candidates if c["contactability_discovery_priority"] == "HIGH"]),
        "MEDIUM": len([c for c in candidates if c["contactability_discovery_priority"] == "MEDIUM"]),
        "LOW": len([c for c in candidates if c["contactability_discovery_priority"] == "LOW"]),
    },
    "contact_source_performance": {
        "Reddit DM": len([c for c in candidates if "Reddit" in c.get("platform_contact", "")]),
        "Email": 0,
        "LinkedIn": 0,
        "Company Website": 0,
    },
    "bottleneck_analysis": [
        "Reddit blocks direct access to post content and contact details",
        "Most posting users are anonymous (no real name, no profile)",
        "Contact details not visible in search results",
        "Platform contact routes (DM) require Reddit account access",
        "No email addresses found in public search results",
        "No LinkedIn profiles found linked to buying events",
    ],
}

with open(OUTPUT_DIR / "v8_3_contactability_report.json", "w", encoding="utf-8") as f:
    json.dump(contactability_report, f, indent=2, default=str)

# 4. Source Quality Report
source_quality = {
    "audit_name": "V8.3 Source Quality Report",
    "audit_date": TODAY_STR,
    "sources_analyzed": [
        {
            "source": "Reddit r/forhire",
            "tier": "TIER_2",
            "buying_events_found": 0,
            "quality": "LOW",
            "reason": "Mostly job seekers posting [For Hire], not buyers posting [Hiring]",
        },
        {
            "source": "Reddit r/startups",
            "tier": "TIER_2",
            "buying_events_found": 0,
            "quality": "LOW",
            "reason": "Mostly cofounder searches and business advice requests",
        },
        {
            "source": "Reddit r/SaaS",
            "tier": "TIER_2",
            "buying_events_found": 0,
            "quality": "LOW",
            "reason": "Mostly SaaS discussions, few explicit hiring posts",
        },
        {
            "source": "Reddit r/Entrepreneur",
            "tier": "TIER_2",
            "buying_events_found": 0,
            "quality": "LOW",
            "reason": "Mostly business advice, few development requests",
        },
        {
            "source": "Reddit r/AppDevelopers",
            "tier": "TIER_2",
            "buying_events_found": 1,
            "quality": "MEDIUM",
            "reason": "Some hiring posts, but anonymous posters, no contact details",
        },
        {
            "source": "Reddit r/jobsdubai",
            "tier": "TIER_2",
            "buying_events_found": 1,
            "quality": "MEDIUM",
            "reason": "AI automation request from business owner, but contact details unknown",
        },
        {
            "source": "Reddit r/developers_hire",
            "tier": "TIER_2",
            "buying_events_found": 1,
            "quality": "LOW",
            "reason": "Hiring posts exist but requirements are vague, no contact details",
        },
        {
            "source": "Reddit r/cofounderhunt",
            "tier": "TIER_2",
            "buying_events_found": 1,
            "quality": "REJECT",
            "reason": "Cofounder searches - NOT outsourcing. CTO rule: REJECT",
        },
        {
            "source": "Reddit r/smallbusiness",
            "tier": "TIER_2",
            "buying_events_found": 1,
            "quality": "LOW",
            "reason": "Advice-seeking post, not explicit agency request",
        },
        {
            "source": "Indie Hackers",
            "tier": "TIER_2",
            "buying_events_found": 0,
            "quality": "LOW",
            "reason": "Mostly job seekers and agency promotions",
        },
        {
            "source": "Product Hunt",
            "tier": "TIER_2",
            "buying_events_found": 0,
            "quality": "LOW",
            "reason": "Hiring threads, not buying events",
        },
        {
            "source": "Wellfound",
            "tier": "TIER_3",
            "buying_events_found": 0,
            "quality": "LOW",
            "reason": "Job board for startup hiring, not outsourcing",
        },
        {
            "source": "Google Search",
            "tier": "TIER_3",
            "buying_events_found": 0,
            "quality": "LOW",
            "reason": "Saturated with agency listings and articles about development",
        },
    ],
    "source_performance_summary": {
        "total_sources_analyzed": 13,
        "sources_with_buying_events": 5,
        "sources_without_buying_events": 8,
        "best_source": "Reddit r/jobsdubai (1 AI automation request)",
        "worst_source": "Google Search (0 buying events, only agency listings)",
    },
    "recommendation": "Public search sources are insufficient for finding contactable buying events. Need access to channels where identifiable buyers post explicit requests with verified contact information.",
}

with open(OUTPUT_DIR / "v8_3_source_quality.json", "w", encoding="utf-8") as f:
    json.dump(source_quality, f, indent=2, default=str)

# 5. Rejected Report
rejected_report = {
    "audit_name": "V8.3 Rejected Opportunities",
    "audit_date": TODAY_STR,
    "total_rejected": len(rejected),
    "rejected": rejected,
}

with open(OUTPUT_DIR / "v8_3_rejected_report.txt", "w", encoding="utf-8") as f:
    f.write(json.dumps(rejected_report, indent=2, default=str))

print(f"\n[DONE] V8.3 output saved to: {OUTPUT_DIR}/")
print(f"  - v8_3_candidates.json")
print(f"  - v8_3_report.txt")
print(f"  - v8_3_contactability_report.json")
print(f"  - v8_3_source_quality.json")
print(f"  - v8_3_rejected_report.txt")

print(f"\n{'='*70}")
print(f"FINAL CTO REPORT")
print(f"{'='*70}")
print(f"  TOTAL_DISCOVERED: {len(candidates)}")
print(f"  SALES_READY: {len(sales_ready)}")
print(f"  NEEDS_RESEARCH: {len(needs_research)}")
print(f"  REJECTED: {len(rejected)}")
print(f"")
print(f"  CONTACTABILITY_HIGH: 0")
print(f"  CONTACTABILITY_MEDIUM: 0")
print(f"  CONTACTABILITY_LOW: {len([c for c in candidates if c['contactability'] == 'LOW'])}")
print(f"")
print(f"  VERDICT: 0 SALES_READY opportunities found.")
print(f"  This is an ACCEPTABLE result.")
print(f"  The problem is DISCOVERY SOURCE QUALITY.")
print(f"  DO NOT weaken V8.2 gates.")
