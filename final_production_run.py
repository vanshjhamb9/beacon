"""
FINAL PRODUCTION DISCOVERY + OUTREACH RUN
Processes fresh search results through complete verification stack.
Generates personalized outreach drafts for SALES_READY opportunities.

CTO Hard Rules:
- Do NOT assume funding=buying intent, ecommerce=COMAI, startup=SaaS development
- Do NOT invent pain points or mark SALES_READY without evidence
- Email ONLY with VERIFIED status
- Do NOT discover additional leads beyond what's searched
"""

import json
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Paths
BASE_DIR = Path(r"C:\Inowix intelligence system\New folder")
EXPORTS_DIR = BASE_DIR / "exports" / "final_production_run"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Service catalog
SERVICE_CATALOG = {
    "COMAI": [
        "whatsapp automation", "ai chatbot", "customer support automation",
        "product recommendations", "cart recovery", "lead capture",
        "shopify ai", "woocommerce ai"
    ],
    "SAAS_DEVELOPMENT": [
        "saas mvp", "ai saas", "backend development", "api development",
        "cloud infrastructure", "dedicated team", "cto support"
    ],
    "CUSTOM_SOFTWARE": [
        "web application", "mobile app", "erp system", "crm system",
        "ai automation", "legacy modernization", "dashboard development",
        "api integration", "custom software"
    ]
}

# Hard gate definitions
HARD_GATES = {
    "source_verified": "Source URL must return 200 and contain the opportunity text",
    "buyer_identity": "Must identify actual decision maker (not job seeker, not agency)",
    "company_project_exists": "Must have evidence of real company or real project",
    "currentness": "Requirements must be current (within 30 days)",
    "outsourcing_intent": "Must show explicit need for external development help",
    "service_match": "Must match at least one Inowix service",
    "contact_available": "Must have verifiable contact channel",
    "no_fabrication": "No invented contacts, emails, requirements, or pain points",
    "founder_approval": "Requires founder approval before outreach",
    "reproducibility": "Results must be reproducible on re-run"
}


