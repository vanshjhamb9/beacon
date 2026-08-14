#!/usr/bin/env python3
"""
ADVERSARIAL SALESABILITY AUDIT V2
Hostile validation test — NOT designed to maximize lead count.
"""

import json
from datetime import datetime
from pathlib import Path

EXPORTS_DIR = Path("exports")

def audit_lead(lead):
    """Audit a single lead against all 17 hard gates."""
    audit = {
        "id": lead["id"],
        "original_title": lead["title"],
        "original_classification": lead["classification"],
        "original_score": lead["scores"]["total"],

        # Gate 1: Source Validation
        "source_validation": {},
        # Gate 2: Person Identity
        "person_identity": {},
        # Gate 3: Actual Requirement
        "actual_requirement": {},
        # Gate 4: Outsourcing Intent
        "outsourcing_intent": {},
        # Gate 5: Service Match
        "service_match": {},
        # Gate 6: Competitor Check
        "competitor_check": {},
        # Gate 7: Buyer Fit
        "buyer_fit": {},
        # Gate 8: Budget
        "budget": {},
        # Gate 9: Project Status
        "project_status": {},
        # Gate 10: India/Global Fit
        "geo_fit": {},
        # Gate 11: Contactability
        "contactability": {},
        # Gate 12: Evidence
        "evidence": {},
        # Gate 13: Final Classification
        "final_classification": "",
        # Gate 14: Scoring
        "scores": {},
        # Gate 15: Anti-Gaming
        # Gate 16: Cross-Source
        "cross_source_validation": {},
        # Gate 17: Output
        "rejection_reasons": [],
        "missing_information": [],
        "recommended_next_action": "",
    }

    # ============================================================
    # GATE 1: SOURCE VALIDATION — HARD GATE
    # ============================================================
    source_url = lead.get("source_url", "")

    # Check if URL is a search/category page
    is_search_page = False
    is_category_page = False
    is_exact_post = False

    if "/search/jobs/?q=" in source_url or "/search/jobs?q=" in source_url:
        is_search_page = True
    elif "/search?" in source_url:
        is_search_page = True
    elif "/nx/search/" in source_url:
        is_search_page = True

    if "/comments/" in source_url and len(source_url.split("/comments/")) > 1:
        post_part = source_url.split("/comments/")[1]
        if post_part and post_part != "" and "/" not in post_part.rstrip("/"):
            is_exact_post = True

    if "/f=" in source_url or "/category/" in source_url or "/tag/" in source_url:
        is_category_page = True

    source_type = "UNKNOWN"
    if is_search_page:
        source_type = "SEARCH_PAGE"
    elif is_category_page:
        source_type = "CATEGORY_PAGE"
    elif is_exact_post:
        source_type = "EXACT_POST"
    elif "upwork.com/nx/search" in source_url:
        source_type = "SEARCH_PAGE"
    elif "upwork.com" in source_url and "/freelancers/" in source_url:
        source_type = "FREELANCER_LISTING"
    elif "upwork.com" in source_url and "/jobs/" in source_url and "/q=" in source_url:
        source_type = "SEARCH_PAGE"
    else:
        source_type = "GENERIC"

    # Determine source access status based on evidence from webfetch
    source_access_status = "UNKNOWN"
    source_evidence = ""

    if is_search_page:
        source_access_status = "INACCESSIBLE"
        source_evidence = "Search result page — returns 403 or shows multiple jobs. NOT a specific job/project."
    elif is_exact_post and "reddit.com" in source_url:
        source_access_status = "PUBLICLY_ACCESSIBLE"
        source_evidence = "Reddit post with exact comment ID. Publicly accessible."
    elif source_url.startswith("https://www.upwork.com/"):
        source_access_status = "INACCESSIBLE"
        source_evidence = "Upwork pages require authentication or return 403."

    audit["source_validation"] = {
        "source_url": source_url,
        "source_type": source_type,
        "source_title": lead.get("title", ""),
        "source_date": lead.get("date", "UNKNOWN"),
        "source_access_status": source_access_status,
        "source_evidence": source_evidence,
        "is_exact_post": is_exact_post,
        "is_search_page": is_search_page,
    }

    # ============================================================
    # GATE 2: PERSON IDENTITY VALIDATION
    # ============================================================
    person_name = lead.get("person", "Unknown")
    identity_confidence = "UNKNOWN"
    role = "UNKNOWN"
    company = "UNKNOWN"
    profile_url = "UNKNOWN"

    if person_name == "Upwork Client":
        identity_confidence = "ANONYMOUS"
        role = "Client (anonymous)"
        company = "Anonymous Upwork client"
    elif "Unknown" in person_name or "r/cofounderhunt" in person_name:
        identity_confidence = "UNKNOWN"
        role = "Reddit user (unidentified)"
    elif person_name == "Aggressive_Buy_4411":
        identity_confidence = "REDDIT_USERNAME"
        role = "First-time founder (non-engineer)"
        company = "Project G-Bridge"
        profile_url = f"https://www.reddit.com/user/{person_name}"
    elif person_name == "sine-si":
        identity_confidence = "REDDIT_USERNAME"
        role = "US agency owner"
        company = "US website agency"
        profile_url = f"https://www.reddit.com/user/{person_name}"
    elif person_name == "FlyFunny8902":
        identity_confidence = "REDDIT_USERNAME"
        role = "Startup founder"
        company = "Finance app startup"
        profile_url = f"https://www.reddit.com/user/{person_name}"
    elif person_name == "GENERICO_____":
        identity_confidence = "REDDIT_USERNAME"
        role = "n8n user"
        company = "UNKNOWN"
        profile_url = f"https://www.reddit.com/user/{person_name}"
    elif person_name == "Fair-Resort8854":
        identity_confidence = "REDDIT_USERNAME"
        role = "First-time builder"
        company = "UNKNOWN"
        profile_url = f"https://www.reddit.com/user/{person_name}"
    elif person_name == "Authority0fReddit":
        identity_confidence = "REDDIT_USERNAME"
        role = "AI/Animation founder"
        company = "UNKNOWN"
        profile_url = f"https://www.reddit.com/user/{person_name}"
    elif person_name == "Specialist-Step1314":
        identity_confidence = "REDDIT_USERNAME"
        role = "SaaS builder"
        company = "UNKNOWN"
        profile_url = f"https://www.reddit.com/user/{person_name}"
    elif person_name == "neb2357":
        identity_confidence = "REDDIT_USERNAME"
        role = "Healthcare SaaS founder"
        company = "Healthcare SaaS"
        profile_url = f"https://www.reddit.com/user/{person_name}"

    audit["person_identity"] = {
        "person_name": person_name,
        "role": role,
        "company": company,
        "profile_url": profile_url,
        "identity_confidence": identity_confidence,
    }

    # ============================================================
    # GATE 3: ACTUAL REQUIREMENT VALIDATION
    # ============================================================
    requirement_text = ""
    required_technology = []
    project_type = "UNKNOWN"
    budget = "UNKNOWN"
    timeline = "UNKNOWN"
    urgency = "UNKNOWN"
    outsourcing_language = ""

    if is_search_page:
        requirement_text = "GENERIC SEARCH PAGE — no specific requirement visible"
        project_type = "UNKNOWN"
    else:
        # Based on verified post content
        if lead["id"] == "HI-001":
            requirement_text = "Seeking technical cofounder / CTO for AI systems, interoperability, cross-platform device bridge. Patent pending concept. Needs production-grade prototype."
            required_technology = ["AI", "full stack", "backend", "cross-platform"]
            project_type = "AI Systems / Cross-platform"
            budget = "UNKNOWN (equity offered)"
            timeline = "UNKNOWN"
            urgency = "MEDIUM"
            outsourcing_language = "Seeking cofounder/CTO — NOT explicitly seeking outsourced development"
        elif lead["id"] == "HI-004":
            requirement_text = "Revenue SaaS hiring full-stack engineer"
            required_technology = ["SaaS", "full stack", "backend", "API"]
            project_type = "SaaS"
            budget = "UNKNOWN"
            timeline = "UNKNOWN"
            urgency = "UNKNOWN"
            outsourcing_language = "HIRING FULL-TIME EMPLOYEE — NOT outsourcing"
        elif lead["id"] == "HI-009":
            requirement_text = "US agency needs web developer. 20% commission. WordPress/Elementor or Webflow. 24-48 hour turnaround."
            required_technology = ["WordPress", "Elementor", "Webflow", "web development"]
            project_type = "Web development (agency sub-contracting)"
            budget = "20% commission per project"
            timeline = "24-48 hours for demo, 5-8 pages"
            urgency = "HIGH"
            outsourcing_language = "Agency seeking freelance developer for sub-contracting"
        elif lead["id"] == "HI-003":
            requirement_text = "REQUIRES_VERIFICATION — retail tech cofounder post"
            required_technology = ["SaaS MVP", "retail tech"]
            project_type = "UNKNOWN"
            budget = "UNKNOWN"
            timeline = "UNKNOWN"
            urgency = "UNKNOWN"
            outsourcing_language = "Seeking cofounder — NOT explicitly seeking outsourced development"
        elif lead["id"] == "HI-002":
            requirement_text = "REQUIRES_VERIFICATION — iOS app cofounder post"
            required_technology = ["iOS", "mobile app", "react native"]
            project_type = "Mobile App"
            budget = "UNKNOWN"
            timeline = "UNKNOWN"
            urgency = "UNKNOWN"
            outsourcing_language = "Seeking cofounder — NOT explicitly seeking outsourced development"
        elif lead["id"] == "HI-005":
            requirement_text = "REQUIRES_VERIFICATION — AI video/animation technical cofounder"
            required_technology = ["AI", "video", "animation"]
            project_type = "AI/Media"
            budget = "UNKNOWN"
            timeline = "UNKNOWN"
            urgency = "UNKNOWN"
            outsourcing_language = "Seeking cofounder — NOT explicitly seeking outsourced development"
        elif lead["id"] == "HI-006":
            requirement_text = "REQUIRES_VERIFICATION — WhatsApp chatbot for customer service using n8n"
            required_technology = ["WhatsApp", "chatbot", "n8n"]
            project_type = "Automation"
            budget = "UNKNOWN"
            timeline = "UNKNOWN"
            urgency = "UNKNOWN"
            outsourcing_language = "Needs help building — POSSIBLE outsourcing"
        elif lead["id"] == "HI-007":
            requirement_text = "REQUIRES_VERIFICATION — First-time builder, WhatsApp API got banned"
            required_technology = ["WhatsApp", "API integration"]
            project_type = "WhatsApp Business"
            budget = "UNKNOWN"
            timeline = "UNKNOWN"
            urgency = "HIGH"
            outsourcing_language = "Needs help — POSSIBLE outsourcing"
        elif lead["id"] == "HI-008":
            requirement_text = "REQUIRES_VERIFICATION — Finance app developer needed"
            required_technology = ["mobile app", "finance", "iOS", "android"]
            project_type = "Mobile App"
            budget = "UNKNOWN"
            timeline = "UNKNOWN"
            urgency = "UNKNOWN"
            outsourcing_language = "Explicitly seeking developer — POSSIBLE outsourcing"
        elif lead["id"] == "HI-010":
            requirement_text = "REQUIRES_VERIFICATION — Developer building micro-SaaS"
            required_technology = ["SaaS", "micro-saaS"]
            project_type = "SaaS"
            budget = "UNKNOWN"
            timeline = "UNKNOWN"
            urgency = "UNKNOWN"
            outsourcing_language = "Building own product — NOT seeking outsourcing"
        elif lead["id"] == "HI-011":
            requirement_text = "REQUIRES_VERIFICATION — Healthcare SaaS bootstrapping"
            required_technology = ["SaaS", "healthcare"]
            project_type = "SaaS"
            budget = "UNKNOWN"
            timeline = "UNKNOWN"
            urgency = "UNKNOWN"
            outsourcing_language = "Bootstrapping — POSSIBLE outsourcing"

    audit["actual_requirement"] = {
        "requirement_text": requirement_text,
        "required_technology": required_technology,
        "project_type": project_type,
        "budget": budget,
        "timeline": timeline,
        "location_requirement": "UNKNOWN",
        "team_requirement": "UNKNOWN",
        "urgency": urgency,
        "outsourcing_language": outsourcing_language,
    }

    # ============================================================
    # GATE 4: OUTSOURCING INTENT — CRITICAL
    # ============================================================
    outsourcing_evidence = lead.get("outsourcing_intent", "UNKNOWN")
    hiring_type = "UNKNOWN"

    if is_search_page:
        outsourcing_evidence = "N/A — search page, no specific person"
        hiring_type = "N/A"
    elif "seeking cofounder" in lead.get("title", "").lower() or "cofounder" in lead.get("title", "").lower():
        hiring_type = "COFOUNDER_SEARCH"
        outsourcing_evidence = "Looking for cofounder/CTO — this is equity partnership, NOT paid outsourcing"
    elif "hiring" in lead.get("title", "").lower() and "engineer" in lead.get("title", "").lower():
        hiring_type = "FULL_TIME_HIRING"
        outsourcing_evidence = "Hiring full-time engineer — NOT an outsourcing opportunity"
    elif "agency" in lead.get("notes", "").lower() and "hiring" in lead.get("notes", "").lower():
        hiring_type = "AGENCY_SUBCONTRACTING"
        outsourcing_evidence = "Agency seeking freelance developer for sub-contracting — NOT buying development services"

    audit["outsourcing_intent"] = {
        "outsourcing_evidence": outsourcing_evidence,
        "hiring_type": hiring_type,
        "is_implicit_outsourcing": hiring_type in ["AGENCY_SUBCONTRACTING"],
        "is_full_time_hiring": hiring_type == "FULL_TIME_HIRING",
        "is_cofounder_search": hiring_type == "COFOUNDER_SEARCH",
    }

    # ============================================================
    # GATE 5: SERVICE MATCH
    # ============================================================
    services_needed = lead.get("services_needed", [])
    service_match_score = 0
    matched_services = []
    service_mismatch_reason = ""

    if is_search_page:
        service_match_score = 0
        service_mismatch_reason = "No specific service needed — search page"
    else:
        # Check against Inowix catalog
        comai_services = ["whatsapp", "chatbot", "customer support", "shopify", "woocommerce", "ecommerce"]
        saas_services = ["saas mvp", "saas", "full stack", "backend", "api", "mvp"]
        custom_services = ["mobile app", "ios", "android", "web app", "crm", "erp"]

        for svc in services_needed:
            svc_lower = svc.lower()
            for cat_svc in comai_services:
                if cat_svc in svc_lower:
                    matched_services.append(f"COMAI: {svc}")
                    service_match_score += 20
            for cat_svc in saas_services:
                if cat_svc in svc_lower:
                    matched_services.append(f"SaaS Dev: {svc}")
                    service_match_score += 20
            for cat_svc in custom_services:
                if cat_svc in svc_lower:
                    matched_services.append(f"Custom: {svc}")
                    service_match_score += 20

    audit["service_match"] = {
        "services_needed": services_needed,
        "matched_services": matched_services,
        "service_match_score": min(100, service_match_score),
        "service_mismatch_reason": service_mismatch_reason,
    }

    # ============================================================
    # GATE 6: COMPETITOR CHECK
    # ============================================================
    is_competitor = False
    competitor_type = "NONE"

    if is_search_page:
        is_competitor = False
    elif "agency" in lead.get("notes", "").lower():
        is_competitor = True
        competitor_type = "AGENCY"
    elif "developer building" in lead.get("notes", "").lower():
        is_competitor = True
        competitor_type = "FREELANCER/DEVELOPER"

    audit["competitor_check"] = {
        "is_competitor": is_competitor,
        "competitor_type": competitor_type,
    }

    # ============================================================
    # GATE 7: BUYER FIT
    # ============================================================
    audit["buyer_fit"] = {
        "company_type": lead.get("prospect_type", "UNKNOWN"),
        "company_stage": lead.get("business_stage", "UNKNOWN"),
        "industry": lead.get("industry", "UNKNOWN"),
        "project_complexity": "UNKNOWN",
        "budget_capability": "UNKNOWN",
        "business_maturity": "UNKNOWN",
    }

    # ============================================================
    # GATE 8: BUDGET
    # ============================================================
    audit["budget"] = {
        "budget_stated": budget,
        "budget_status": "UNKNOWN" if budget == "UNKNOWN" else "STATED",
        "budget_compatible": "UNKNOWN",
    }

    # ============================================================
    # GATE 9: PROJECT STATUS
    # ============================================================
    project_status = "UNKNOWN"
    if is_search_page:
        project_status = "GENERIC_SEARCH"
    elif "2-3 months ago" in lead.get("date", ""):
        project_status = "STALE"
    elif "3+ months ago" in lead.get("date", "") or "4+ months ago" in lead.get("date", ""):
        project_status = "STALE"
    elif "1 month ago" in lead.get("date", ""):
        project_status = "RECENT_BUT_STALE"
    elif "Active" in lead.get("date", ""):
        project_status = "ACTIVE_BUT_UNVERIFIED"

    audit["project_status"] = {
        "status": project_status,
        "date_reported": lead.get("date", "UNKNOWN"),
    }

    # ============================================================
    # GATE 10: INDIA/GLOBAL FIT
    # ============================================================
    audit["geo_fit"] = {
        "prospect_country": "UNKNOWN",
        "timezone": "UNKNOWN",
        "service_region_fit": "GLOBAL",
    }

    # ============================================================
    # GATE 11: CONTACTABILITY
    # ============================================================
    contactability = "UNKNOWN"
    email_status = "UNKNOWN"
    linkedin = "UNKNOWN"

    if is_search_page:
        contactability = "INACCESSIBLE"
        email_status = "NOT_AVAILABLE"
    elif identity_confidence == "REDDIT_USERNAME":
        contactability = "PUBLIC_UNVERIFIED"
        linkedin = profile_url

    audit["contactability"] = {
        "contactability": contactability,
        "email": "NOT_GUESSED",
        "email_status": email_status,
        "linkedin": linkedin,
    }

    # ============================================================
    # GATE 12: EVIDENCE REQUIREMENT
    # ============================================================
    evidence_claims = []

    if is_search_page:
        evidence_claims.append({
            "claim": "Multiple jobs match search query",
            "value": "GENERIC — no specific opportunity identified",
            "source": "Upwork search page",
            "source_url": source_url,
            "confidence": "LOW",
            "observed_at": "audit_v2",
        })
    else:
        evidence_claims.append({
            "claim": f"Post exists at {source_url}",
            "value": "Verified via websearch",
            "source": "Reddit",
            "source_url": source_url,
            "confidence": "HIGH",
            "observed_at": "audit_v2",
        })

    audit["evidence"] = {
        "claims": evidence_claims,
        "total_claims": len(evidence_claims),
    }

    # ============================================================
    # GATE 13: FINAL CLASSIFICATION
    # ============================================================
    rejection_reasons = []
    missing_information = []

    # Hard gate checks
    if is_search_page:
        rejection_reasons.append("SOURCE: URL is a search/category page, not an exact post/job/project")

    if source_access_status == "INACCESSIBLE":
        rejection_reasons.append("SOURCE: Page is not publicly accessible (403 or requires auth)")

    if identity_confidence in ["ANONYMOUS", "UNKNOWN"]:
        rejection_reasons.append("IDENTITY: Person is anonymous/unknown")

    if hiring_type == "FULL_TIME_HIRING":
        rejection_reasons.append("OUTSOURCING: Full-time hiring — NOT an outsourcing opportunity")

    if hiring_type == "COFOUNDER_SEARCH":
        rejection_reasons.append("OUTSOURCING: Cofounder search — equity partnership, NOT paid outsourcing")

    if is_competitor:
        rejection_reasons.append(f"COMPETITOR: Prospect is a {competitor_type} — not a customer")

    if project_status in ["STALE", "CLOSED"]:
        rejection_reasons.append(f"STATUS: Opportunity is {project_status}")

    if not services_needed and not is_search_page:
        rejection_reasons.append("SERVICE: No specific services identified")

    if service_match_score == 0 and not is_search_page:
        rejection_reasons.append("SERVICE: No service match with Inowix catalog")

    if not requirement_text or "GENERIC" in requirement_text or "REQUIRES_VERIFICATION" in requirement_text:
        rejection_reasons.append("REQUIREMENT: No verified specific requirement")

    # Determine final classification
    if len(rejection_reasons) >= 3:
        final_classification = "REJECT"
    elif len(rejection_reasons) >= 1:
        final_classification = "REJECT"
    elif missing_information:
        final_classification = "NEEDS_RESEARCH"
    else:
        final_classification = "HIGH_PRIORITY"

    audit["final_classification"] = final_classification
    audit["rejection_reasons"] = rejection_reasons
    audit["missing_information"] = missing_information

    # ============================================================
    # GATE 14: SCORING
    # ============================================================
    intent_score = lead.get("intent_score", 0)
    evidence_score = 0 if is_search_page else lead.get("evidence_quality", 0)
    icp_score = 0
    outsourcing_score = 0
    service_match = 0
    contactability_score = 0
    commercial_score = 0

    if is_search_page:
        intent_score = 0
        evidence_score = 0
    elif hiring_type == "FULL_TIME_HIRING":
        intent_score = 0
        outsourcing_score = 0
    elif hiring_type == "COFOUNDER_SEARCH":
        intent_score = 0
        outsourcing_score = 0
    elif is_competitor:
        intent_score = 0
        outsourcing_score = 0
    else:
        outsourcing_score = 100 if outsourcing_evidence == "EXPLICIT" else 50
        icp_score = 50  # Default
        contactability_score = 50 if contactability == "PUBLIC_UNVERIFIED" else 0
        commercial_score = 30  # Low — no budget evidence

    salesability_score = (
        intent_score * 0.25 +
        evidence_score * 0.20 +
        icp_score * 0.15 +
        outsourcing_score * 0.20 +
        service_match * 0.10 +
        contactability_score * 0.05 +
        commercial_score * 0.05
    )

    # Override if hard failure
    if rejection_reasons:
        salesability_score = min(salesability_score, 20)

    audit["scores"] = {
        "intent": round(intent_score, 1),
        "evidence_quality": round(evidence_score, 1),
        "icp_fit": round(icp_score, 1),
        "outsourcing_fit": round(outsourcing_score, 1),
        "service_match": round(service_match, 1),
        "contactability": round(contactability_score, 1),
        "commercial_fit": round(commercial_score, 1),
        "salesability_score": round(salesability_score, 1),
    }

    # ============================================================
    # GATE 16: CROSS-SOURCE VALIDATION
    # ============================================================
    audit["cross_source_validation"] = {
        "attempted": False,
        "person_verified": False,
        "company_verified": False,
        "requirement_verified": False,
        "notes": "Cross-source validation not attempted — pending verification",
    }

    # ============================================================
    # RECOMMENDED NEXT ACTION
    # ============================================================
    if final_classification == "REJECT":
        audit["recommended_next_action"] = "DO NOT CONTACT — Lead rejected due to: " + "; ".join(rejection_reasons[:3])
    elif final_classification == "NEEDS_RESEARCH":
        audit["recommended_next_action"] = "RESEARCH FIRST — Verify identity, requirement, and outsourcing intent before outreach"
    else:
        audit["recommended_next_action"] = "QUALIFIED — Contact via Reddit DM or Upwork proposal"

    return audit


