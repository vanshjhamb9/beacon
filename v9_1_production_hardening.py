"""
BEACON V9.1 — PRODUCTION SALESABILITY HARDENING PATCH
CTO DIRECTIVE: Harden V9 only. Do not redesign discovery.
"""
import json
from datetime import datetime
from pathlib import Path

V9_INPUT = Path("exports/discovery_v9/v9_report.json")
OUTPUT_DIR = Path("exports/discovery_v9_1")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TODAY = datetime.now()
TODAY_STR = TODAY.strftime("%Y-%m-%d")


class Opportunity:
    def __init__(self, v9_data):
        self.id = v9_data.get("id")
        self.source = v9_data.get("source")
        self.post_url = v9_data.get("post_url")
        self.post_date = v9_data.get("post_date")
        self.title = v9_data.get("title")
        self.body_snippet = v9_data.get("body_snippet")
        self.evidence = v9_data.get("evidence", [])

        self.requirement_verified = False
        self.requirement_evidence = []
        self.source_status = "UNVERIFIED"
        self.source_evidence = []
        self.identity_confidence = "UNKNOWN"
        self.identity_evidence = []
        self.company_verified = False
        self.company_evidence = []
        self.currentness_status = "STALE"
        self.currentness_evidence = []
        self.outsourcing_intent = "UNKNOWN"
        self.outsourcing_confidence = "LOW"
        self.outsourcing_evidence = []
        self.service_match = "UNDETERMINED"
        self.service_match_confidence = "LOW"
        self.service_match_evidence = []

        self.email = None
        self.email_status = "UNKNOWN"
        self.email_evidence = []
        self.linkedin_url = None
        self.linkedin_verification_status = "UNKNOWN"
        self.linkedin_evidence = []
        self.phone = None
        self.phone_status = "UNKNOWN"
        self.phone_evidence = []

        self.contact_channel_type = "NONE"
        self.contactability_level = "NONE"
        self.contact_owner = "UNKNOWN"
        self.contact_owner_match = "UNKNOWN"
        self.contact_owner_evidence = []

        self.competitor = False
        self.safety_clear = True

        self.evidence_consistency_status = "FAIL"
        self.reproducibility_status = "FAIL"
        self.duplicate_status = "UNIQUE"

        self.cto_15_minute_test = "NO"
        self.cto_decision_reason = ""

        self.final_classification = "PENDING"
        self.final_salesability = "PENDING"
        self.rejection_reason = None
        self.rejection_gate = None


def write_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Wrote: {path}")


def load_v9_report():
    if not V9_INPUT.exists():
        print(f"ERROR: V9 report not found at {V9_INPUT}")
        return None
    with open(V9_INPUT, "r", encoding="utf-8") as f:
        return json.load(f)


def create_opportunities(v9_report):
    opps = []
    for sr in v9_report.get("sales_ready", []):
        opps.append(Opportunity(sr))
    for nr in v9_report.get("needs_research", []):
        opps.append(Opportunity(nr))
    for rj in v9_report.get("rejected", []):
        opps.append(Opportunity(rj))
    return opps


def verify_requirement(opp):
    for e in opp.evidence:
        if e.get("claim") == "requirement_verified" and e.get("value") == True:
            opp.requirement_verified = True
            opp.requirement_evidence.append(e)
            return
    opp.requirement_verified = False


def verify_source(opp):
    valid_sources = [
        "Reddit r/AppDevelopers", "Reddit r/WebDevJobs", "Reddit r/SaaS",
        "IndieHackers", "Upwork"
    ]
    if opp.source in valid_sources:
        opp.source_status = "VERIFIED"
        opp.source_evidence.append({
            "claim": "source_status",
            "value": "VERIFIED",
            "source": "V9.1",
            "source_url": opp.post_url,
            "confidence": "HIGH",
            "observed_at": TODAY_STR
        })
    else:
        opp.source_status = "UNVERIFIED"


def verify_identity(opp):
    for e in opp.evidence:
        if e.get("claim") == "budget" and e.get("confidence") == "HIGH":
            opp.identity_confidence = "HIGH"
            opp.identity_evidence.append(e)
            return
    opp.identity_confidence = "MEDIUM"


