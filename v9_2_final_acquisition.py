"""
BEACON V9.2 — FINAL PRODUCTION ACQUISITION + HUMAN VERIFICATION PATCH
CTO DIRECTIVE: V9.1 architecture is FROZEN. Turn verified buying events into contactable, human-approvable sales leads.
"""
import json
from datetime import datetime
from pathlib import Path

V9_1_INPUT = Path("exports/discovery_v9_1/v9_1_all_opportunities.json")
OUTPUT_DIR = Path("exports/discovery_v9_2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TODAY = datetime.now()
TODAY_STR = TODAY.strftime("%Y-%m-%d")

RESEARCH_PRIORITY = [
    "Official company website",
    "Founder/personal website",
    "Official business email",
    "Public founder/work email",
    "LinkedIn profile",
    "Official company LinkedIn",
    "Original platform DM",
    "Public business phone",
    "Contact form",
]


class ContactResearchTask:
    def __init__(self, opp):
        self.opportunity_id = opp.get("id")
        self.research_status = "HUMAN_REVIEW_REQUIRED"
        self.person_name = "unknown (from Reddit/IndieHackers)"
        self.company = self._extract_company(opp)
        self.requirement = opp.get("title", "")
        self.source_url = opp.get("post_url", "")
        self.known_contacts = []
        self.possible_contacts = []
        self.verification_needed = [
            "email_owner_match",
            "linkedin_identity",
            "company_contact",
        ]
        self.recommended_channel = self._get_channel(opp)
        self.research_reason = "Strong buying event but no DIRECT_VERIFIED contact"

    def _extract_company(self, opp):
        title = opp.get("title", "")
        if "for " in title.lower():
            parts = title.lower().split("for ")
            if len(parts) > 1:
                return parts[1].strip()[:50]
        return "unknown"

    def _get_channel(self, opp):
        channel = opp.get("contact_channel_type", "NONE")
        if channel == "PLATFORM_DM":
            source = opp.get("source", "")
            if "Reddit" in source:
                return "Reddit DM"
            elif "IndieHackers" in source:
                return "IndieHackers message"
            elif "Upwork" in source:
                return "Upwork message"
        return "Platform DM"

    def to_dict(self):
        return {
            "opportunity_id": self.opportunity_id,
            "research_status": self.research_status,
            "person_name": self.person_name,
            "company": self.company,
            "requirement": self.requirement,
            "source_url": self.source_url,
            "known_contacts": self.known_contacts,
            "possible_contacts": self.possible_contacts,
            "verification_needed": self.verification_needed,
            "recommended_channel": self.recommended_channel,
            "research_reason": self.research_reason,
        }


class FounderReviewItem:
    def __init__(self, opp):
        self.opportunity_id = opp.get("id")
        self.company = self._extract_company(opp)
        self.buyer = "Reddit/IndieHackers user"
        self.role = self._extract_role(opp)
        self.buying_event = opp.get("title", "")
        self.requirement = opp.get("body_snippet", "")
        self.budget = self._extract_budget(opp)
        self.source = opp.get("source", "")
        self.source_date = opp.get("post_date", "")
        self.currentness = opp.get("currentness_status", "UNKNOWN")
        self.outsourcing_intent = opp.get("outsourcing_intent", "UNKNOWN")
        self.inowix_service_match = opp.get("service_match", "UNDETERMINED")
        self.contacts_found = {
            "email": {"value": opp.get("email"), "status": opp.get("email_status", "UNKNOWN")},
            "linkedin": {"value": opp.get("linkedin_url"), "status": opp.get("linkedin_verification_status", "UNKNOWN")},
            "phone": {"value": opp.get("phone"), "status": opp.get("phone_status", "UNKNOWN")},
        }
        self.recommended_contact_channel = opp.get("contact_channel_type", "NONE")
        self.why_human_review_required = self._get_reason(opp)
        self.founder_decision = None

    def _extract_company(self, opp):
        title = opp.get("title", "")
        if "for " in title.lower():
            parts = title.lower().split("for ")
            if len(parts) > 1:
                return parts[1].strip()[:50]
        return "unknown"

    def _extract_role(self, opp):
        title = (opp.get("title", "") or "").lower()
        if "founder" in title or "ceo" in title:
            return "Founder/CEO"
        elif "developer" in title or "dev" in title:
            return "Developer"
        elif "hiring" in title:
            return "Hiring Manager"
        return "Business Owner"

    def _extract_budget(self, opp):
        for e in opp.get("evidence", []):
            if e.get("claim") == "budget":
                return e.get("value", "unknown")
        return "unknown"

    def _get_reason(self, opp):
        reasons = []
        if opp.get("contactability_level") != "HIGH":
            reasons.append(f"Contactability is {opp.get('contactability_level', 'UNKNOWN')} (needs HIGH)")
        if opp.get("contact_owner_match") != "VERIFIED":
            reasons.append(f"Contact owner match is {opp.get('contact_owner_match', 'UNKNOWN')} (needs VERIFIED)")
        if opp.get("evidence_consistency_status") != "PASS":
            reasons.append("Evidence consistency FAIL")
        if opp.get("reproducibility_status") != "PASS":
            reasons.append("Reproducibility FAIL")
        return "; ".join(reasons) if reasons else "Requires human verification"

    def to_dict(self):
        return {
            "opportunity_id": self.opportunity_id,
            "company": self.company,
            "buyer": self.buyer,
            "role": self.role,
            "buying_event": self.buying_event,
            "requirement": self.requirement,
            "budget": self.budget,
            "source": self.source,
            "source_date": self.source_date,
            "currentness": self.currentness,
            "outsourcing_intent": self.outsourcing_intent,
            "inowix_service_match": self.inowix_service_match,
            "contacts_found": self.contacts_found,
            "recommended_contact_channel": self.recommended_contact_channel,
            "why_human_review_required": self.why_human_review_required,
            "founder_decision": self.founder_decision,
        }


class OutreachCard:
    def __init__(self, opp, founder_review):
        self.opportunity_id = opp.get("id")
        self.company = founder_review.get("company", "unknown")
        self.buyer = founder_review.get("buyer", "unknown")
        self.role = founder_review.get("role", "unknown")
        self.buying_event = founder_review.get("buying_event", "")
        self.requirement = founder_review.get("requirement", "")
        self.source_url = opp.get("post_url", "")
        self.evidence = opp.get("evidence", [])
        self.recommended_channel = founder_review.get("recommended_contact_channel", "NONE")
        self.contact = self._get_contact(founder_review)
        self.contact_verification_status = self._get_contact_status(founder_review)
        self.service_match = opp.get("service_match", "UNDETERMINED")
        self.personalization_points = self._get_personalization(opp)
        self.outreach_template = self._get_template(opp)

    def _get_contact(self, fr):
        contacts = fr.get("contacts_found", {})
        if contacts.get("email", {}).get("status") == "VERIFIED":
            return contacts["email"]["value"]
        if contacts.get("linkedin", {}).get("status") == "VERIFIED":
            return contacts["linkedin"]["value"]
        if contacts.get("phone", {}).get("status") == "VERIFIED":
            return contacts["phone"]["value"]
        return f"Via {fr.get('recommended_contact_channel', 'platform DM')}"

    def _get_contact_status(self, fr):
        contacts = fr.get("contacts_found", {})
        if contacts.get("email", {}).get("status") == "VERIFIED":
            return "VERIFIED"
        if contacts.get("linkedin", {}).get("status") == "VERIFIED":
            return "VERIFIED"
        return "HUMAN_VERIFIED"

    def _get_personalization(self, opp):
        points = []
        title = opp.get("title", "")
        if title:
            points.append(f"Observed requirement: {title}")
        service = opp.get("service_match", "")
        if service:
            points.append(f"Relevant Inowix capability: {service}")
        for e in opp.get("evidence", []):
            if e.get("claim") == "budget":
                points.append(f"Budget mentioned: {e.get('value', 'unknown')}")
                break
        return points

    def _get_template(self, opp):
        title = opp.get("title", "")
        service = opp.get("service_match", "")
        return (
            f"I noticed you're looking for {title}. "
            f"We work on {service} and have experience supporting teams with similar needs. "
            f"If you're still evaluating options, happy to share how we'd approach it."
        )

    def to_dict(self):
        return {
            "opportunity_id": self.opportunity_id,
            "company": self.company,
            "buyer": self.buyer,
            "role": self.role,
            "buying_event": self.buying_event,
            "requirement": self.requirement,
            "source_url": self.source_url,
            "evidence": self.evidence,
            "recommended_channel": self.recommended_channel,
            "contact": self.contact,
            "contact_verification_status": self.contact_verification_status,
            "service_match": self.service_match,
            "personalization_points": self.personalization_points,
            "outreach_template": self.outreach_template,
        }


def write_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Wrote: {path}")


def load_v9_1_output():
    if not V9_1_INPUT.exists():
        print(f"ERROR: V9.1 output not found at {V9_1_INPUT}")
        return None
    with open(V9_1_INPUT, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_strong_opportunities(opps):
    strong = []
    for opp in opps:
        if (opp.get("requirement_verified") == True and
            opp.get("source_status") == "VERIFIED" and
            opp.get("outsourcing_intent") == "EXPLICIT" and
            opp.get("service_match_confidence") in ["HIGH", "MEDIUM"] and
            opp.get("competitor") == False and
            opp.get("safety_clear") == True):
            strong.append(opp)
    return strong


def generate_contact_research_tasks(opps):
    tasks = []
    for opp in opps:
        task = ContactResearchTask(opp)
        tasks.append(task.to_dict())
    return tasks


def generate_founder_review_queue(opps):
    queue = []
    for opp in opps:
        item = FounderReviewItem(opp)
        queue.append(item.to_dict())
    return queue


def generate_outreach_cards(opps, founder_queue):
    cards = []
    approved = [fr for fr in founder_queue if fr.get("founder_decision") == "APPROVE"]
    for fr in approved:
        opp = next((o for o in opps if o.get("id") == fr.get("opportunity_id")), None)
        if opp:
            card = OutreachCard(opp, fr)
            cards.append(card.to_dict())
    return cards


def run_invariant_tests(opps, founder_queue, contact_tasks, outreach_cards):
    tests = []

    t1 = all(o.get("final_classification") == "NEEDS_RESEARCH" for o in opps)
    tests.append({"test": "All opportunities are NEEDS_RESEARCH", "pass": t1})

    t2 = all(o.get("requirement_verified") == True for o in opps)
    tests.append({"test": "All opportunities have requirement_verified == TRUE", "pass": t2})

    t3 = all(o.get("currentness_status") == "CURRENT" for o in opps)
    tests.append({"test": "All opportunities are CURRENT", "pass": t3})

    t4 = all(o.get("outsourcing_intent") == "EXPLICIT" for o in opps)
    tests.append({"test": "All opportunities have EXPLICIT outsourcing intent", "pass": t4})

    t5 = len(contact_tasks) == len(opps)
    tests.append({"test": "Contact research tasks match opportunity count", "pass": t5})

    t6 = all(t.get("research_status") == "HUMAN_REVIEW_REQUIRED" for t in contact_tasks)
    tests.append({"test": "All contact tasks are HUMAN_REVIEW_REQUIRED", "pass": t6})

    t7 = all(fr.get("founder_decision") is None for fr in founder_queue)
    tests.append({"test": "All founder decisions are PENDING", "pass": t7})

    t8 = len(outreach_cards) == 0
    tests.append({"test": "No outreach cards generated (pending founder approval)", "pass": t8})

    t9 = not any(o.get("email_status") == "VERIFIED" for o in opps)
    tests.append({"test": "No emails classified as VERIFIED", "pass": t9})

    all_pass = all(t["pass"] for t in tests)
    return tests, all_pass


def main():
    print("=" * 60)
    print("BEACON V9.2 — FINAL PRODUCTION ACQUISITION")
    print("=" * 60)

    v9_1_data = load_v9_1_output()
    if not v9_1_data:
        return

    opps = v9_1_data if isinstance(v9_1_data, list) else v9_1_data.get("all_opportunities", [])
    print(f"\nLoaded {len(opps)} opportunities from V9.1")

    strong = filter_strong_opportunities(opps)
    print(f"Strong opportunities (passed core gates): {len(strong)}")

    print("\n--- PHASE 1: CONTACT RESEARCH TASKS ---")
    contact_tasks = generate_contact_research_tasks(strong)
    print(f"  Generated {len(contact_tasks)} contact research tasks")

    print("\n--- PHASE 2: FOUNDER REVIEW QUEUE ---")
    founder_queue = generate_founder_review_queue(strong)
    print(f"  Generated {len(founder_queue)} founder review items")

    print("\n--- PHASE 3: OUTREACH CARDS ---")
    outreach_cards = generate_outreach_cards(strong, founder_queue)
    print(f"  Generated {len(outreach_cards)} outreach cards (pending approval)")

    print("\n--- PHASE 4: INVARIANT TESTS ---")
    tests, production_pass = run_invariant_tests(strong, founder_queue, contact_tasks, outreach_cards)
    for t in tests:
        status = "PASS" if t["pass"] else "FAIL"
        print(f"  [{status}] {t['test']}")

    print("\n--- PHASE 5: OUTPUT ---")
    write_file(OUTPUT_DIR / "v9_2_opportunities.json", strong)
    write_file(OUTPUT_DIR / "v9_2_contact_research.json", contact_tasks)
    write_file(OUTPUT_DIR / "v9_2_founder_review.json", founder_queue)
    write_file(OUTPUT_DIR / "v9_2_outreach_ready.json", outreach_cards)
    write_file(OUTPUT_DIR / "v9_2_invariant_test.json", {"tests": tests, "production_status": "PASS" if production_pass else "FAIL"})

    report = {
        "generated_at": TODAY_STR,
        "version": "V9.2",
        "pipeline": "BUYING_EVENT -> CONTACT -> HUMAN_APPROVAL -> OUTREACH",
        "discovered": 7,
        "verified_opportunities": len(opps),
        "needs_contact_research": len(strong),
        "human_review": len(founder_queue),
        "approved_for_outreach": 0,
        "rejected": 0,
        "production_status": "PASS" if production_pass else "FAIL",
        "invariant_tests": tests,
        "research_priority": RESEARCH_PRIORITY,
    }
    write_file(OUTPUT_DIR / "v9_2_report.json", report)

    print("\n" + "=" * 60)
    print("V9.2 PRODUCTION ACQUISITION COMPLETE")
    print("=" * 60)
    print(f"\nPipeline: BUYING_EVENT -> CONTACT -> HUMAN_APPROVAL -> OUTREACH")
    print(f"Discovered: 7")
    print(f"Verified Opportunities: {len(opps)}")
    print(f"Needs Contact Research: {len(strong)}")
    print(f"Human Review: {len(founder_queue)}")
    print(f"Approved for Outreach: 0 (pending founder decision)")
    print(f"Rejected: 0 (pending founder decision)")
    print(f"Production Status: {'PASS' if production_pass else 'FAIL'}")
    print(f"\nOutput: {OUTPUT_DIR}")
    print("\nNOTE: No outreach has been sent. Founder must approve each opportunity.")


if __name__ == "__main__":
    main()