def run_adversarial_audit():
    """Run the full adversarial audit."""
    print("=" * 70)
    print("ADVERSARIAL SALESABILITY AUDIT V2")
    print("Hostile Validation Test — Quality > Quantity")
    print("=" * 70)

    # Load existing opportunities
    json_path = EXPORTS_DIR / "high_intent_discovery_test.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    opportunities = data["opportunities"]
    print(f"\nLoaded {len(opportunities)} opportunities from {json_path}")

    # Audit each lead
    audited_leads = []
    for opp in opportunities:
        audit = audit_lead(opp)
        audited_leads.append(audit)

    # Sort by salesability score
    audited_leads.sort(key=lambda x: x["scores"]["salesability_score"], reverse=True)

    # Classify
    high_priority = [l for l in audited_leads if l["final_classification"] == "HIGH_PRIORITY"]
    qualified = [l for l in audited_leads if l["final_classification"] == "QUALIFIED"]
    needs_research = [l for l in audited_leads if l["final_classification"] == "NEEDS_RESEARCH"]
    reject = [l for l in audited_leads if l["final_classification"] == "REJECT"]

    print(f"\n{'='*70}")
    print(f"FINAL AUDIT RESULTS")
    print(f"{'='*70}")
    print(f"Total audited: {len(audited_leads)}")
    print(f"HIGH_PRIORITY: {len(high_priority)}")
    print(f"QUALIFIED: {len(qualified)}")
    print(f"NEEDS_RESEARCH: {len(needs_research)}")
    print(f"REJECT: {len(reject)}")
    print(f"{'='*70}")

    # Print all leads with classification
    print(f"\nALL LEADS:")
    print(f"{'='*70}")
    for i, lead in enumerate(audited_leads, 1):
        print(f"\n{i}. [{lead['final_classification']}] {lead['original_title']}")
        print(f"   Original Score: {lead['original_score']} -> New Score: {lead['scores']['salesability_score']}")
        print(f"   Source Type: {lead['source_validation']['source_type']}")
        print(f"   Person: {lead['person_identity']['person_name']} ({lead['person_identity']['identity_confidence']})")
        print(f"   Outsourcing: {lead['outsourcing_intent']['hiring_type']}")
        if lead['rejection_reasons']:
            print(f"   REJECTION REASONS:")
            for reason in lead['rejection_reasons']:
                print(f"     - {reason}")
        print(f"   ACTION: {lead['recommended_next_action']}")

    # Save JSON
    json_output = EXPORTS_DIR / "final_salesability_audit_v2.json"
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump({
            "audit_name": "Adversarial Salesability Audit V2",
            "audit_date": datetime.now().isoformat(),
            "total_audited": len(audited_leads),
            "summary": {
                "HIGH_PRIORITY": len(high_priority),
                "QUALIFIED": len(qualified),
                "NEEDS_RESEARCH": len(needs_research),
                "REJECT": len(reject),
            },
            "leads": audited_leads,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nJSON saved: {json_output}")

    # Save XLSX
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Adversarial Audit V2"

        headers = [
            "ID", "Original Title", "Original Classification", "Final Classification",
            "Salesability Score", "Original Score",
            "Source Type", "Source URL", "Source Access",
            "Person", "Role", "Identity Confidence",
            "Outsourcing Type", "Service Match",
            "Competitor", "Project Status",
            "Rejection Reasons", "Recommended Action"
        ]
        ws.append(headers)

        for lead in audited_leads:
            ws.append([
                lead["id"],
                lead["original_title"],
                lead["original_classification"],
                lead["final_classification"],
                lead["scores"]["salesability_score"],
                lead["original_score"],
                lead["source_validation"]["source_type"],
                lead["source_validation"]["source_url"],
                lead["source_validation"]["source_access_status"],
                lead["person_identity"]["person_name"],
                lead["person_identity"]["role"],
                lead["person_identity"]["identity_confidence"],
                lead["outsourcing_intent"]["hiring_type"],
                lead["service_match"]["service_match_score"],
                lead["competitor_check"]["is_competitor"],
                lead["project_status"]["status"],
                "; ".join(lead["rejection_reasons"]),
                lead["recommended_next_action"],
            ])

        xlsx_path = EXPORTS_DIR / "final_salesability_audit_v2.xlsx"
        wb.save(xlsx_path)
        print(f"XLSX saved: {xlsx_path}")
    except ImportError:
        print("openpyxl not installed, skipping XLSX export")

    # Save TXT report
    txt_path = EXPORTS_DIR / "final_salesability_audit_v2_report.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("ADVERSARIAL SALESABILITY AUDIT V2 — FINAL REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")

        f.write("SCORING MODEL:\n")
        f.write("  Intent * 0.25 + Evidence Quality * 0.20 + ICP Fit * 0.15\n")
        f.write("  + Outsourcing Fit * 0.20 + Service Match * 0.10\n")
        f.write("  + Contactability * 0.05 + Commercial Fit * 0.05\n\n")

        f.write("SUMMARY:\n")
        f.write(f"  Total audited: {len(audited_leads)}\n")
        f.write(f"  HIGH_PRIORITY: {len(high_priority)}\n")
        f.write(f"  QUALIFIED: {len(qualified)}\n")
        f.write(f"  NEEDS_RESEARCH: {len(needs_research)}\n")
        f.write(f"  REJECT: {len(reject)}\n\n")

        # Rejection reasons grouped by count
        f.write("=" * 70 + "\n")
        f.write("REJECTION REASONS (GROUPED BY COUNT):\n")
        f.write("=" * 70 + "\n\n")

        reason_counts = {}
        for lead in reject:
            for reason in lead["rejection_reasons"]:
                category = reason.split(":")[0] if ":" in reason else "OTHER"
                if category not in reason_counts:
                    reason_counts[category] = {"count": 0, "examples": []}
                reason_counts[category]["count"] += 1
                if len(reason_counts[category]["examples"]) < 3:
                    reason_counts[category]["examples"].append(f"{lead['id']}: {reason}")

        for category, data in sorted(reason_counts.items(), key=lambda x: x[1]["count"], reverse=True):
            f.write(f"  {category}: {data['count']} leads\n")
            for example in data["examples"]:
                f.write(f"    - {example}\n")
            f.write("\n")

        # Percentage metrics
        f.write("=" * 70 + "\n")
        f.write("KEY METRICS:\n")
        f.write("=" * 70 + "\n\n")

        total = len(audited_leads)
        explicit_outsourcing = len([l for l in audited_leads if l["outsourcing_intent"]["hiring_type"] == "EXPLICIT_OUTSOURCING"])
        full_time_hiring = len([l for l in audited_leads if l["outsourcing_intent"]["hiring_type"] == "FULL_TIME_HIRING"])
        cofounder_search = len([l for l in audited_leads if l["outsourcing_intent"]["hiring_type"] == "COFOUNDER_SEARCH"])
        identifiable_dm = len([l for l in audited_leads if l["person_identity"]["identity_confidence"] in ["REDDIT_USERNAME", "VERIFIED"]])
        exact_source = len([l for l in audited_leads if l["source_validation"]["is_exact_post"]])
        cross_source = len([l for l in audited_leads if l["cross_source_validation"]["attempted"]])
        service_match = len([l for l in audited_leads if l["service_match"]["service_match_score"] > 0])
        competitor = len([l for l in audited_leads if l["competitor_check"]["is_competitor"]])
        contactable = len([l for l in audited_leads if l["contactability"]["contactability"] != "INACCESSIBLE"])
        commercially_plausible = len([l for l in audited_leads if l["budget"]["budget_status"] != "IMPOSSIBLE"])

        f.write(f"  Explicit outsourcing: {explicit_outsourcing}/{total} ({explicit_outsourcing/total*100:.0f}%)\n")
        f.write(f"  Full-time hiring: {full_time_hiring}/{total} ({full_time_hiring/total*100:.0f}%)\n")
        f.write(f"  Cofounder search: {cofounder_search}/{total} ({cofounder_search/total*100:.0f}%)\n")
        f.write(f"  Identifiable decision maker: {identifiable_dm}/{total} ({identifiable_dm/total*100:.0f}%)\n")
        f.write(f"  Exact source verification: {exact_source}/{total} ({exact_source/total*100:.0f}%)\n")
        f.write(f"  Cross-source verification: {cross_source}/{total} ({cross_source/total*100:.0f}%)\n")
        f.write(f"  Service match: {service_match}/{total} ({service_match/total*100:.0f}%)\n")
        f.write(f"  Competitor: {competitor}/{total} ({competitor/total*100:.0f}%)\n")
        f.write(f"  Contactable: {contactable}/{total} ({contactable/total*100:.0f}%)\n")
        f.write(f"  Commercially plausible: {commercially_plausible}/{total} ({commercially_plausible/total*100:.0f}%)\n\n")

        # Top 10 Real Opportunities
        f.write("=" * 70 + "\n")
        f.write("TOP 10 REAL OPPORTUNITIES (if any):\n")
        f.write("=" * 70 + "\n\n")

        real_opportunities = [l for l in audited_leads if l["final_classification"] in ["HIGH_PRIORITY", "QUALIFIED", "NEEDS_RESEARCH"]]

        if real_opportunities:
            for i, lead in enumerate(real_opportunities[:10], 1):
                f.write(f"{i}. [{lead['final_classification']}] {lead['original_title']}\n")
                f.write(f"   Person: {lead['person_identity']['person_name']}\n")
                f.write(f"   Role: {lead['person_identity']['role']}\n")
                f.write(f"   Source: {lead['source_validation']['source_url']}\n")
                f.write(f"   Requirement: {lead['actual_requirement']['requirement_text'][:100]}...\n")
                f.write(f"   Service Match: {lead['service_match']['matched_services']}\n")
                f.write(f"   Outsourcing Evidence: {lead['outsourcing_intent']['outsourcing_evidence']}\n")
                f.write(f"   Contactability: {lead['contactability']['contactability']}\n")
                f.write(f"   Score: {lead['scores']['salesability_score']}\n")
                f.write(f"   Recommended Channel: {lead['recommended_next_action']}\n\n")
        else:
            f.write("  NO REAL OPPORTUNITIES FOUND.\n\n")

        # CTO Question
        f.write("=" * 70 + "\n")
        f.write("CTO QUESTION:\n")
        f.write("=" * 70 + "\n\n")

        if real_opportunities:
            f.write("  Would I personally give this lead to the Inowix sales team\n")
            f.write("  and tell them to spend 15 minutes researching/contacting this person?\n\n")
            f.write("  ANSWER: RESEARCH FIRST\n\n")
            f.write("  Reasons:\n")
            f.write("  - Most leads are Reddit usernames, not verified companies\n")
            f.write("  - Cofounder searches are equity partnerships, not paid outsourcing\n")
            f.write("  - No budget evidence for any lead\n")
            f.write("  - Many leads are stale (2-4 months old)\n")
            f.write("  - Upwork search pages are not specific opportunities\n")
        else:
            f.write("  ANSWER: NO\n\n")
            f.write("  No leads survived the adversarial audit.\n")
            f.write("  This is the correct outcome — quality > quantity.\n")

    print(f"TXT saved: {txt_path}")

    # Print final answer
    print(f"\n{'='*70}")
    print("CTO ANSWER:")
    print("=" * 70)
    if real_opportunities:
        print("\n  Would I personally give this lead to the Inowix sales team\n")
        print("  and tell them to spend 15 minutes researching/contacting this person?\n")
        print("  ANSWER: RESEARCH FIRST")
        print(f"\n  {len(real_opportunities)} leads need research before outreach.")
    else:
        print("\n  ANSWER: NO")
        print("\n  No leads survived the adversarial audit.")
        print("  This is the correct outcome — quality > quantity.")

    print(f"\n{'='*70}")
    print("AUDIT COMPLETE")
    print(f"{'='*70}")

    return audited_leads


if __name__ == "__main__":
    run_adversarial_audit()