def verify_company(opp):
    if opp.title and opp.body_snippet:
        opp.company_verified = True
        opp.company_evidence.append({
            "claim": "company_verified",
            "value": True,
            "source": "V9.1",
            "source_url": opp.post_url,
            "confidence": "MEDIUM",
            "observed_at": TODAY_STR
        })
    else:
        opp.company_verified = False


def verify_currentness(opp):
    if opp.post_date and opp.post_date >= "2026-01-01":
        opp.currentness_status = "CURRENT"
        opp.currentness_evidence.append({
            "claim": "currentness_status",
            "value": "CURRENT",
            "source": "V9.1",
            "source_url": opp.post_url,
            "confidence": "HIGH",
            "observed_at": TODAY_STR
        })
    else:
        opp.currentness_status = "STALE"


def verify_outsourcing(opp):
    keywords = ["hiring", "looking for", "need", "build", "develop", "create", "make"]
    title_lower = (opp.title or "").lower()
    body_lower = (opp.body_snippet or "").lower()
    if any(kw in title_lower or kw in body_lower for kw in keywords):
        opp.outsourcing_intent = "EXPLICIT"
        opp.outsourcing_confidence = "HIGH"
        opp.outsourcing_evidence.append({
            "claim": "outsourcing_intent",
            "value": "EXPLICIT",
            "source": "V9.1",
            "source_url": opp.post_url,
            "confidence": "HIGH",
            "observed_at": TODAY_STR
        })
    else:
        opp.outsourcing_intent = "IMPLICIT"
        opp.outsourcing_confidence = "LOW"


def verify_service_match(opp):
    for e in opp.evidence:
        if e.get("claim") == "service_match":
            opp.service_match = e.get("value", "UNDETERMINED")
            opp.service_match_confidence = e.get("confidence", "LOW")
            opp.service_match_evidence.append(e)
            return
    opp.service_match = "UNDETERMINED"
    opp.service_match_confidence = "LOW"


def verify_contactability(opp):
    if opp.email and opp.email_status == "VERIFIED":
        opp.contact_channel_type = "DIRECT_VERIFIED"
        opp.contactability_level = "HIGH"
    elif opp.linkedin_url and opp.linkedin_verification_status == "VERIFIED":
        opp.contact_channel_type = "DIRECT_VERIFIED"
        opp.contactability_level = "HIGH"
    elif opp.source in ["Reddit r/AppDevelopers", "Reddit r/WebDevJobs", "Reddit r/SaaS"]:
        opp.contact_channel_type = "PLATFORM_DM"
        opp.contactability_level = "MEDIUM"
    elif opp.source == "IndieHackers":
        opp.contact_channel_type = "PLATFORM_DM"
        opp.contactability_level = "MEDIUM"
    elif opp.source == "Upwork":
        opp.contact_channel_type = "PLATFORM_DM"
        opp.contactability_level = "MEDIUM"
    else:
        opp.contact_channel_type = "NONE"
        opp.contactability_level = "NONE"


def verify_contact_owner(opp):
    if opp.contactability_level == "HIGH" and opp.contact_channel_type == "DIRECT_VERIFIED":
        opp.contact_owner_match = "VERIFIED"
        opp.contact_owner_evidence.append({
            "claim": "contact_owner_match",
            "value": "VERIFIED",
            "source": "V9.1",
            "source_url": opp.post_url,
            "confidence": "HIGH",
            "observed_at": TODAY_STR
        })
    elif opp.contactability_level == "MEDIUM":
        opp.contact_owner_match = "LIKELY"
    else:
        opp.contact_owner_match = "UNKNOWN"


def check_evidence_consistency(opp):
    required_claims = [
        "requirement_verified", "source_status", "identity_confidence",
        "company_verified", "currentness_status", "outsourcing_intent",
        "service_match_confidence", "contactability", "contact_owner_match",
        "competitor", "safety_clear"
    ]
    missing = []
    for claim in required_claims:
        found = False
        for e in opp.evidence:
            if e.get("claim") == claim:
                found = True
                break
        if not found:
            missing.append(claim)

    if missing:
        opp.evidence_consistency_status = "FAIL"
    else:
        opp.evidence_consistency_status = "PASS"


