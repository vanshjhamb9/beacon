"""CTO FINAL 50-LEAD SALESABILITY AUDIT.

Evaluates every opportunity in intent_opportunities_50.json against strict CTO criteria.
No new leads. No modifications. Pure audit.
"""
import json
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "exports"
INPUT = OUTPUT_DIR / "intent_opportunities_50.json"

with open(INPUT, encoding="utf-8") as f:
    data = json.load(f)

opps = data["opportunities"]

# ── AUDIT RULES ──────────────────────────────────────────────────────
# Each function evaluates one dimension and returns (score, notes)

def audit_person(o):
    """A. PERSON — Is this a real, verifiable decision maker?"""
    name = o.get("person_name", "")
    role = o.get("person_role", "")
    
    # Reject generic/unverifiable names
    generic_names = ["Reddit User", "Upwork Client", "LinkedIn User", "IndieHackers User", 
                     "Product Hunt Maker", "Freelancer Client", "Upwork Freelancer"]
    
    is_generic = any(g in name for g in generic_names)
    
    # Decision maker roles
    dm_roles = ["Founder", "CEO", "CTO", "COO", "Head", "Director", "Owner", "Maker", "Solo Founder"]
    is_dm = any(r in role for r in dm_roles)
    
    if is_generic and not is_dm:
        return 0, "LOW", "Generic/unverifiable person identity"
    elif is_generic and is_dm:
        return 5, "MEDIUM", "Generic name but decision-maker role claimed"
    else:
        return 10, "HIGH", f"Named person with role: {role}"

def audit_requirement(o):
    """B. REQUIREMENT — Is there a clear, specific need?"""
    req = o.get("requirement_summary", "")
    
    strong_signals = [
        "looking for", "need", "need a", "need to build", "need help",
        "seeking", "hiring", "budget", "timeline", "must have",
        "requirement", "build a", "develop", "create a"
    ]
    
    req_lower = req.lower()
    matches = sum(1 for s in strong_signals if s in req_lower)
    
    if matches >= 3:
        return 30, "STRONG", f"Clear requirement with {matches} strong signals"
    elif matches >= 2:
        return 20, "MODERATE", f"Requirement present with {matches} signals"
    elif matches >= 1:
        return 10, "WEAK", f"Vague requirement with only {matches} signal"
    else:
        return 0, "NONE", "No clear requirement expressed"

def audit_evidence(o):
    """C. EVIDENCE — Is the source URL real and verifiable?"""
    url = o.get("source_url", "")
    
    # Check if URL points to a specific page (not a generic subreddit/page)
    generic_urls = [
        "reddit.com/r/SaaS/", "reddit.com/r/Entrepreneur/",
        "reddit.com/r/shopify/", "reddit.com/r/smallbusiness/",
        "reddit.com/r/fintech/", "reddit.com/r/healthtech/",
        "reddit.com/r/realestate/", "reddit.com/r/edtech/",
        "reddit.com/r/n8n/", "reddit.com/r/whatsapp/",
        "upwork.com/hire/software-developers/",
        "upwork.com/freelance-jobs/coding/",
        "fiverr.com/hire/shopify-development",
    ]
    
    is_generic = any(g in url for g in generic_urls)
    
    # Check for specific post URLs (contain comment/post IDs)
    has_specific_post = "/comments/" in url or "/posts/" in url
    
    if is_generic and not has_specific_post:
        return 0, "UNKNOWN", "Generic page URL - cannot verify specific requirement"
    elif has_specific_post:
        return 5, "VERIFIED", "Specific post URL present"
    else:
        return 3, "MEDIUM", "URL present but not a specific post"

def audit_recency(o):
    """D. REQUIREMENT RECENCY — How recent is the evidence?"""
    date_str = o.get("discovery_date", "")
    if not date_str:
        return 0, "UNKNOWN", "No date available"
    
    try:
        disc_date = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime(2026, 8, 8)
        days_old = (today - disc_date).days
        
        if days_old <= 7:
            return 10, "CURRENT", f"{days_old} days old"
        elif days_old <= 30:
            return 8, "RECENT", f"{days_old} days old"
        elif days_old <= 90:
            return 5, "AGING", f"{days_old} days old"
        else:
            return 0, "OLD", f"{days_old} days old"
    except:
        return 0, "UNKNOWN", "Cannot parse date"

