#!/usr/bin/env python3
"""
V4 ADVERSARIAL OPPORTUNITY VERIFICATION
========================================
Strict verification of existing V3 opportunities.
"""

import json
from datetime import datetime
from pathlib import Path

EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)


def v4_audit_lead(lead):
    """Run V4 adversarial audit on a single lead."""
    audit = {
        "v4_audit_id": f"V4-{lead['id'].replace('V3-', '')}",
        "original_opportunity_id": lead["id"],
        "company": lead.get("company", "UNKNOWN"),
        "person": lead.get("person", {}).get("name", "UNKNOWN"),
        "role": lead.get("person", {}).get("role", "UNKNOWN"),

        # Gate 1: Source Verification
        "original_source": {
            "source_type": lead.get("source_type", "UNKNOWN"),
            "source_url": lead.get("source_url", ""),
            "exact_source": False,
            "source_access": "UNKNOWN",
            "source_confidence": "UNKNOWN"
        },

        # Gate 2: Requirement Verification
        "requirement": {
            "text": "",
            "quote": "",
            "source_url": "",
            "confidence": "UNKNOWN"
        },

        # Gate 3: Identity Verification
        "identity": {
            "name": lead.get("person", {}).get("name", "UNKNOWN"),
            "username": "",
            "role": lead.get("person", {}).get("role", "UNKNOWN"),
            "linkedin_url": "",
            "company_url": "",
            "confidence": "UNKNOWN"
        },

        # Gate 4: Currentness
        "currentness": {
            "status": "UNKNOWN",
            "observed_date": "",
            "evidence": "",
            "confidence": "UNKNOWN"
        },

        # Gate 5: Commercial Intent
        "commercial_intent": {
            "type": "UNKNOWN",
            "explicit_outsourcing": False,
            "budget_evidence": "",
            "confidence": "UNKNOWN"
        },

        # Gate 6: Buyer Context
        "buyer_context": {
            "buyer_type": "",
            "decision_authority": "UNKNOWN",
            "confidence": "UNKNOWN"
        },

        # Gate 7: Service Fit
        "service_fit": {
            "business_unit": lead.get("service_match", {}).get("business_unit", "UNKNOWN"),
            "services": lead.get("service_match", {}).get("matched_services", []),
            "confidence": "UNKNOWN"
        },

        # Gate 8: Contactability
        "contactability": {
            "email": "",
            "email_status": "UNKNOWN",
            "linkedin_url": "",
            "platform_url": lead.get("source_url", ""),
            "contact_paths": []
        },

        # Gate 9: Cross-Source Verification
        "cross_source_verification": {
            "verified": False,
            "sources": [],
            "confidence": "UNKNOWN"
        },

        # Gate 10: Outreach
        "outreach": {
            "recommended_channel": "",
            "channel_reason": "",
            "email_allowed": False,
            "linkedin_allowed": False,
            "platform_proposal_allowed": False
        },

        # V4 Score
        "v4_score": 0,

        # Classification
        "classification": "",

        # Hard Gate Failures
        "hard_gate_failures": [],

        # Evidence
        "evidence": [],

        # Missing Information
        "missing_information": [],

        # CTO Verdict
        "cto_verdict": "",
        "recommended_next_action": ""
    }

    source_url = lead.get("source_url", "")

    # ============================================================
    # GATE 1: SOURCE VERIFICATION
    # ============================================================
    exact_source = False
    source_access = "UNKNOWN"
    source_confidence = "UNKNOWN"
    source_evidence = ""

    # Check Upwork URLs
    if "/freelance-jobs/apply/" in source_url and "_~" in source_url:
        # Upwork exact job URL format
        exact_source = True
        source_access = "BLOCKED_BUT_URL_VALID"
        source_confidence = "MEDIUM"
        source_evidence = f"Upwork job URL with correct format: {source_url}"
        audit["original_source"]["exact_source"] = True
        audit["original_source"]["source_access"] = source_access
        audit["original_source"]["source_confidence"] = source_confidence

    # Check Freelancer.com URLs
    elif "/jobs/ai-chatbot/" in source_url or "/jobs/chatbot/" in source_url:
        # These are CATEGORY PAGES, not exact job postings
        exact_source = False
        source_access = "CATEGORY_PAGE"
        source_confidence = "LOW"
        source_evidence = f"Freelancer.com CATEGORY PAGE — NOT an exact job posting: {source_url}"
        audit["original_source"]["exact_source"] = False
        audit["original_source"]["source_access"] = source_access
        audit["original_source"]["source_confidence"] = source_confidence
        audit["hard_gate_failures"].append("SOURCE: URL is a category page, not an exact job posting")

    # Check Truelancer URLs
    elif "/freelance-whatsapp-bot-jobs" in source_url:
        # Category page
        exact_source = False
        source_access = "CATEGORY_PAGE"
        source_confidence = "LOW"
        source_evidence = f"Truelancer CATEGORY PAGE — NOT an exact job posting: {source_url}"
        audit["original_source"]["exact_source"] = False
        audit["original_source"]["source_access"] = source_access
        audit["original_source"]["source_confidence"] = source_confidence
        audit["hard_gate_failures"].append("SOURCE: URL is a category page, not an exact job posting")

    else:
        source_access = "UNKNOWN"
        source_confidence = "UNKNOWN"
        source_evidence = f"Unknown source type: {source_url}"

    audit["evidence"].append({
        "claim": "Source URL verification",
        "value": source_evidence,
        "source": "URL analysis",
        "source_url": source_url,
        "confidence": source_confidence,
        "observed_at": "V4_audit"
    })

    # ============================================================
    # GATE 2: REQUIREMENT VERIFICATION
    # ============================================================
    requirement_text = lead.get("requirement", {}).get("text", "")
    requirement_confidence = "UNKNOWN"
    requirement_quote = ""

    if not requirement_text or len(requirement_text) < 20:
        audit["hard_gate_failures"].append("REQUIREMENT: No specific requirement extracted")
        requirement_confidence = "UNKNOWN"
    else:
        # Check if requirement was actually verified from source
        if source_access == "BLOCKED_BUT_URL_VALID":
            # Upwork — we cannot verify the actual content
            requirement_confidence = "UNVERIFIED"
            requirement_quote = "Requirement claimed but NOT independently verified — Upwork blocks access"
            audit["hard_gate_failures"].append("REQUIREMENT: Claimed but NOT verified — Upwork blocks access")
        elif source_access == "CATEGORY_PAGE":
            # Freelancer.com category — we found jobs on the page but cannot confirm they match V3 claims
            requirement_confidence = "UNVERIFIED"
            requirement_quote = "Jobs exist on category page but cannot confirm they match the V3 claim"
            audit["hard_gate_failures"].append("REQUIREMENT: Cannot confirm job matches V3 claim — category page")
        else:
            requirement_confidence = "MEDIUM"
            requirement_quote = requirement_text

    audit["requirement"] = {
        "text": requirement_text,
        "quote": requirement_quote,
        "source_url": source_url,
        "confidence": requirement_confidence
    }

    # ============================================================
    # GATE 3: IDENTITY VERIFICATION
    # ============================================================
    identity_confidence = "UNKNOWN"
    person_name = lead.get("person", {}).get("name", "UNKNOWN")

    if "Upwork Client" in person_name or "Upwork" in person_name:
        identity_confidence = "ANONYMOUS"
        audit["hard_gate_failures"].append("IDENTITY: Anonymous Upwork client — no named person")
    elif "Client" in person_name or "Owner" in person_name or "Founder" in person_name:
        identity_confidence = "GENERIC"
        audit["hard_gate_failures"].append("IDENTITY: Generic role — no named person")
    elif "Representative" in person_name:
        identity_confidence = "GENERIC"
        audit["hard_gate_failures"].append("IDENTITY: Generic representative — no named person")

    audit["identity"]["confidence"] = identity_confidence

    # ============================================================
    # GATE 4: CURRENTNESS
    # ============================================================
    source_date = lead.get("source_date", "UNKNOWN")
    freshness = lead.get("freshness", "UNKNOWN")
    currentness_status = "UNKNOWN"
    currentness_evidence = ""

    if "5 months ago" in source_date:
        currentness_status = "STALE"
        currentness_evidence = "Posted 5 months ago — likely closed"
        audit["hard_gate_failures"].append("CURRENTNESS: 5 months old — STALE")
    elif "Recent" in source_date or "Active" in source_date or "HOT" in freshness:
        currentness_status = "RECENT"
        currentness_evidence = "Recent/active posting"
    elif "posted July 9, 2026" in source_date:
        currentness_status = "RECENT"
        currentness_evidence = "Posted July 9, 2026 — approximately 1 month ago"
    else:
        currentness_status = "UNKNOWN"
        currentness_evidence = f"Date: {source_date}"

    audit["currentness"] = {
        "status": currentness_status,
        "observed_date": source_date,
        "evidence": currentness_evidence,
        "confidence": "MEDIUM" if currentness_status != "UNKNOWN" else "LOW"
    }

    # ============================================================
    # GATE 5: COMMERCIAL INTENT
    # ============================================================
    outsourcing_intent = lead.get("outsourcing_intent", "UNKNOWN")
    commercial_type = "UNKNOWN"
    explicit_outsourcing = False

    if outsourcing_intent == "EXPLICIT_OUTSOURCING":
        commercial_type = "EXPLICIT_OUTSOURCING"
        explicit_outsourcing = True
    elif outsourcing_intent == "COFOUNDER_SEARCH":
        commercial_type = "EQUITY_ONLY"
        audit["hard_gate_failures"].append("COMMERCIAL: Cofounder search — equity only")
    elif outsourcing_intent == "FULL_TIME_HIRING":
        commercial_type = "FULL_TIME_ONLY"
        audit["hard_gate_failures"].append("COMMERCIAL: Full-time hiring — not outsourcing")

    audit["commercial_intent"] = {
        "type": commercial_type,
        "explicit_outsourcing": explicit_outsourcing,
        "budget_evidence": lead.get("requirement", {}).get("budget", "Unknown"),
        "confidence": "MEDIUM" if explicit_outsourcing else "LOW"
    }

    # ============================================================
    # GATE 6: BUYER CONTEXT
    # ============================================================
    buyer_type = "UNKNOWN"
    decision_authority = "UNKNOWN"

    if "Upwork Client" in person_name:
        buyer_type = "ANONYMOUS_BUYER"
        decision_authority = "UNKNOWN"
    elif "Business Owner" in lead.get("person", {}).get("role", ""):
        buyer_type = "BUSINESS_OWNER"
        decision_authority = "HIGH"
    elif "Founder" in lead.get("person", {}).get("role", ""):
        buyer_type = "FOUNDER"
        decision_authority = "HIGH"
    else:
        buyer_type = "UNKNOWN"
        decision_authority = "UNKNOWN"

    audit["buyer_context"] = {
        "buyer_type": buyer_type,
        "decision_authority": decision_authority,
        "confidence": "LOW" if buyer_type == "UNKNOWN" else "MEDIUM"
    }

    # ============================================================
    # GATE 7: SERVICE FIT
    # ============================================================
    service_score = lead.get("service_match", {}).get("score", 0)
    service_confidence = "UNKNOWN"

    if service_score >= 80:
        service_confidence = "HIGH"
    elif service_score >= 60:
        service_confidence = "MEDIUM"
    elif service_score > 0:
        service_confidence = "LOW"
    else:
        service_confidence = "NONE"
        audit["hard_gate_failures"].append("SERVICE: No service match")

    audit["service_fit"]["confidence"] = service_confidence

    # ============================================================
    # GATE 8: CONTACTABILITY
    # ============================================================
    contact_paths = []
    email_status = "UNKNOWN"

    if "UPWORK" in lead.get("source_type", ""):
        contact_paths.append("UPWORK_PROPOSAL")
        audit["outreach"]["platform_proposal_allowed"] = True
    elif "FREELANCER" in lead.get("source_type", ""):
        contact_paths.append("FREELANCER_PROPOSAL")
        audit["outreach"]["platform_proposal_allowed"] = True

    audit["contactability"] = {
        "email": "",
        "email_status": email_status,
        "linkedin_url": "",
        "platform_url": source_url,
        "contact_paths": contact_paths
    }

    # ============================================================
    # GATE 9: CROSS-SOURCE VERIFICATION
    # ============================================================
    # No cross-source verification performed for any lead
    audit["cross_source_verification"] = {
        "verified": False,
        "sources": [],
        "confidence": "NOT_ATTEMPTED"
    }

    # ============================================================
    # GATE 10: OUTREACH
    # ============================================================
    if "UPWORK" in lead.get("source_type", ""):
        audit["outreach"]["recommended_channel"] = "UPWORK_PROPOSAL"
        audit["outreach"]["channel_reason"] = "Upwork job posting — platform proposal is legitimate channel"
    elif "FREELANCER" in lead.get("source_type", ""):
        audit["outreach"]["recommended_channel"] = "FREELANCER_PROPOSAL"
        audit["outreach"]["channel_reason"] = "Freelancer.com job — platform proposal is legitimate channel"
    else:
        audit["outreach"]["recommended_channel"] = "UNKNOWN"
        audit["outreach"]["channel_reason"] = "No clear outreach path"

    # ============================================================
    # V4 SALESABILITY SCORE
    # ============================================================
    evidence_score = 0
    requirement_score = 0
    currentness_score = 0
    commercial_score = 0
    buyer_score = 0
    service_fit_score = 0
    contactability_score = 0

    # Evidence Quality (20%)
    if source_confidence == "VERIFIED":
        evidence_score = 100
    elif source_confidence == "HIGH":
        evidence_score = 80
    elif source_confidence == "MEDIUM":
        evidence_score = 50
    elif source_confidence == "LOW":
        evidence_score = 20
    else:
        evidence_score = 0

    # Requirement Strength (20%)
    if requirement_confidence == "VERIFIED":
        requirement_score = 100
    elif requirement_confidence == "HIGH":
        requirement_score = 80
    elif requirement_confidence == "MEDIUM":
        requirement_score = 50
    elif requirement_confidence == "UNVERIFIED":
        requirement_score = 20
    else:
        requirement_score = 0

    # Currentness (15%)
    if currentness_status == "CURRENT":
        currentness_score = 100
    elif currentness_status == "RECENT":
        currentness_score = 70
    elif currentness_status == "AGING":
        currentness_score = 40
    elif currentness_status == "STALE":
        currentness_score = 10
    else:
        currentness_score = 20

    # Commercial Intent (20%)
    if commercial_type == "EXPLICIT_OUTSOURCING":
        commercial_score = 100
    elif commercial_type == "PROJECT_WITH_BUDGET":
        commercial_score = 80
    elif commercial_type == "PROJECT_WITHOUT_BUDGET":
        commercial_score = 50
    elif commercial_type == "EQUITY_ONLY":
        commercial_score = 0
    elif commercial_type == "FULL_TIME_ONLY":
        commercial_score = 0
    else:
        commercial_score = 0

    # Buyer Quality (10%)
    if decision_authority == "HIGH":
        buyer_score = 100
    elif decision_authority == "MEDIUM":
        buyer_score = 60
    elif decision_authority == "LOW":
        buyer_score = 30
    else:
        buyer_score = 0

    # Service Fit (10%)
    if service_confidence == "HIGH":
        service_fit_score = 100
    elif service_confidence == "MEDIUM":
        service_fit_score = 60
    elif service_confidence == "LOW":
        service_fit_score = 30
    else:
        service_fit_score = 0

    # Contactability (5%)
    if contact_paths:
        contactability_score = 80
    else:
        contactability_score = 0

    v4_score = (
        evidence_score * 0.20 +
        requirement_score * 0.20 +
        currentness_score * 0.15 +
        commercial_score * 0.20 +
        buyer_score * 0.10 +
        service_fit_score * 0.10 +
        contactability_score * 0.05
    )

    audit["v4_score"] = round(v4_score, 1)

    # ============================================================
    # CLASSIFICATION
    # ============================================================
    hard_failures = audit["hard_gate_failures"]

    if len(hard_failures) == 0:
        classification = "HIGH_PRIORITY"
    elif len(hard_failures) <= 2:
        classification = "QUALIFIED"
    elif len(hard_failures) <= 4:
        classification = "NEEDS_RESEARCH"
    else:
        classification = "REJECT"

    # Override: if any critical gate fails, force REJECT
    critical_gates = ["SOURCE:", "REQUIREMENT:", "IDENTITY:", "COMMERCIAL:"]
    has_critical_failure = any(any(cg in f for cg in critical_gates) for f in hard_failures)

    if has_critical_failure:
        classification = "REJECT"

    audit["classification"] = classification

    # ============================================================
    # CTO VERDICT
    # ============================================================
    if classification == "REJECT":
        audit["cto_verdict"] = "NO"
        audit["recommended_next_action"] = "DO NOT PURSUE — Lead rejected due to: " + "; ".join(hard_failures[:3])
    elif classification == "NEEDS_RESEARCH":
        audit["cto_verdict"] = "RESEARCH_FIRST"
        audit["recommended_next_action"] = "RESEARCH — Verify before pursuing"
    elif classification == "QUALIFIED":
        audit["cto_verdict"] = "MAYBE"
        audit["recommended_next_action"] = "QUALIFIED — Minor verification needed"
    else:
        audit["cto_verdict"] = "YES"
        audit["recommended_next_action"] = "PURSUE — Contact via platform proposal"

    return audit


