"""Post-enrichment QA: drop unverifiable / mismatched domains and rewrite exports."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "exports" / "vansh_list_enriched.json"
CSV_PATH = ROOT / "exports" / "vansh_list_enriched.csv"
SUMMARY_PATH = ROOT / "exports" / "vansh_list_enriched_summary.json"

STOP = {
    "the", "and", "of", "a", "an", "pvt", "ltd", "llc", "inc", "co",
    "private", "limited", "solutions", "solution", "media", "digital",
    "marketing", "agency", "studio", "studios", "group", "services",
    "service", "company", "technologies", "technology", "tech",
}

# Domains that must never be treated as niche agency sites
BLOCKLIST = {
    "mega.io", "google.com", "microsoft.com", "facebook.com", "linkedin.com",
    "instagram.com", "youtube.com", "amazon.com", "apple.com", "wikipedia.org",
    "canva.com", "wix.com", "shopify.com", "godaddy.com", "blogspot.com",
    "wordpress.com", "medium.com", "twitter.com", "x.com",
}

CSV_FIELDS = [
    "founder_name", "company_name", "location", "job_title", "industry",
    "company_size", "enrichment_status", "domain", "website", "pages_scraped",
    "founder_email", "general_email", "support_email", "business_phone",
    "emails", "phones", "linkedin_person_url", "linkedin_company_url",
    "linkedin_urls", "decision_makers", "errors",
]


def tokens(name: str) -> list[str]:
    raw = re.sub(r"[^a-zA-Z0-9\s]", " ", name.lower())
    return [t for t in raw.split() if len(t) >= 2 and t not in STOP][:5]


COMMON_FALSE_SLUGS = {
    "bot", "point", "aura", "reset", "twist", "trek", "brave", "odd", "ginger",
    "leaf", "nest", "care", "fire", "vision", "corner", "weave", "pixel", "plus",
    "gen", "tea", "rose", "empire", "social", "digital", "media", "brand", "ads",
    "walas", "lowkey", "mega", "apple", "google", "meta", "amazon", "oracle",
    "cisco", "adobe", "salesforce", "hubspot", "shopify", "canva", "notion",
}


def domain_ok(company: str, domain: str | None) -> bool:
    if not domain:
        return False
    host = domain.lower().removeprefix("www.")
    if host in BLOCKLIST or any(host.endswith(f".{b}") for b in BLOCKLIST):
        return False
    if host.endswith((".edu", ".gov", ".gov.in", ".ac.in", ".nic.in")):
        return False
    toks = tokens(company)
    compact = re.sub(r"[^a-z0-9]", "", company.lower())
    slug = host.split(".")[0]
    host_flat = host.replace(".", "")
    joined = "".join(toks)
    hyphen = "-".join(toks)

    if slug in COMMON_FALSE_SLUGS:
        # Only allow if a longer distinctive brand form is present in the host
        if not (joined and len(joined) >= len(slug) + 3 and joined in host_flat):
            return False

    if compact and len(compact) >= 6 and compact in host_flat:
        return True
    if joined and len(joined) >= 5 and joined in host_flat:
        return True
    if hyphen and len(hyphen) >= 5 and hyphen in host:
        return True
    if len(toks) >= 2:
        first_two = toks[0] + toks[1]
        if len(first_two) >= 6 and first_two in host_flat:
            return True
        return False
    if len(toks) == 1 and len(toks[0]) >= 5 and toks[0] == slug and slug not in COMMON_FALSE_SLUGS:
        return True
    return False


def flatten(row: dict) -> dict:
    flat = {k: row.get(k, "") for k in CSV_FIELDS}
    for key in ("emails", "phones", "linkedin_urls", "decision_makers", "errors"):
        val = row.get(key) or []
        if isinstance(val, list):
            if key in ("emails", "phones") and val and isinstance(val[0], dict):
                flat[key] = "; ".join(f"{i.get('value','')}" for i in val)
            elif key == "decision_makers" and val and isinstance(val[0], dict):
                flat[key] = "; ".join(f"{i.get('name','')}|{i.get('role','')}" for i in val)
            else:
                flat[key] = "; ".join(str(x) for x in val)
    return flat


def summarize(results: list[dict]) -> dict:
    n = len(results) or 1
    domain_found = sum(1 for r in results if r.get("domain"))
    email = sum(1 for r in results if r.get("emails") or r.get("founder_email") or r.get("general_email"))
    phone = sum(1 for r in results if r.get("phones") or r.get("business_phone"))
    li_person = sum(1 for r in results if r.get("linkedin_person_url"))
    li_company = sum(1 for r in results if r.get("linkedin_company_url"))
    status_counts: dict[str, int] = {}
    for r in results:
        st = r.get("enrichment_status") or "unknown"
        status_counts[st] = status_counts.get(st, 0) + 1
    return {
        "total": len(results),
        "domain_found": domain_found,
        "domain_found_pct": round(100 * domain_found / n, 1),
        "with_email": email,
        "with_email_pct": round(100 * email / n, 1),
        "with_phone": phone,
        "with_phone_pct": round(100 * phone / n, 1),
        "linkedin_person": li_person,
        "linkedin_person_pct": round(100 * li_person / n, 1),
        "linkedin_company": li_company,
        "linkedin_company_pct": round(100 * li_company / n, 1),
        "status_counts": status_counts,
        "qa_note": "Post-filtered mismatched/blocklisted domains; contacts cleared when domain rejected",
    }


def main() -> None:
    payload = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    leads = payload["leads"]
    rejected = []
    for lead in leads:
        domain = lead.get("domain")
        if domain and not domain_ok(lead.get("company_name") or "", domain):
            rejected.append((lead.get("company_name"), domain))
            lead["errors"] = list(lead.get("errors") or []) + [f"qa_rejected_domain:{domain}"]
            lead["domain"] = None
            lead["website"] = None
            lead["pages_scraped"] = 0
            lead["emails"] = []
            lead["phones"] = []
            lead["founder_email"] = ""
            lead["general_email"] = ""
            lead["support_email"] = ""
            lead["business_phone"] = ""
            lead["enrichment_status"] = "domain_not_found"

    # Drop phones that appear on many unrelated leads (SERP pollution)
    phone_freq: dict[str, int] = {}
    for lead in leads:
        for p in lead.get("phones") or []:
            val = p.get("value") if isinstance(p, dict) else str(p)
            if val:
                phone_freq[val] = phone_freq.get(val, 0) + 1
    polluted = {p for p, n in phone_freq.items() if n >= 4}
    for lead in leads:
        if not lead.get("phones"):
            continue
        lead["phones"] = [
            p for p in lead["phones"]
            if (p.get("value") if isinstance(p, dict) else str(p)) not in polluted
        ]
        if lead.get("business_phone") in polluted:
            lead["business_phone"] = lead["phones"][0]["value"] if lead["phones"] else ""

    # Drop obviously broken emails
    for lead in leads:
        cleaned = []
        for e in lead.get("emails") or []:
            val = (e.get("value") if isinstance(e, dict) else str(e)).strip()
            if not val or " " in val or val.startswith("%") or val.startswith("-") or "google@" in val:
                continue
            if len(val) > 80:
                continue
            e = dict(e) if isinstance(e, dict) else {"value": val}
            e["value"] = val.lstrip("-").strip()
            cleaned.append(e)
        lead["emails"] = cleaned
        for field in ("founder_email", "general_email", "support_email"):
            v = (lead.get(field) or "").strip()
            if v.startswith("%") or v.startswith("-") or "google@" in v or " " in v:
                lead[field] = ""

    payload["leads"] = leads
    payload["qa_rejected"] = [{"company": c, "domain": d} for c, d in rejected]
    JSON_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in leads:
            writer.writerow(flatten(row))
    summary = summarize(leads)
    summary["elapsed_seconds"] = payload.get("elapsed_seconds")
    summary["qa_rejected_count"] = len(rejected)
    summary["polluted_phones_removed"] = sorted(polluted)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("QA rejected:", len(rejected))
    for c, d in rejected:
        print(" ", c, "->", d)
    print("Polluted phones removed:", sorted(polluted))
    print(json.dumps({k: summary[k] for k in summary if k != "polluted_phones_removed"}, indent=2))


if __name__ == "__main__":
    main()