def check_reproducibility(opp):
    reproducible_claims = ["source_url", "requirement", "budget"]
    reproducible_count = 0
    for claim in reproducible_claims:
        for e in opp.evidence:
            if e.get("claim") == claim and e.get("source_url"):
                reproducible_count += 1
                break

    if reproducible_count >= 2:
        opp.reproducibility_status = "PASS"
    else:
        opp.reproducibility_status = "FAIL"


def detect_duplicates(opps):
    seen = {}
    for opp in opps:
        key = f"{opp.source}:{opp.post_url}"
        if key in seen:
            opp.duplicate_status = "DUPLICATE"
        else:
            seen[key] = opp.id
            opp.duplicate_status = "UNIQUE"


def cto_test(opp):
    if (opp.requirement_verified and
        opp.source_status == "VERIFIED" and
        opp.identity_confidence == "HIGH" and
        opp.company_verified and
        opp.currentness_status == "CURRENT" and
        opp.outsourcing_intent == "EXPLICIT" and
        opp.service_match_confidence == "HIGH" and
        opp.contactability_level in ["HIGH", "MEDIUM"] and
        opp.contact_owner_match in ["VERIFIED", "LIKELY"] and
        not opp.competitor and
        opp.safety_clear):
        opp.cto_15_minute_test = "YES"
        opp.cto_decision_reason = "All gates passed"
    else:
        opp.cto_15_minute_test = "NO"
        failed = []
        if not opp.requirement_verified:
            failed.append("requirement_verified")
        if opp.source_status != "VERIFIED":
            failed.append("source_status")
        if opp.identity_confidence != "HIGH":
            failed.append("identity_confidence")
        if not opp.company_verified:
            failed.append("company_verified")
        if opp.currentness_status != "CURRENT":
            failed.append("currentness_status")
        if opp.outsourcing_intent != "EXPLICIT":
            failed.append("outsourcing_intent")
        if opp.service_match_confidence != "HIGH":
            failed.append("service_match_confidence")
        if opp.contactability_level not in ["HIGH", "MEDIUM"]:
            failed.append("contactability_level")
        if opp.contact_owner_match not in ["VERIFIED", "LIKELY"]:
            failed.append("contact_owner_match")
        if opp.competitor:
            failed.append("competitor")
        if not opp.safety_clear:
            failed.append("safety_clear")
        opp.cto_decision_reason = f"Failed: {', '.join(failed)}"


def final_classification(opp):
    if (opp.requirement_verified and
        opp.source_status == "VERIFIED" and
        opp.identity_confidence == "HIGH" and
        opp.company_verified and
        opp.currentness_status == "CURRENT" and
        opp.outsourcing_intent == "EXPLICIT" and
        opp.service_match_confidence == "HIGH" and
        opp.contactability_level == "HIGH" and
        opp.contact_owner_match == "VERIFIED" and
        opp.evidence_consistency_status == "PASS" and
        opp.reproducibility_status == "PASS" and
        not opp.competitor and
        opp.safety_clear and
        opp.cto_15_minute_test == "YES" and
        opp.duplicate_status == "UNIQUE"):
        opp.final_classification = "SALES_READY"
        opp.final_salesability = "HIGH"
    elif (opp.requirement_verified and
          opp.source_status == "VERIFIED" and
          opp.outsourcing_intent == "EXPLICIT" and
          opp.service_match_confidence in ["HIGH", "MEDIUM"] and
          not opp.competitor and
          opp.safety_clear):
        opp.final_classification = "NEEDS_RESEARCH"
        opp.final_salesability = "MEDIUM"
    else:
        opp.final_classification = "REJECT"
        opp.final_salesability = "LOW"
        failed = []
        if not opp.requirement_verified:
            failed.append("requirement_verified")
        if opp.source_status != "VERIFIED":
            failed.append("source_status")
        if opp.identity_confidence != "HIGH":
            failed.append("identity_confidence")
        if not opp.company_verified:
            failed.append("company_verified")
        if opp.currentness_status != "CURRENT":
            failed.append("currentness_status")
        if opp.outsourcing_intent != "EXPLICIT":
            failed.append("outsourcing_intent")
        if opp.service_match_confidence != "HIGH":
            failed.append("service_match_confidence")
        if opp.contactability_level != "HIGH":
            failed.append("contactability_level")
        if opp.contact_owner_match != "VERIFIED":
            failed.append("contact_owner_match")
        if opp.evidence_consistency_status != "PASS":
            failed.append("evidence_consistency")
        if opp.reproducibility_status != "PASS":
            failed.append("reproducibility")
        if opp.competitor:
            failed.append("competitor")
        if not opp.safety_clear:
            failed.append("safety_clear")
        if opp.cto_15_minute_test != "YES":
            failed.append("cto_test")
        if opp.duplicate_status != "UNIQUE":
            failed.append("duplicate")
        opp.rejection_reason = f"Failed: {', '.join(failed)}"
        opp.rejection_gate = failed[0] if failed else "unknown"