def audit_bu_fit(o):
    """E. BUSINESS UNIT FIT — Does requirement match Inowix services?"""
    bu = o.get("bu_match", "")
    req = o.get("requirement_summary", "").lower()
    
    comai_keywords = ["whatsapp", "chatbot", "shopify", "ecommerce", "ai customer", 
                       "product recommendation", "cart recovery", "lead capture"]
    saas_keywords = ["saas", "mvp", "subscription", "platform", "multitenant"]
    custom_keywords = ["app", "dashboard", "crm", "erp", "api", "integration",
                        "mobile", "web application", "software"]
    
    if bu == "COMAI":
        matches = sum(1 for k in comai_keywords if k in req)
        score = min(20, matches * 7)
        return score, "MATCH" if matches > 0 else "WEAK", f"{matches} COMAI keywords"
    elif bu == "SAAS_DEVELOPMENT":
        matches = sum(1 for k in saas_keywords if k in req)
        score = min(20, matches * 7)
        return score, "MATCH" if matches > 0 else "WEAK", f"{matches} SaaS keywords"
    elif bu == "CUSTOM_SOFTWARE":
        matches = sum(1 for k in custom_keywords if k in req)
        score = min(20, matches * 7)
        return score, "MATCH" if matches > 0 else "WEAK", f"{matches} Custom keywords"
    return 0, "UNKNOWN", "No BU match"

def audit_outsourcing(o):
    """F. OUTSOURCING INTENT — Is this person looking to buy, not build internally?"""
    req = o.get("requirement_summary", "").lower()
    role = o.get("person_role", "").lower()
    
    explicit = ["looking for", "need a developer", "need help", "agency", "team to build",
                "external", "outsourc", "freelance", "contract"]
    strong = ["technical cofounder", "need someone", "looking for someone"]
    hiring = ["hiring", "job posting", "employee"]
    
    explicit_matches = sum(1 for e in explicit if e in req)
    strong_matches = sum(1 for s in strong if s in req)
    hiring_matches = sum(1 for h in hiring if h in req)
    
    if explicit_matches >= 2:
        return 10, "EXPLICIT_OUTSOURCING", f"{explicit_matches} explicit signals"
    elif strong_matches >= 1:
        return 8, "STRONG_EXTERNAL_SIGNAL", f"{strong_matches} strong signals"
    elif "developer" in role or "client" in role:
        return 5, "POSSIBLE_EXTERNAL_NEED", "Role suggests external need"
    elif hiring_matches > 0:
        return 2, "INTERNAL_HIRING_ONLY", "May be internal hiring"
    else:
        return 3, "UNKNOWN", "Outsourcing intent unclear"

def audit_competitor(o):
    """G. COMPETITOR CHECK — Is this a service provider, not a buyer?"""
    name = o.get("company_name", "").lower()
    req = o.get("requirement_summary", "").lower()
    
    competitor_signals = ["agency", "consulting", "development company", "software company",
                          "outsourcing", "freelance platform", "marketplace"]
    
    matches = sum(1 for c in competitor_signals if c in name or c in req)
    
    if matches > 0:
        return True, "POTENTIAL_COMPETITOR", f"{matches} competitor signals"
    return False, "BUYER", "No competitor signals"

def audit_contact(o):
    """H. CONTACT ENRICHMENT — Can we reach this person?"""
    email = o.get("public_email", "")
    linkedin = o.get("linkedin_url", "")
    
    if email and email != "":
        return 5, "VERIFIED", f"Email: {email}"
    elif linkedin and linkedin != "":
        return 3, "LINKEDIN_ONLY", f"LinkedIn: {linkedin}"
    else:
        return 0, "UNKNOWN", "No contact information"

def compute_salesability_score(audit_results):
    """Compute deterministic salesability score 0-100."""
    score = 0
    
    # Explicit Requirement (30)
    req_score = audit_results["requirement"][0]
    score += min(30, req_score)
    
    # Service Fit (20)
    bu_score = audit_results["bu_fit"][0]
    score += min(20, bu_score)
    
    # Decision Maker Verified (15)
    person_score = audit_results["person"][0]
    score += min(15, person_score)
    
    # Requirement Recency (10)
    recency_score = audit_results["recency"][0]
    score += min(10, recency_score)
    
    # External/Buying Signal (10)
    outsource_score = audit_results["outsourcing"][0]
    score += min(10, outsource_score)
    
    # Evidence Quality (5)
    evidence_score = audit_results["evidence"][0]
    score += min(5, evidence_score)
    
    # Cross-source validation (5)
    csv = o.get("cross_source_validation", {})
    if csv.get("source_count", 0) > 1:
        score += 5
    
    # Contactability (5)
    contact_score = audit_results["contact"][0]
    score += min(5, contact_score)
    
    # HARD CAPS
    if audit_results["requirement"][0] == 0:
        score = min(score, 49)
    
    if audit_results["person"][1] == "LOW" or audit_results["person"][1] == "UNKNOWN":
        if score >= 80:
            score = 79  # Cannot be HIGH PRIORITY with unknown person
    
    if audit_results["recency"][1] == "OLD":
        if score >= 80:
            score = 79
    
    return min(100, max(0, score))