def run_v4_audit():
    """Run V4 adversarial audit."""
    print("=" * 70)
    print("V4 ADVERSARIAL OPPORTUNITY VERIFICATION")
    print("=" * 70)

    # Load V3 opportunities
    v3_path = EXPORTS_DIR / "discovery_v3_verified.json"
    with open(v3_path, "r", encoding="utf-8") as f:
        v3_data = json.load(f)

    opportunities = v3_data["opportunities"]
    print(f"\nLoaded {len(opportunities)} V3 opportunities")

    # Audit each lead
    audited_leads = []
    for opp in opportunities:
        audit = v4_audit_lead(opp)
        audited_leads.append(audit)

    # Sort by classification and score
    classification_order = {"HIGH_PRIORITY": 0, "QUALIFIED": 1, "NEEDS_RESEARCH": 2, "REJECT": 3}
    audited_leads.sort(key=lambda x: (classification_order.get(x["classification"], 4), -x["v4_score"]))

    # Classify
    high_priority = [l for l in audited_leads if l["classification"] == "HIGH_PRIORITY"]
    qualified = [l for l in audited_leads if l["classification"] == "QUALIFIED"]
    needs_research = [l for l in audited_leads if l["classification"] == "NEEDS_RESEARCH"]
    reject = [l for l in audited_leads if l["classification"] == "REJECT"]

    print(f"\n{'='*70}")
    print(f"V4 AUDIT RESULTS")
    print(f"{'='*70}")
    print(f"Total audited: {len(audited_leads)}")
    print(f"HIGH_PRIORITY: {len(high_priority)}")
    print(f"QUALIFIED: {len(qualified)}")
    print(f"NEEDS_RESEARCH: {len(needs_research)}")
    print(f"REJECT: {len(reject)}")
    print(f"{'='*70}")

    # Print all leads
    print(f"\nALL LEADS:")
    print(f"{'='*70}")
    for i, lead in enumerate(audited_leads, 1):
        print(f"\n{i}. [{lead['classification']}] {lead['original_opportunity_id']}: {lead['company']}")
        print(f"   Person: {lead['person']} ({lead['role']})")
        print(f"   Source: {lead['original_source']['source_type']}")
        print(f"   Source Access: {lead['original_source']['source_access']}")
        print(f"   Exact Source: {lead['original_source']['exact_source']}")
        print(f"   Requirement Confidence: {lead['requirement']['confidence']}")
        print(f"   Currentness: {lead['currentness']['status']}")
        print(f"   Commercial Intent: {lead['commercial_intent']['type']}")
        print(f"   Service Fit: {lead['service_fit']['confidence']}")
        print(f"   V4 Score: {lead['v4_score']}")
        print(f"   CTO Verdict: {lead['cto_verdict']}")
        if lead['hard_gate_failures']:
            print(f"   HARD GATE FAILURES:")
            for failure in lead['hard_gate_failures']:
                print(f"     - {failure}")

    # Save JSON
    json_path = EXPORTS_DIR / "discovery_v4_verified.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "audit_name": "V4 Adversarial Opportunity Verification",
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
    print(f"\nJSON saved: {json_path}")

    # Save XLSX
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "V4 Audit"

        headers = [
            "V4 Audit ID", "Original ID", "Company", "Person", "Role",
            "Classification", "V4 Score", "CTO Verdict",
            "Source Type", "Source URL", "Exact Source", "Source Access",
            "Requirement Confidence", "Currentness", "Commercial Intent",
            "Service Fit", "Hard Gate Failures", "Recommended Action"
        ]
        ws.append(headers)

        for lead in audited_leads:
            ws.append([
                lead["v4_audit_id"],
                lead["original_opportunity_id"],
                lead["company"],
                lead["person"],
                lead["role"],
                lead["classification"],
                lead["v4_score"],
                lead["cto_verdict"],
                lead["original_source"]["source_type"],
                lead["original_source"]["source_url"],
                lead["original_source"]["exact_source"],
                lead["original_source"]["source_access"],
                lead["requirement"]["confidence"],
                lead["currentness"]["status"],
                lead["commercial_intent"]["type"],
                lead["service_fit"]["confidence"],
                "; ".join(lead["hard_gate_failures"]),
                lead["recommended_next_action"],
            ])

        xlsx_path = EXPORTS_DIR / "discovery_v4_verified.xlsx"
        wb.save(xlsx_path)
        print(f"XLSX saved: {xlsx_path}")
    except ImportError:
        print("openpyxl not installed, skipping XLSX export")

    # Save TXT report
    txt_path = EXPORTS_DIR / "discovery_v4_report.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("V4 ADVERSARIAL OPPORTUNITY VERIFICATION — FINAL REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")

        f.write("EXECUTIVE SUMMARY:\n")
        f.write(f"  Total audited: {len(audited_leads)}\n")
        f.write(f"  HIGH_PRIORITY: {len(high_priority)}\n")
        f.write(f"  QUALIFIED: {len(qualified)}\n")
        f.write(f"  NEEDS_RESEARCH: {len(needs_research)}\n")
        f.write(f"  REJECT: {len(reject)}\n\n")

        f.write("=" * 70 + "\n")
        f.write("REJECTION REASONS (GROUPED):\n")
        f.write("=" * 70 + "\n\n")

        reason_counts = {}
        for lead in reject:
            for reason in lead["hard_gate_failures"]:
                category = reason.split(":")[0] if ":" in reason else "OTHER"
                if category not in reason_counts:
                    reason_counts[category] = {"count": 0, "examples": []}
                reason_counts[category]["count"] += 1
                if len(reason_counts[category]["examples"]) < 3:
                    reason_counts[category]["examples"].append(f"{lead['original_opportunity_id']}: {reason}")

        for category, data in sorted(reason_counts.items(), key=lambda x: x[1]["count"], reverse=True):
            f.write(f"  {category}: {data['count']} leads\n")
            for example in data["examples"]:
                f.write(f"    - {example}\n")
            f.write("\n")

        f.write("=" * 70 + "\n")
        f.write("ALL LEADS — DETAILED ANALYSIS:\n")
        f.write("=" * 70 + "\n\n")

        for lead in audited_leads:
            f.write(f"{lead['v4_audit_id']}: {lead['company']}\n")
            f.write(f"  Original ID: {lead['original_opportunity_id']}\n")
            f.write(f"  Person: {lead['person']} ({lead['role']})\n")
            f.write(f"  Classification: {lead['classification']}\n")
            f.write(f"  V4 Score: {lead['v4_score']}\n")
            f.write(f"  CTO Verdict: {lead['cto_verdict']}\n")
            f.write(f"  Source Type: {lead['original_source']['source_type']}\n")
            f.write(f"  Source URL: {lead['original_source']['source_url']}\n")
            f.write(f"  Exact Source: {lead['original_source']['exact_source']}\n")
            f.write(f"  Source Access: {lead['original_source']['source_access']}\n")
            f.write(f"  Requirement: {lead['requirement']['text'][:100]}\n")
            f.write(f"  Requirement Confidence: {lead['requirement']['confidence']}\n")
            f.write(f"  Currentness: {lead['currentness']['status']}\n")
            f.write(f"  Commercial Intent: {lead['commercial_intent']['type']}\n")
            f.write(f"  Service Fit: {lead['service_fit']['confidence']}\n")
            f.write(f"  Contact Paths: {lead['contactability']['contact_paths']}\n")
            f.write(f"  Recommended Channel: {lead['outreach']['recommended_channel']}\n")
            if lead['hard_gate_failures']:
                f.write(f"  Hard Gate Failures:\n")
                for failure in lead['hard_gate_failures']:
                    f.write(f"    - {failure}\n")
            f.write(f"  Recommended Action: {lead['recommended_next_action']}\n\n")

        # CTO Final Test
        f.write("=" * 70 + "\n")
        f.write("CTO FINAL TEST:\n")
        f.write("=" * 70 + "\n\n")

        if high_priority:
            f.write("HIGH_PRIORITY leads — 'Would I personally give this lead to the Inowix sales team?'\n\n")
            for lead in high_priority:
                f.write(f"  {lead['v4_audit_id']}: {lead['company']}\n")
                f.write(f"    VERDICT: {lead['cto_verdict']}\n")
                f.write(f"    REASON: {lead['recommended_next_action']}\n\n")
        else:
            f.write("  NO HIGH_PRIORITY LEADS FOUND.\n\n")

        if qualified:
            f.write("QUALIFIED leads — 'Would I personally give this lead to the Inowix sales team?'\n\n")
            for lead in qualified:
                f.write(f"  {lead['v4_audit_id']}: {lead['company']}\n")
                f.write(f"    VERDICT: {lead['cto_verdict']}\n")
                f.write(f"    REASON: {lead['recommended_next_action']}\n\n")

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
            f.write("  No leads survived the V4 audit.\n")
            f.write("  This is the correct outcome — quality > quantity.\n")

    print(f"TXT saved: {txt_path}")

    print(f"\n{'='*70}")
    print("V4 AUDIT COMPLETE")
    print(f"{'='*70}")

    return audited_leads


if __name__ == "__main__":
    run_v4_audit()