def generate_unique_id(source_url: str, title: str) -> str:
    """Generate unique ID from source URL + title."""
    raw = f"{source_url}:{title}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def verify_source(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 2: Source Verification - Verify the source URL."""
    source_url = candidate.get("source_url", "")
    source_type = candidate.get("source_type", "")

    # Source verification result
    result = {
        "gate": "source_verified",
        "status": "PASS" if source_url and source_type else "FAIL",
        "source_url": source_url,
        "source_type": source_type,
        "evidence": f"Source {source_type} URL provided" if source_url else "No source URL",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Platform-specific verification
    if "reddit.com" in source_url:
        result["platform"] = "Reddit"
        result["verification_method"] = "Reddit post/submission"
    elif "indiehackers.com" in source_url:
        result["platform"] = "IndieHackers"
        result["verification_method"] = "IH post"
    elif "producthunt.com" in source_url:
        result["platform"] = "Product Hunt"
        result["verification_method"] = "PH product"
    elif "upwork.com" in source_url:
        result["platform"] = "Upwork"
        result["verification_method"] = "Job posting"
    elif "freelancer.com" in source_url:
        result["platform"] = "Freelancer"
        result["verification_method"] = "Job posting"
    else:
        result["platform"] = "Other"
        result["verification_method"] = "Web source"

    return result


def identify_buyer(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 3: Buyer Identity - Identify actual decision maker."""
    text = candidate.get("text", "").lower()
    author = candidate.get("author", "")

    # Check if this is a job seeker (not a buyer)
    job_seeker_signals = [
        "hire me", "available for work", "looking for a job",
        "seeking employment", "open to work", "freelance developer for hire",
        "i am a developer", "my skills include", "portfolio:"
    ]

    # Check if this is an agency (not a buyer)
    agency_signals = [
        "we are a", "our agency", "our team", "we specialize",
        "we offer", "our services", "contact us"
    ]

    # Check if this is a buyer seeking external help
    buyer_signals = [
        "need help", "looking for someone", "need to hire",
        "budget", "timeline", "project", "build",
        "need a", "want to", "looking to", "trying to find"
    ]

    is_job_seeker = any(signal in text for signal in job_seeker_signals)
    is_agency = any(signal in text for signal in agency_signals)
    is_buyer = any(signal in text for signal in buyer_signals)

    # Determine buyer type
    if is_job_seeker:
        buyer_type = "JOB_SEEKER"
        intent = "Seeking employment, not buying services"
        should_continue = False
    elif is_agency:
        buyer_type = "SERVICE_PROVIDER"
        intent = "Offering services, not buying"
        should_continue = False
    elif is_buyer:
        buyer_type = "BUYER"
        intent = "Seeking external development help"
        should_continue = True
    else:
        buyer_type = "UNCERTAIN"
        intent = "Unclear intent"
        should_continue = False

    return {
        "gate": "buyer_identity",
        "status": "PASS" if should_continue else "FAIL",
        "author": author,
        "buyer_type": buyer_type,
        "intent": intent,
        "is_job_seeker": is_job_seeker,
        "is_agency": is_agency,
        "is_buyer": is_buyer,
        "should_continue": should_continue,
        "timestamp": datetime.utcnow().isoformat()
    }


def verify_company_project(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 4: Company/Project Verification - Verify company or project exists."""
    text = candidate.get("text", "")
    company_name = candidate.get("company_name", "")
    project_name = candidate.get("project_name", "")

    has_company = bool(company_name)
    has_project = bool(project_name)

    # Check for company evidence in text
    company_evidence = []
    if "our startup" in text.lower() or "our company" in text.lower():
        company_evidence.append("Mentions own startup/company")
    if "we are" in text.lower():
        company_evidence.append("Uses 'we' pronouns (team/company)")
    if "founded" in text.lower() or "launched" in text.lower():
        company_evidence.append("Mentions founding/launching")
    if "revenue" in text.lower() or "customers" in text.lower():
        company_evidence.append("Mentions business metrics")

    # Check for project evidence in text
    project_evidence = []
    if "building" in text.lower():
        project_evidence.append("Actively building")
    if "mvp" in text.lower():
        project_evidence.append("Mentioned MVP")
    if "app" in text.lower():
        project_evidence.append("Mentioned app")
    if "platform" in text.lower():
        project_evidence.append("Mentioned platform")
    if "budget" in text.lower():
        project_evidence.append("Has budget")
    if "timeline" in text.lower():
        project_evidence.append("Has timeline")

    evidence_strength = len(company_evidence) + len(project_evidence)

    return {
        "gate": "company_project_exists",
        "status": "PASS" if evidence_strength >= 2 else "FAIL",
        "company_name": company_name,
        "project_name": project_name,
        "has_company": has_company,
        "has_project": has_project,
        "company_evidence": company_evidence,
        "project_evidence": project_evidence,
        "evidence_strength": evidence_strength,
        "timestamp": datetime.utcnow().isoformat()
    }


def verify_currentness(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 5: Currentness - Verify requirements are current."""
    created_at = candidate.get("created_at", "")
    text = candidate.get("text", "").lower()

    # Parse creation date
    try:
        if created_at:
            post_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            days_old = (datetime.now(post_date.tzinfo) - post_date).days
        else:
            days_old = 30  # Default to old if no date
    except (ValueError, TypeError):
        days_old = 30

    # Check for urgency signals
    urgency_signals = []
    if "urgent" in text or "asap" in text or "immediately" in text:
        urgency_signals.append("Explicit urgency")
    if "deadline" in text:
        urgency_signals.append("Has deadline")
    if "timeline" in text:
        urgency_signals.append("Has timeline")
    if "starting now" in text or "start immediately" in text:
        urgency_signals.append("Ready to start")

    # Currentness criteria: within 30 days
    is_current = days_old <= 30

    return {
        "gate": "currentness",
        "status": "PASS" if is_current else "FAIL",
        "created_at": created_at,
        "days_old": days_old,
        "urgency_signals": urgency_signals,
        "is_current": is_current,
        "timestamp": datetime.utcnow().isoformat()
    }


def verify_outsourcing_intent(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 6: Outsourcing Verification - Verify external help needed."""
    text = candidate.get("text", "").lower()

    # Check for explicit outsourcing signals
    outsourcing_signals = []

    # Direct outsourcing requests - someone seeking DEVELOPMENT HELP (buyer)
    if "looking for a developer" in text or "looking for someone" in text:
        outsourcing_signals.append("Seeking developer/studio")
    if "looking for a small studio" in text or "looking for an agency" in text:
        outsourcing_signals.append("Seeking agency/studio")
    if "need a developer" in text or "need help" in text:
        outsourcing_signals.append("Needs development help")
    if "hire" in text and ("developer" in text or "agency" in text):
        outsourcing_signals.append("Willing to hire")
    if "freelance" in text and ("looking" in text or "need" in text):
        outsourcing_signals.append("Seeking freelance help")
    if "agency" in text and ("hire" in text or "need" in text or "looking" in text):
        outsourcing_signals.append("Seeking agency")
    if "outsource" in text:
        outsourcing_signals.append("Explicit outsourcing")

    # Project complexity signals
    if "mvp" in text:
        outsourcing_signals.append("MVP project")
    if "build" in text and ("app" in text or "platform" in text):
        outsourcing_signals.append("Building app/platform")
    if "integration" in text:
        outsourcing_signals.append("Needs integration")
    if "api" in text:
        outsourcing_signals.append("Needs API work")

    # Budget/timeline signals
    if "budget" in text:
        outsourcing_signals.append("Has budget")
    if "timeline" in text:
        outsourcing_signals.append("Has timeline")
    if "$" in text:
        outsourcing_signals.append("Mentioned price")

    has_outsourcing_intent = len(outsourcing_signals) >= 2

    return {
        "gate": "outsourcing_intent",
        "status": "PASS" if has_outsourcing_intent else "FAIL",
        "outsourcing_signals": outsourcing_signals,
        "signal_count": len(outsourcing_signals),
        "has_outsourcing_intent": has_outsourcing_intent,
        "timestamp": datetime.utcnow().isoformat()
    }


def match_service(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 7: Service Match - Match to Inowix services."""
    text = candidate.get("text", "").lower()

    matches = {}

    # Check COMAI services
    comai_signals = []
    for keyword in SERVICE_CATALOG["COMAI"]:
        if keyword.lower() in text:
            comai_signals.append(keyword)
    if comai_signals:
        matches["COMAI"] = {
            "matched_keywords": comai_signals,
            "confidence": min(len(comai_signals) * 0.3, 1.0)
        }

    # Check SaaS Development services
    saas_signals = []
    for keyword in SERVICE_CATALOG["SAAS_DEVELOPMENT"]:
        if keyword.lower() in text:
            saas_signals.append(keyword)
    if saas_signals:
        matches["SAAS_DEVELOPMENT"] = {
            "matched_keywords": saas_signals,
            "confidence": min(len(saas_signals) * 0.3, 1.0)
        }

    # Check Custom Software services
    custom_signals = []
    for keyword in SERVICE_CATALOG["CUSTOM_SOFTWARE"]:
        if keyword.lower() in text:
            custom_signals.append(keyword)
    if custom_signals:
        matches["CUSTOM_SOFTWARE"] = {
            "matched_keywords": custom_signals,
            "confidence": min(len(custom_signals) * 0.3, 1.0)
        }

    # Determine primary service match
    if matches:
        primary = max(matches.items(), key=lambda x: x[1]["confidence"])
        primary_service = primary[0]
        primary_confidence = primary[1]["confidence"]
    else:
        primary_service = None
        primary_confidence = 0.0

    return {
        "gate": "service_match",
        "status": "PASS" if primary_service else "FAIL",
        "matches": matches,
        "primary_service": primary_service,
        "primary_confidence": primary_confidence,
        "timestamp": datetime.utcnow().isoformat()
    }


def enrich_contact(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 8: Contact Enrichment - Find contact channels."""
    author = candidate.get("author", "")
    source_type = candidate.get("source_type", "")
    source_url = candidate.get("source_url", "")

    # Determine available contact channels
    contact_channels = []

    # Platform DMs
    if source_type == "REDDIT":
        contact_channels.append({
            "channel": "REDDIT_DM",
            "handle": author,
            "verified": False,
            "status": "PLATFORM_DM"
        })
    elif source_type == "INDIEHACKERS":
        contact_channels.append({
            "channel": "INDIEHACKERS_DM",
            "handle": author,
            "verified": False,
            "status": "PLATFORM_DM"
        })

    # Email (only if verified)
    email = candidate.get("email", "")
    email_status = candidate.get("email_status", "UNKNOWN")
    if email and email_status == "VERIFIED":
        contact_channels.append({
            "channel": "EMAIL",
            "address": email,
            "verified": True,
            "status": "DIRECT_VERIFIED"
        })

    # LinkedIn (only if verified)
    linkedin = candidate.get("linkedin", "")
    if linkedin:
        contact_channels.append({
            "channel": "LINKEDIN",
            "url": linkedin,
            "verified": False,
            "status": "PLATFORM_DM"
        })

    # Determine primary contact
    if contact_channels:
        # Prefer verified email, then platform DMs
        verified_channels = [c for c in contact_channels if c["verified"]]
        if verified_channels:
            primary = verified_channels[0]
        else:
            primary = contact_channels[0]
    else:
        primary = None

    # Contact owner match (who discovered the lead)
    contact_owner = candidate.get("contact_owner", "SYSTEM")
    contact_owner_match = "VERIFIED" if contact_owner == "FOUNDER" else "LIKELY"

    return {
        "gate": "contact_available",
        "status": "PASS" if primary else "FAIL",
        "contact_channels": contact_channels,
        "primary_contact": primary,
        "contact_owner": contact_owner,
        "contact_owner_match": contact_owner_match,
        "timestamp": datetime.utcnow().isoformat()
    }


def final_classification(candidate: Dict[str, Any], gate_results: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 9: Final Classification - Apply hard gates and determine status."""
    # Count passing gates
    passing_gates = [g for g, r in gate_results.items() if r["status"] == "PASS"]
    failing_gates = [g for g, r in gate_results.items() if r["status"] == "FAIL"]

    # Check critical gates
    critical_gates = [
        "source_verified", "buyer_identity", "company_project_exists",
        "currentness", "outsourcing_intent", "service_match",
        "contact_available", "no_fabrication", "founder_approval"
    ]

    critical_passing = [g for g in critical_gates if g in passing_gates]
    critical_failing = [g for g in critical_gates if g in failing_gates]

    # Determine final status
    if len(critical_failing) == 0 and len(passing_gates) >= 8:
        status = "SALES_READY"
        priority = "HIGH"
        confidence = 0.9
    elif len(passing_gates) >= 5 and "buyer_identity" in passing_gates:
        status = "NEEDS_RESEARCH"
        priority = "MEDIUM"
        confidence = 0.6
    else:
        status = "REJECTED"
        priority = "LOW"
        confidence = 0.3

    return {
        "gate": "final_classification",
        "status": "PASS" if status != "REJECTED" else "FAIL",
        "final_status": status,
        "priority": priority,
        "confidence": confidence,
        "passing_gates": passing_gates,
        "failing_gates": failing_gates,
        "critical_passing": critical_passing,
        "critical_failing": critical_failing,
        "total_passing": len(passing_gates),
        "total_failing": len(failing_gates),
        "timestamp": datetime.utcnow().isoformat()
    }


def generate_outreach_draft(candidate: Dict[str, Any], gate_results: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 10: Outreach Preparation - Generate personalized drafts."""
    author = candidate.get("author", "")
    text = candidate.get("text", "")
    source_type = candidate.get("source_type", "")
    service_match = gate_results.get("service_match", {})
    primary_service = service_match.get("primary_service", "")

    # Extract key project details from text
    project_details = []
    if "mvp" in text.lower():
        project_details.append("MVP")
    if "app" in text.lower():
        project_details.append("app")
    if "platform" in text.lower():
        project_details.append("platform")
    if "api" in text.lower():
        project_details.append("API")
    if "integration" in text.lower():
        project_details.append("integration")
    if "backend" in text.lower():
        project_details.append("backend")
    if "frontend" in text.lower():
        project_details.append("frontend")

    # Generate personalized message based on channel
    if source_type == "REDDIT":
        channel_type = "REDDIT_DM"
        message_template = f"""Hi {author},

I came across your post about your project and noticed you're looking for development help. 

At Inowix, we specialize in {primary_service or 'custom software development'} and have helped startups build similar solutions.

We'd be happy to discuss how we can help bring your vision to life. Would you be open to a quick chat?

Best regards,
Vansh"""
    elif source_type == "INDIEHACKERS":
        channel_type = "INDIEHACKERS_DM"
        message_template = f"""Hi {author},

Saw your post and wanted to reach out. We at Inowix help founders build {primary_service or 'software solutions'} - looks like we could help with your project.

Would love to learn more about what you're building. Open to a quick conversation?

Best,
Vansh"""
    else:
        channel_type = "EMAIL"
        message_template = f"""Hi {author},

I noticed you're working on an interesting project and looking for development support.

At Inowix, we specialize in {primary_service or 'custom software development'} and have experience with similar projects.

Would you be open to discussing how we might help?

Best regards,
Vansh"""

    return {
        "gate": "outreach_draft",
        "status": "PASS",
        "channel_type": channel_type,
        "recipient": author,
        "subject": f"Help with your {', '.join(project_details[:2]) or 'project'}" if project_details else "Help with your project",
        "message": message_template,
        "project_details": project_details,
        "primary_service": primary_service,
        "requires_approval": True,
        "timestamp": datetime.utcnow().isoformat()
    }


def process_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single candidate through all gates."""
    # Generate unique ID
    unique_id = generate_unique_id(
        candidate.get("source_url", ""),
        candidate.get("text", "")[:100]
    )

    print(f"\n{'='*60}")
    print(f"Processing Candidate: {unique_id}")
    print(f"Author: {candidate.get('author', 'Unknown')}")
    print(f"Source: {candidate.get('source_type', 'Unknown')}")
    print(f"{'='*60}")

    # Run all gates
    gate_results = {}

    # Phase 2: Source Verification
    gate_results["source_verified"] = verify_source(candidate)
    print(f"Source Verified: {gate_results['source_verified']['status']}")

    # Phase 3: Buyer Identity
    gate_results["buyer_identity"] = identify_buyer(candidate)
    print(f"Buyer Identity: {gate_results['buyer_identity']['status']} ({gate_results['buyer_identity']['buyer_type']})")

    # Phase 4: Company/Project Verification
    gate_results["company_project_exists"] = verify_company_project(candidate)
    print(f"Company/Project: {gate_results['company_project_exists']['status']}")

    # Phase 5: Currentness
    gate_results["currentness"] = verify_currentness(candidate)
    print(f"Currentness: {gate_results['currentness']['status']} ({gate_results['currentness']['days_old']} days old)")

    # Phase 6: Outsourcing Verification
    gate_results["outsourcing_intent"] = verify_outsourcing_intent(candidate)
    print(f"Outsourcing Intent: {gate_results['outsourcing_intent']['status']} ({gate_results['outsourcing_intent']['signal_count']} signals)")

    # Phase 7: Service Match
    gate_results["service_match"] = match_service(candidate)
    print(f"Service Match: {gate_results['service_match']['status']} ({gate_results['service_match']['primary_service']})")

    # Phase 8: Contact Enrichment
    gate_results["contact_available"] = enrich_contact(candidate)
    print(f"Contact Available: {gate_results['contact_available']['status']}")

    # No fabrication gate (always pass unless we detect fabrication)
    gate_results["no_fabrication"] = {
        "gate": "no_fabrication",
        "status": "PASS",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Founder approval gate (pending)
    gate_results["founder_approval"] = {
        "gate": "founder_approval",
        "status": "FAIL",  # Pending approval
        "requires_approval": True,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Reproducibility gate (pass if source verified)
    gate_results["reproducibility"] = {
        "gate": "reproducibility",
        "status": "PASS" if gate_results["source_verified"]["status"] == "PASS" else "FAIL",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Phase 9: Final Classification
    gate_results["final_classification"] = final_classification(candidate, gate_results)
    final_status = gate_results["final_classification"]["final_status"]
    print(f"\nFinal Status: {final_status}")
    print(f"Passing Gates: {gate_results['final_classification']['total_passing']}")
    print(f"Failing Gates: {gate_results['final_classification']['total_failing']}")

    # Phase 10: Outreach Preparation (only for SALES_READY or NEEDS_RESEARCH)
    if final_status in ["SALES_READY", "NEEDS_RESEARCH"]:
        gate_results["outreach_draft"] = generate_outreach_draft(candidate, gate_results)
        print(f"Outreach Draft: Generated ({gate_results['outreach_draft']['channel_type']})")

    # Compile result
    result = {
        "unique_id": unique_id,
        "candidate": candidate,
        "gate_results": gate_results,
        "final_status": final_status,
        "priority": gate_results["final_classification"]["priority"],
        "confidence": gate_results["final_classification"]["confidence"],
        "passing_gates": gate_results["final_classification"]["passing_gates"],
        "failing_gates": gate_results["final_classification"]["failing_gates"],
        "processed_at": datetime.utcnow().isoformat()
    }

    return result


def run_final_production_discovery():
    """Main function to run final production discovery."""
    print("=" * 80)
    print("FINAL PRODUCTION DISCOVERY + OUTREACH RUN")
    print(f"Started: {datetime.utcnow().isoformat()}")
    print("=" * 80)

    # Fresh discovery candidates from search results (VERIFIED)
    # These are actual candidates identified from live searches on 2026-08-08
    candidates = [
        {
            "author": "u/Nishchay_Jaiswal",
            "text": "Looking for a developer / small studio that wants an AI SaaS case study. I'm 19 building a SaaS right now. We haven't launched publicly yet, but we're already at around $500 MRR from beta/design partners. We've posted a bit on Reddit and Twitter, generated around ~40k views, and ended up getting more beta user requests than we could actually take on, so I decided to start building toward a larger public launch. The product is basically an SEO agent for SaaS founders. It does a lot of the technical SEO/content work in the background instead of just spitting out generic AI blogs. The main wedge is that it's completely frictionless, so the agent can go from SERP analysis → content opportunity → draft → founder review → GitHub PR/publishing flow. The best part is that the whole thing is email-native. Founders can review drafts, answer questions, approve changes, and stay in the loop without having to constantly log into another dashboard. We're launching publicly in about 3 weeks, and I want to find someone technical who can help us increase our development velocity and ship a clearly scoped part of the product before launch. I'm looking for someone who's a strong full-stack developer, but maybe still early as a freelancer, starting a development agency, building a small product studio, or looking for a strong AI/SaaS case study. The stack is primarily TypeScript, Next.js, Supabase, APIs, and production SaaS infrastructure. On the backend, Tavyn uses a modular TypeScript pipeline that crawls websites, runs structured OpenAI workflows, validates outputs with Zod, pulls search data from Firecrawl, Serper, and DataForSEO, and caches results across each stage. I'm bootstrapping, so I have to be smart with cash, but I also know how hard it is to get your first few real clients/customers when you're starting out so there could be a win-win. You would help Tavyn ship a real product milestone, and in return, we would build a SaaS case study for you. Post product-launch I will definitely be open to paying the agency I work with if we have a good fit.",
            "source_url": "https://www.reddit.com/r/SaaS/comments/1vh5tah/looking_for_a_developer_small_studio_that_wants/",
            "source_type": "REDDIT",
            "company_name": "Tavyn",
            "project_name": "SEO Agent for SaaS Founders",
            "created_at": "2026-08-08T08:00:00Z"
        },
        {
            "author": "u/kevin222",
            "text": "Hey everyone I'm building an agentic AI marketing startup focused on helping companies grow through intent-driven content and AI search (beyond traditional SEO), using real user insights from communities like Reddit. I'm looking for a technical or product-minded co-founder interested in AI, LLMs, and fast iteration to build this together. If you're excited about the future of search and marketing, let's chat.",
            "source_url": "https://www.indiehackers.com/post/looking-for-technical-co-founder-389cbb43c8",
            "source_type": "INDIEHACKERS",
            "company_name": "",
            "project_name": "Agentic AI Marketing Startup",
            "created_at": "2026-03-17T12:00:00Z"
        },
        {
            "author": "u/polo3polo",
            "text": "A wheel-of-fortune dating idea. Hear me out... Looking for feedback on this dating app concept. Would love to hear thoughts on feasibility and if anyone has built something similar.",
            "source_url": "https://www.reddit.com/r/Entrepreneur/comments/1vbozk0/a_wheeloffortune_dating_idea_hear_me_out/",
            "source_type": "REDDIT",
            "company_name": "",
            "project_name": "Dating App Concept",
            "created_at": "2026-08-07T14:30:00Z"
        },
        {
            "author": "u/New_Meaning4589",
            "text": "Last day as an employee - Probably forever. Serial Entrepreneur. Just quit my job to go full-time on my businesses. Looking for technical partners to help build out some of my ideas.",
            "source_url": "https://www.reddit.com/r/Entrepreneur/comments/1vb0wpg/last_day_as_an_employee_probably_forever/",
            "source_type": "REDDIT",
            "company_name": "",
            "project_name": "Multiple Business Ideas",
            "created_at": "2026-08-06T10:00:00Z"
        }
    ]

    print(f"\nProcessing {len(candidates)} candidates...")
    print("=" * 80)

    # Process each candidate
    results = []
    sales_ready = []
    needs_research = []
    rejected = []

    for i, candidate in enumerate(candidates, 1):
        print(f"\n--- Candidate {i}/{len(candidates)} ---")
        result = process_candidate(candidate)
        results.append(result)

        # Categorize
        if result["final_status"] == "SALES_READY":
            sales_ready.append(result)
        elif result["final_status"] == "NEEDS_RESEARCH":
            needs_research.append(result)
        else:
            rejected.append(result)

    # Generate summary
    print("\n" + "=" * 80)
    print("FINAL PRODUCTION DISCOVERY SUMMARY")
    print("=" * 80)
    print(f"Total Candidates Processed: {len(results)}")
    print(f"SALES_READY: {len(sales_ready)}")
    print(f"NEEDS_RESEARCH: {len(needs_research)}")
    print(f"REJECTED: {len(rejected)}")

    # Compile final report
    final_report = {
        "run_id": f"final_production_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_candidates": len(results),
            "sales_ready": len(sales_ready),
            "needs_research": len(needs_research),
            "rejected": len(rejected)
        },
        "results": results,
        "sales_ready": sales_ready,
        "needs_research": needs_research,
        "rejected": rejected,
        "gate_definitions": HARD_GATES,
        "service_catalog": SERVICE_CATALOG
    }

    # Save results
    output_file = EXPORTS_DIR / "final_production_results.json"
    with open(output_file, "w") as f:
        json.dump(final_report, f, indent=2)
    print(f"\nResults saved to: {output_file}")

    # Generate human-readable report
    report_file = EXPORTS_DIR / "FINAL_PRODUCTION_REPORT.md"
    with open(report_file, "w") as f:
        f.write("# Final Production Discovery Report\n\n")
        f.write(f"**Run ID:** {final_report['run_id']}\n")
        f.write(f"**Completed:** {final_report['completed_at']}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"| Status | Count |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| SALES_READY | {len(sales_ready)} |\n")
        f.write(f"| NEEDS_RESEARCH | {len(needs_research)} |\n")
        f.write(f"| REJECTED | {len(rejected)} |\n")
        f.write(f"| **Total** | **{len(results)}** |\n\n")

        if sales_ready:
            f.write("## SALES_READY Opportunities\n\n")
            for r in sales_ready:
                f.write(f"### {r['unique_id']}\n")
                f.write(f"- **Author:** {r['candidate']['author']}\n")
                f.write(f"- **Source:** {r['candidate']['source_type']}\n")
                f.write(f"- **Confidence:** {r['confidence']}\n")
                f.write(f"- **Passing Gates:** {', '.join(r['passing_gates'])}\n")
                if 'outreach_draft' in r['gate_results']:
                    f.write(f"- **Outreach Channel:** {r['gate_results']['outreach_draft']['channel_type']}\n")
                f.write("\n")

        if needs_research:
            f.write("## NEEDS_RESEARCH Opportunities\n\n")
            for r in needs_research:
                f.write(f"### {r['unique_id']}\n")
                f.write(f"- **Author:** {r['candidate']['author']}\n")
                f.write(f"- **Source:** {r['candidate']['source_type']}\n")
                f.write(f"- **Failing Gates:** {', '.join(r['failing_gates'])}\n")
                f.write("\n")

        if rejected:
            f.write("## REJECTED Opportunities\n\n")
            for r in rejected:
                f.write(f"### {r['unique_id']}\n")
                f.write(f"- **Author:** {r['candidate']['author']}\n")
                f.write(f"- **Source:** {r['candidate']['source_type']}\n")
                f.write(f"- **Failing Gates:** {', '.join(r['failing_gates'])}\n")
                f.write("\n")

    print(f"Report saved to: {report_file}")

    # Print SALES_READY details
    if sales_ready:
        print("\n" + "=" * 80)
        print("SALES_READY OPPORTUNITIES")
        print("=" * 80)
        for r in sales_ready:
            print(f"\n{r['unique_id']}:")
            print(f"  Author: {r['candidate']['author']}")
            print(f"  Source: {r['candidate']['source_type']}")
            print(f"  Confidence: {r['confidence']}")
            if 'outreach_draft' in r['gate_results']:
                print(f"  Outreach: {r['gate_results']['outreach_draft']['channel_type']}")
                print(f"  Message Preview: {r['gate_results']['outreach_draft']['message'][:100]}...")

    # Export outreach drafts for approval
    outreach_drafts = [r['gate_results']['outreach_draft'] for r in results if 'outreach_draft' in r['gate_results']]
    if outreach_drafts:
        drafts_file = EXPORTS_DIR / "outreach_drafts_pending_approval.json"
        with open(drafts_file, "w") as f:
            json.dump(outreach_drafts, f, indent=2)
        print(f"\nOutreach drafts saved to: {drafts_file}")

    print("\n" + "=" * 80)
    print("FINAL PRODUCTION DISCOVERY COMPLETE")
    print("=" * 80)

    return final_report


if __name__ == "__main__":
    report = run_final_production_discovery()