def classify(score):
    """Final classification based on score."""
    if score >= 80:
        return "HIGH_PRIORITY"
    elif score >= 65:
        return "QUALIFIED"
    elif score >= 50:
        return "NEEDS_RESEARCH"
    else:
        return "REJECT"

def rejection_reason(o, classification, audit_results):
    """For REJECT leads, provide primary rejection reason."""
    if classification != "REJECT":
        return ""
    
    if audit_results["evidence"][1] == "UNKNOWN":
        return "LOW_EVIDENCE"
    if audit_results["person"][1] in ("LOW", "UNKNOWN"):
        return "UNVERIFIED_IDENTITY"
    if audit_results["requirement"][0] == 0:
        return "NO_EXPLICIT_REQUIREMENT"
    if audit_results["recency"][1] == "OLD":
        return "STALE_REQUIREMENT"
    if audit_results["competitor"][1] == "POTENTIAL_COMPETITOR":
        return "COMPETITOR"
    if audit_results["outsourcing"][1] == "INTERNAL_HIRING_ONLY":
        return "INTERNAL_HIRING_ONLY"
    if audit_results["bu_fit"][1] == "WEAK":
        return "SERVICE_MISMATCH"
    return "OTHER"

def generate_why(o, audit_results, classification):
    """One factual sentence explaining why this lead exists."""
    req = o.get("requirement_summary", "")
    person = o.get("person_name", "")
    role = o.get("person_role", "")
    bu = o.get("bu_match", "")
    evidence = audit_results["evidence"][1]
    
    if classification == "REJECT":
        reason = rejection_reason(o, classification, audit_results)
        if reason == "LOW_EVIDENCE":
            return f"Source URL is generic page - cannot verify that {person} actually expressed this requirement."
        elif reason == "UNVERIFIED_IDENTITY":
            return f"Person identity cannot be verified - generic/unverifiable name with no confirmation of role."
        elif reason == "NO_EXPLICIT_REQUIREMENT":
            return f"No clear, specific requirement found in the source material."
        elif reason == "COMPETITOR":
            return f"Company appears to be a service provider/competitor, not a buyer."
        elif reason == "INTERNAL_HIRING_ONLY":
            return f"Signal suggests internal hiring rather than outsourcing intent."
        elif reason == "SERVICE_MISMATCH":
            return f"Requirement does not clearly match any Inowix service."
        else:
            return f"Lead does not meet CTO salesability criteria."
    
    return f"{role} at {person} has publicly expressed: {req[:120]}..."

def generate_trigger(o, audit_results):
    """For qualified leads, what triggered the opportunity?"""
    req = o.get("requirement_summary", "")
    signals = o.get("technology_signals", [])
    
    if not req:
        return ""
    
    return f"Public requirement: {req[:100]}..."

def generate_service_match(o):
    """Which Inowix service matches?"""
    bu = o.get("bu_match", "")
    req = o.get("requirement_summary", "").lower()
    
    if bu == "COMAI":
        if "whatsapp" in req:
            return ["WhatsApp Commerce", "AI Chatbot"]
        if "shopify" in req:
            return ["Shopify Development", "AI Product Recommendations"]
        return ["AI Customer Support", "Chatbot Development"]
    elif bu == "SAAS_DEVELOPMENT":
        return ["SaaS MVP Development", "Full-Stack Development"]
    elif bu == "CUSTOM_SOFTWARE":
        if "mobile" in req or "app" in req:
            return ["Mobile App Development"]
        if "crm" in req:
            return ["CRM Development"]
        if "erp" in req:
            return ["ERP Development"]
        if "dashboard" in req:
            return ["Dashboard Development"]
        return ["Custom Software Development"]
    return []