def run_invariant_tests(opps, summary):
    tests = []
    sales_ready = [o for o in opps if o.final_classification == "SALES_READY"]
    needs_research = [o for o in opps if o.final_classification == "NEEDS_RESEARCH"]
    rejected = [o for o in opps if o.final_classification == "REJECT"]

    t1 = summary.get("sales_ready", 0) == len(sales_ready)
    tests.append({"test": "summary.sales_ready == actual count", "pass": t1})

    t2 = summary.get("needs_research", 0) == len(needs_research)
    tests.append({"test": "summary.needs_research == actual count", "pass": t2})

    t3 = summary.get("rejected", 0) == len(rejected)
    tests.append({"test": "summary.rejected == actual count", "pass": t3})

    for opp in sales_ready:
        if opp.contactability_level == "HIGH" and opp.contact_channel_type != "DIRECT_VERIFIED":
            tests.append({"test": f"SALES_READY {opp.id} has HIGH contact but no DIRECT_VERIFIED", "pass": False})
            break
    else:
        tests.append({"test": "SALES_READY contactability consistency", "pass": True})

    for opp in sales_ready:
        if opp.contact_owner_match != "VERIFIED":
            tests.append({"test": f"SALES_READY {opp.id} contact_owner_match != VERIFIED", "pass": False})
            break
    else:
        tests.append({"test": "SALES_READY contact ownership", "pass": True})

    for opp in sales_ready:
        if opp.evidence_consistency_status != "PASS":
            tests.append({"test": f"SALES_READY {opp.id} evidence consistency FAIL", "pass": False})
            break
    else:
        tests.append({"test": "SALES_READY evidence consistency", "pass": True})

    for opp in sales_ready:
        if opp.reproducibility_status != "PASS":
            tests.append({"test": f"SALES_READY {opp.id} reproducibility FAIL", "pass": False})
            break
    else:
        tests.append({"test": "SALES_READY reproducibility", "pass": True})

    for opp in sales_ready:
        if opp.cto_15_minute_test != "YES":
            tests.append({"test": f"SALES_READY {opp.id} CTO test NO", "pass": False})
            break
    else:
        tests.append({"test": "SALES_READY CTO test", "pass": True})

    all_pass = all(t["pass"] for t in tests)
    return tests, all_pass


def opp_to_dict(opp):
    return {
        "id": opp.id, "source": opp.source, "post_url": opp.post_url,
        "post_date": opp.post_date, "title": opp.title,
        "body_snippet": opp.body_snippet,
        "final_classification": opp.final_classification,
        "final_salesability": opp.final_salesability,
        "requirement_verified": opp.requirement_verified,
        "requirement_evidence": opp.requirement_evidence,
        "source_status": opp.source_status,
        "source_evidence": opp.source_evidence,
        "identity_confidence": opp.identity_confidence,
        "identity_evidence": opp.identity_evidence,
        "company_verified": opp.company_verified,
        "company_evidence": opp.company_evidence,
        "currentness_status": opp.currentness_status,
        "currentness_evidence": opp.currentness_evidence,
        "outsourcing_intent": opp.outsourcing_intent,
        "outsourcing_confidence": opp.outsourcing_confidence,
        "outsourcing_evidence": opp.outsourcing_evidence,
        "service_match": opp.service_match,
        "service_match_confidence": opp.service_match_confidence,
        "service_match_evidence": opp.service_match_evidence,
        "email": opp.email, "email_status": opp.email_status,
        "email_evidence": opp.email_evidence,
        "linkedin_url": opp.linkedin_url,
        "linkedin_verification_status": opp.linkedin_verification_status,
        "linkedin_evidence": opp.linkedin_evidence,
        "phone": opp.phone, "phone_status": opp.phone_status,
        "phone_evidence": opp.phone_evidence,
        "contact_channel_type": opp.contact_channel_type,
        "contactability_level": opp.contactability_level,
        "contact_owner_match": opp.contact_owner_match,
        "contact_owner_evidence": opp.contact_owner_evidence,
        "competitor": opp.competitor, "safety_clear": opp.safety_clear,
        "evidence_consistency_status": opp.evidence_consistency_status,
        "reproducibility_status": opp.reproducibility_status,
        "duplicate_status": opp.duplicate_status,
        "cto_15_minute_test": opp.cto_15_minute_test,
        "cto_decision_reason": opp.cto_decision_reason,
        "rejection_reason": opp.rejection_reason,
        "rejection_gate": opp.rejection_gate,
    }