# ── RUN AUDIT ON ALL 50 ──────────────────────────────────────────────
audited = []

for o in opps:
    person_score, person_conf, person_note = audit_person(o)
    req_score, req_status, req_note = audit_requirement(o)
    evidence_score, evidence_conf, evidence_note = audit_evidence(o)
    recency_score, recency_status, recency_note = audit_recency(o)
    bu_score, bu_status, bu_note = audit_bu_fit(o)
    is_competitor, competitor_status, competitor_note = audit_competitor(o)
    outsource_score, outsource_status, outsource_note = audit_outsourcing(o)
    contact_score, contact_status, contact_note = audit_contact(o)
    
    audit_results = {
        "person": (person_score, person_conf, person_note),
        "requirement": (req_score, req_status, req_note),
        "evidence": (evidence_score, evidence_conf, evidence_note),
        "recency": (recency_score, recency_status, recency_note),
        "bu_fit": (bu_score, bu_status, bu_note),
        "competitor": (is_competitor, competitor_status, competitor_note),
        "outsourcing": (outsource_score, outsource_status, outsource_note),
        "contact": (contact_score, contact_status, contact_note),
    }
    
    score = compute_salesability_score(audit_results)
    classification = classify(score)
    
    # Override: if competitor and no buying evidence
    if is_competitor and outsource_score < 5:
        classification = "REJECT"
        score = min(score, 40)
    
    why = generate_why(o, audit_results, classification)
    trigger = generate_trigger(o, audit_results)
    services = generate_service_match(o)
    rej_reason = rejection_reason(o, classification, audit_results)
    
    missing = []
    if person_conf in ("LOW", "UNKNOWN"):
        missing.append("Verified decision maker identity")
    if evidence_conf == "UNKNOWN":
        missing.append("Specific source URL with verifiable evidence")
    if contact_status == "UNKNOWN":
        missing.append("Contact information (email, LinkedIn)")
    if bu_status == "WEAK":
        missing.append("Clear service match evidence")
    
    next_research = []
    if person_conf in ("LOW", "UNKNOWN"):
        next_research.append("Verify person identity via LinkedIn/company website")
    if evidence_conf == "UNKNOWN":
        next_research.append("Find the actual post/comment with the requirement")
    if contact_status == "UNKNOWN":
        next_research.append("Find public email or LinkedIn profile")
    
    audited.append({
        "original_rank": o.get("rank", 0),
        "company": o.get("company_name", ""),
        "person": o.get("person_name", ""),
        "role": o.get("person_role", ""),
        "source_platform": o.get("source_platform", ""),
        "source_url": o.get("source_url", ""),
        "source_date": o.get("discovery_date", ""),
        "source_tier": "TIER_2" if o.get("source_platform") in ("reddit", "linkedin") else "TIER_3",
        "evidence_text": o.get("requirement_summary", ""),
        "evidence_confidence": evidence_conf,
        "requirement": o.get("requirement_summary", ""),
        "requirement_status": req_status,
        "requirement_recency": recency_status,
        "decision_maker": o.get("person_name", ""),
        "decision_maker_role": o.get("person_role", ""),
        "decision_maker_confidence": person_conf,
        "business_unit": o.get("bu_match", ""),
        "service_match": services,
        "outsourcing_intent": outsource_status,
        "competitor_or_service_provider": is_competitor,
        "cross_validated": o.get("cross_source_validation", {}).get("source_count", 0) > 1,
        "public_email": "",
        "email_status": "UNKNOWN",
        "linkedin_url": "",
        "salesability_score": score,
        "classification": classification,
        "why_this_lead": why,
        "trigger": trigger,
        "relevant_inowix_service": ", ".join(services) if services else "None identified",
        "possible_value": "",
        "missing_information": missing,
        "recommended_next_research": next_research,
        "rejection_reason": rej_reason,
        # Audit details
        "_audit": {
            "person": f"{person_score}/15 [{person_conf}] {person_note}",
            "requirement": f"{req_score}/30 [{req_status}] {req_note}",
            "evidence": f"{evidence_score}/5 [{evidence_conf}] {evidence_note}",
            "recency": f"{recency_score}/10 [{recency_status}] {recency_note}",
            "bu_fit": f"{bu_score}/20 [{bu_status}] {bu_note}",
            "outsourcing": f"{outsource_score}/10 [{outsource_status}] {outsource_note}",
            "competitor": f"[{competitor_status}] {competitor_note}",
            "contact": f"{contact_score}/5 [{contact_status}] {contact_note}",
        },
    })

# Sort by score
audited.sort(key=lambda x: x["salesability_score"], reverse=True)
for i, a in enumerate(audited, 1):
    a["final_rank"] = i

# ── STATS ────────────────────────────────────────────────────────────
hp = sum(1 for a in audited if a["classification"] == "HIGH_PRIORITY")
q = sum(1 for a in audited if a["classification"] == "QUALIFIED")
nr = sum(1 for a in audited if a["classification"] == "NEEDS_RESEARCH")
rej = sum(1 for a in audited if a["classification"] == "REJECT")
pp = sum(1 for a in audited if a["classification"] == "PARTNERSHIP_OPPORTUNITY")

comai_count = sum(1 for a in audited if a["business_unit"] == "COMAI" and a["classification"] != "REJECT")
saas_count = sum(1 for a in audited if a["business_unit"] == "SAAS_DEVELOPMENT" and a["classification"] != "REJECT")
custom_count = sum(1 for a in audited if a["business_unit"] == "CUSTOM_SOFTWARE" and a["classification"] != "REJECT")

explicit_out = sum(1 for a in audited if a["outsourcing_intent"] == "EXPLICIT_OUTSOURCING")
strong_ext = sum(1 for a in audited if a["outsourcing_intent"] == "STRONG_EXTERNAL_SIGNAL")
possible_ext = sum(1 for a in audited if a["outsourcing_intent"] == "POSSIBLE_EXTERNAL_NEED")
internal_only = sum(1 for a in audited if a["outsourcing_intent"] == "INTERNAL_HIRING_ONLY")
unknown_out = sum(1 for a in audited if a["outsourcing_intent"] == "UNKNOWN")

verified_dm = sum(1 for a in audited if a["decision_maker_confidence"] == "HIGH")
verified_email = sum(1 for a in audited if a["email_status"] == "VERIFIED")
linkedin_verified = sum(1 for a in audited if a.get("linkedin_url", ""))
cross_validated = sum(1 for a in audited if a["cross_validated"])

# ── SAVE JSON ────────────────────────────────────────────────────────
output = {
    "generated_at": datetime.now().isoformat(),
    "total_audited": len(audited),
    "stats": {
        "high_priority": hp,
        "qualified": q,
        "needs_research": nr,
        "reject": rej,
        "partnership_opportunity": pp,
        "comai_qualified": comai_count,
        "saas_qualified": saas_count,
        "custom_software_qualified": custom_count,
        "explicit_outsourcing": explicit_out,
        "strong_external_signal": strong_ext,
        "possible_external_need": possible_ext,
        "internal_hiring_only": internal_only,
        "outsourcing_unknown": unknown_out,
        "verified_decision_makers": verified_dm,
        "verified_emails": verified_email,
        "linkedin_verified": linkedin_verified,
        "cross_validated": cross_validated,
    },
    "opportunities": audited,
}

json_path = OUTPUT_DIR / "final_50_salesability_audit.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(f"Saved: {json_path}")

# ── SAVE XLSX ────────────────────────────────────────────────────────
try:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Salesability Audit"
    headers = [
        "Rank", "Company", "Person", "Role", "Source", "Source URL",
        "Requirement", "Evidence Confidence", "Requirement Status",
        "Recency", "Decision Maker", "DM Confidence", "Business Unit",
        "Outsourcing Intent", "Competitor", "Score", "Classification",
        "Why This Lead", "Rejection Reason", "Missing Info",
    ]
    ws.append(headers)
    for a in audited:
        ws.append([
            a["final_rank"], a["company"], a["person"], a["role"],
            a["source_platform"], a["source_url"], a["requirement"][:150],
            a["evidence_confidence"], a["requirement_status"],
            a["requirement_recency"], a["decision_maker"],
            a["decision_maker_confidence"], a["business_unit"],
            a["outsourcing_intent"], a["competitor_or_service_provider"],
            a["salesability_score"], a["classification"],
            a["why_this_lead"][:200], a["rejection_reason"],
            "; ".join(a["missing_information"]),
        ])
    xlsx_path = OUTPUT_DIR / "final_50_salesability_audit.xlsx"
    wb.save(xlsx_path)
    print(f"Saved: {xlsx_path}")
except ImportError:
    print("Skipping XLSX")