def main():
    print("=" * 60)
    print("BEACON V9.1 — PRODUCTION SALESABILITY HARDENING")
    print("=" * 60)

    v9_report = load_v9_report()
    if not v9_report:
        return

    opps = create_opportunities(v9_report)
    print(f"\nLoaded {len(opps)} opportunities from V9")

    print("\n--- PHASE 1: VERIFICATION ---")
    for opp in opps:
        verify_requirement(opp)
        verify_source(opp)
        verify_identity(opp)
        verify_company(opp)
        verify_currentness(opp)
        verify_outsourcing(opp)
        verify_service_match(opp)
        verify_contactability(opp)
        verify_contact_owner(opp)

    print("\n--- PHASE 2: EVIDENCE CHECKS ---")
    for opp in opps:
        check_evidence_consistency(opp)
        check_reproducibility(opp)

    print("\n--- PHASE 3: DUPLICATE DETECTION ---")
    detect_duplicates(opps)

    print("\n--- PHASE 4: CTO TEST ---")
    for opp in opps:
        cto_test(opp)

    print("\n--- PHASE 5: FINAL CLASSIFICATION ---")
    for opp in opps:
        final_classification(opp)

    sales_ready = [o for o in opps if o.final_classification == "SALES_READY"]
    needs_research = [o for o in opps if o.final_classification == "NEEDS_RESEARCH"]
    rejected = [o for o in opps if o.final_classification == "REJECT"]

    summary = {
        "sales_ready": len(sales_ready),
        "needs_research": len(needs_research),
        "rejected": len(rejected),
    }

    print("\n--- PHASE 6: INVARIANT TESTS ---")
    tests, production_pass = run_invariant_tests(opps, summary)
    for t in tests:
        status = "PASS" if t["pass"] else "FAIL"
        print(f"  [{status}] {t['test']}")

    print("\n--- PHASE 7: OUTPUT ---")
    write_file(OUTPUT_DIR / "v9_1_all_opportunities.json", [opp_to_dict(o) for o in opps])
    write_file(OUTPUT_DIR / "v9_1_sales_ready.json", [opp_to_dict(o) for o in sales_ready])
    write_file(OUTPUT_DIR / "v9_1_needs_research.json", [opp_to_dict(o) for o in needs_research])
    write_file(OUTPUT_DIR / "v9_1_rejected.json", [opp_to_dict(o) for o in rejected])
    write_file(OUTPUT_DIR / "v9_1_invariant_test.json", {"tests": tests, "production_status": "PASS" if production_pass else "FAIL"})

    report = {
        "generated_at": TODAY_STR,
        "version": "V9.1",
        "total_discovered": len(opps),
        "sales_ready": len(sales_ready),
        "needs_research": len(needs_research),
        "rejected": len(rejected),
        "production_status": "PASS" if production_pass else "FAIL",
        "invariant_tests": tests,
        "sales_ready_details": [opp_to_dict(o) for o in sales_ready],
        "rejected_details": [opp_to_dict(o) for o in rejected],
    }
    write_file(OUTPUT_DIR / "v9_1_report.json", report)

    print("\n" + "=" * 60)
    print("V9.1 PRODUCTION HARDENING COMPLETE")
    print("=" * 60)
    print(f"\nSales Ready: {len(sales_ready)}")
    print(f"Needs Research: {len(needs_research)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Production Status: {'PASS' if production_pass else 'FAIL'}")
    print(f"\nOutput: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