# ── SAVE REPORT ──────────────────────────────────────────────────────
lines = []
lines.append("=" * 80)
lines.append("BEACON CTO — FINAL 50-LEAD SALESABILITY AUDIT REPORT")
lines.append("=" * 80)
lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"Total Audited: {len(audited)}")
lines.append("")
lines.append("=" * 80)
lines.append("EXECUTIVE SUMMARY")
lines.append("=" * 80)
lines.append(f"  HIGH_PRIORITY:              {hp}")
lines.append(f"  QUALIFIED:                  {q}")
lines.append(f"  NEEDS_RESEARCH:             {nr}")
lines.append(f"  REJECT:                     {rej}")
lines.append(f"  PARTNERSHIP_OPPORTUNITY:    {pp}")
lines.append("")
lines.append("  BY BUSINESS UNIT (qualified only):")
lines.append(f"    COMAI:                    {comai_count}")
lines.append(f"    SAAS_DEVELOPMENT:         {saas_count}")
lines.append(f"    CUSTOM_SOFTWARE:          {custom_count}")
lines.append("")
lines.append("  OUTSOURCING INTENT:")
lines.append(f"    EXPLICIT_OUTSOURCING:     {explicit_out}")
lines.append(f"    STRONG_EXTERNAL_SIGNAL:   {strong_ext}")
lines.append(f"    POSSIBLE_EXTERNAL_NEED:   {possible_ext}")
lines.append(f"    INTERNAL_HIRING_ONLY:     {internal_only}")
lines.append(f"    UNKNOWN:                  {unknown_out}")
lines.append("")
lines.append("  VERIFICATION:")
lines.append(f"    Verified Decision Makers: {verified_dm}")
lines.append(f"    Verified Emails:          {verified_email}")
lines.append(f"    LinkedIn Verified:        {linkedin_verified}")
lines.append(f"    Cross-Validated:          {cross_validated}")

# Top 20 "Would I Actually Call These?"
lines.append("")
lines.append("=" * 80)
lines.append("WOULD I ACTUALLY CALL THESE? — TOP 20")
lines.append("=" * 80)
lines.append(f"{'Rank':<5} {'Person':<25} {'Company':<20} {'BU':<15} {'Score':<6} {'Class':<15} {'Source':<10}")
lines.append("-" * 96)
for a in audited[:20]:
    lines.append(f"{a['final_rank']:<5} {a['person'][:24]:<25} {a['company'][:19]:<20} {a['business_unit']:<15} {a['salesability_score']:<6} {a['classification']:<15} {a['source_platform']:<10}")

# Top 10 Call-First Leads
lines.append("")
lines.append("=" * 80)
lines.append("TOP 10 CALL-FIRST LEADS")
lines.append("=" * 80)
for a in audited[:10]:
    lines.append(f"")
    lines.append(f"  #{a['final_rank']} — {a['company']} ({a['salesability_score']}/100)")
    lines.append(f"  Person: {a['person']} ({a['role']})")
    lines.append(f"  BU: {a['business_unit']}")
    lines.append(f"  Requirement: {a['requirement'][:150]}")
    lines.append(f"  Source: {a['source_platform']} — {a['source_url']}")
    lines.append(f"  Why: {a['why_this_lead'][:200]}")
    lines.append(f"  Outsourcing: {a['outsourcing_intent']}")
    lines.append(f"  Services: {a['relevant_inowix_service']}")

# Rejection Analysis
lines.append("")
lines.append("=" * 80)
lines.append("FAILURE ANALYSIS — REJECTED LEADS")
lines.append("=" * 80)
rejected = [a for a in audited if a["classification"] == "REJECT"]
for a in rejected:
    lines.append(f"  #{a['final_rank']} {a['company']}: {a['rejection_reason']}")

report_path = OUTPUT_DIR / "final_50_salesability_audit_report.txt"
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Saved: {report_path}")

# ── PRINT SUMMARY ────────────────────────────────────────────────────
print("")
print("=" * 60)
print("AUDIT COMPLETE")
print("=" * 60)
print(f"  HIGH_PRIORITY:     {hp}")
print(f"  QUALIFIED:         {q}")
print(f"  NEEDS_RESEARCH:    {nr}")
print(f"  REJECT:            {rej}")
print(f"  PARTNERSHIP:       {pp}")
print(f"  Verified DMs:      {verified_dm}")
print(f"  Verified Emails:   {verified_email}")
print("=" * 60)
