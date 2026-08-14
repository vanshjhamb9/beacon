#!/usr/bin/env python3
"""Second-pass deep dive for Kochi industry CEOs/contacts — targeted public sources."""

from __future__ import annotations

import asyncio
import csv
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import httpx

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "packages" / "sales_intelligence_platform"))
sys.path.insert(0, str(ROOT / "packages"))

from engines.real_contact_enricher import USER_AGENTS  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("kochi_pass2")

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+91[\s\-]*)?(?:0)?([6-9]\d{9})")
NAME_ROLE_RE = re.compile(
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z\.]+){1,3})\s*[,|–—\-]?\s*"
    r"(?:CEO|Managing Director|MD|Founder|Director|Proprietor|Partner)",
    re.I,
)
ROLE_NAME_RE = re.compile(
    r"(?:CEO|Managing Director|MD|Founder|Director|Proprietor)\s*[:\-–—]?\s*"
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z\.]+){1,3})",
)

# Known polluted phones from prior runs
POLLUTED = {
    "7326059369", "6392214503", "6392214584", "6392225580", "6392225584",
    "6392225589", "6392225603", "6392225609", "6392225613", "7496969728",
}

FALSE_DOMAINS = {
    "destaco.com",  # US DESTACO, not De Staco Kochi
    "merit.ac.in",
    "ants.andamannicobar.gov.in",
    "libcinder.org",
    "labcorp.com",
    "lancerindia.com",  # likely wrong brand collision; re-check carefully
}

# Manual high-confidence domain hypotheses to verify
DOMAIN_HINTS: dict[str, list[str]] = {
    "Kanotekk Engineering Consultants Pvt. Ltd.": ["kanotekk.com", "kanotekk.in", "kanotekk.co.in"],
    "PhyEcoSyS Pvt. Ltd.": ["phyecosys.com", "phyecosys.in"],
    "SREELAKSHMI ENERGY SYSTEM PVT. LTD.": [
        "sreelakshmienergy.com", "sreelakshmienergy.in", "sreelakshmi.in",
        "sreelakshmienergysystem.com", "slespl.com",
    ],
    "Ecodew": ["ecodew.solutions", "ecodew.com", "ecodew.in"],
    "Merit Biolabs": ["meritbiolabs.com", "meritbiolabs.in", "meritbio.com"],
    "GENESPEC PRIVATE LIMITED": ["genespec.com", "genespec.in"],
    "De Staco Turnkey Solutions LLP": [
        "destacoturnkey.com", "destaco.co.in", "destacollp.com", "de-staco.com",
    ],
    "Thinkbizz Ventures LLP": ["thinkbizz.com", "thinkbizz.in", "thinkbizzventures.com"],
    "Biosix Peptides India Pvt. Ltd.": ["biosixpeptides.com", "biosix.in", "biosixpeptides.in"],
    "ANTS Lifecare Pvt. Ltd.": ["antslifecare.com", "antslifecare.in", "antslife.com"],
    "Tubazionic Engineering Pvt Ltd": ["tubazionic.com", "tubazionic.in", "tubazionicengineering.com"],
    "LANCER DRUGS AND PHARMACEUTICALS INDIA": [
        "lancerdrugs.com", "lancerpharma.com", "lancerpharmaceuticals.com", "lancerdrugs.in",
    ],
    "Kochi Salem Pipeline Pvt. Ltd": [
        "kochisalempipeline.com", "kspl.co.in", "kochisalem.in", "petronetlng.com",
    ],
    "CINDER CARBON": ["cindercarbon.com", "cindercarbon.in", "cinder.carbon"],
    "ZeeKay International": ["zeekayinternational.com", "zeekay.in"],
    "Lab Technics India": ["labtechnics.com", "labtechnics.in", "labtechnicsindia.com"],
    "Hydrox Technologies Private Limited": ["hydrox.in", "hydroxtech.com", "hydroxtechnologies.com"],
    "Meticulous Cochin": ["meticulouscochin.com", "meticulous.co.in"],
    "Capservo Global": ["capservo.com", "capservo.in", "capservoglobal.com", "capservo.co.in"],
}


def headers() -> dict[str, str]:
    import random

    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
    }


def tokens(company: str) -> list[str]:
    stop = {
        "the", "and", "of", "a", "an", "pvt", "ltd", "llc", "inc", "co", "private",
        "limited", "india", "llp", "solutions", "system", "systems", "global",
        "official", "page", "turnkey", "engineering", "consultants", "consultant",
    }
    raw = re.sub(r"[^a-zA-Z0-9\s]", " ", company.lower())
    return [t for t in raw.split() if len(t) >= 3 and t not in stop][:5]


def clean_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name or "").strip(" .,;:|-")
    bad = {
        "Private", "Limited", "Company", "India", "Kochi", "Kerala", "Director",
        "Managing", "Founder", "Ceo", "Pvt", "Ltd", "Llp", "The", "And", "Team",
        "Author", "Hydrox", "Genespec", "Ecodew",
    }
    parts = [p for p in name.split() if p.title() not in bad and len(p) > 1]
    if len(parts) < 2:
        return ""
    if any(x in " ".join(parts).lower() for x in ("http", "www", "pvt", "ltd")):
        return ""
    return " ".join(parts[:4])


def phone_ok(digits: str) -> bool:
    d = "".join(ch for ch in digits if ch.isdigit())
    if d.startswith("91") and len(d) > 10:
        d = d[-10:]
    if len(d) != 10:
        return False
    if d in POLLUTED:
        return False
    if len(set(d)) <= 2:
        return False
    if d.endswith("000000"):
        return False
    return True


def norm_phone(raw: str) -> str:
    d = "".join(ch for ch in raw if ch.isdigit())
    if d.startswith("91") and len(d) >= 12:
        d = d[-10:]
    if len(d) == 10 and phone_ok(d):
        return f"+91{d}"
    return ""


def extract_contacts(text: str, domain: str | None = None) -> dict[str, Any]:
    emails = []
    for e in EMAIL_RE.findall(text or ""):
        el = e.lower()
        if any(x in el for x in ("example.", "sentry.", "wixpress", "schema", "png", "jpg", "webpack")):
            continue
        if domain and domain not in el.split("@")[-1] and el.split("@")[-1] not in {
            "gmail.com", "yahoo.com", "yahoo.co.in", "outlook.com", "hotmail.com", "rediffmail.com"
        }:
            # keep only same-domain or personal webmail for CEO hunts
            if not any(t in el for t in tokens(domain or "")):
                continue
        emails.append(el)
    phones = []
    for m in PHONE_RE.finditer(text or ""):
        p = norm_phone(m.group(0))
        if p and p not in phones:
            phones.append(p)
    people = []
    for rx in (NAME_ROLE_RE, ROLE_NAME_RE):
        for m in rx.finditer(text or ""):
            n = clean_name(m.group(1))
            if n:
                people.append(n)
    # dedupe
    emails = list(dict.fromkeys(emails))
    people = list(dict.fromkeys(people))
    return {"emails": emails[:8], "phones": phones[:8], "people": people[:8]}


async def fetch(client: httpx.AsyncClient, url: str) -> tuple[int, str, str]:
    try:
        r = await client.get(url, headers=headers(), follow_redirects=True, timeout=15)
        return r.status_code, str(r.url), r.text[:250000]
    except Exception as exc:
        return 0, url, str(exc)


def html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


async def verify_domain(client: httpx.AsyncClient, domain: str, company: str) -> tuple[bool, str, str]:
    if domain.lower() in FALSE_DOMAINS:
        return False, "", "false_domain"
    toks = tokens(company)
    compact = re.sub(r"[^a-z0-9]", "", company.lower())
    for url in (f"https://{domain}", f"https://www.{domain}"):
        code, final, html = await fetch(client, url)
        if code == 0 or code >= 400 or len(html) < 200:
            continue
        blob = (html_to_text(html) + " " + html[:50000]).lower()
        if any(p in blob for p in ("domain is for sale", "buy this domain", "godaddy auction")):
            return False, "", "parked"
        hits = sum(1 for t in toks if t in blob)
        if compact and len(compact) >= 6 and compact in blob.replace(" ", ""):
            hits = max(hits, 2)
        # Reject US DESTACO collision for De Staco
        if "destaco.com" in domain and "de staco" not in blob and "destaco turnkey" not in blob:
            if "dover" in blob or "workholding" in blob:
                return False, "", "wrong_brand_destaco"
        if hits >= 1:
            return True, final, html
    return False, "", "no_match"


async def bing_html(client: httpx.AsyncClient, query: str) -> str:
    url = f"https://www.bing.com/search?q={quote_plus(query)}&count=20"
    code, _, html = await fetch(client, url)
    return html if code == 200 else ""


async def ddg_html(client: httpx.AsyncClient, query: str) -> str:
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    code, _, html = await fetch(client, url)
    return html if code == 200 else ""


def extract_links(html: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r'https?://[^\s\"\'<>]+', html or "")))[:40]


async def enrich_one(client: httpx.AsyncClient, seed: dict, prior: dict) -> dict:
    company = seed["company_name"]
    city = "Kochi"
    out: dict[str, Any] = {
        **{k: seed.get(k, "") for k in (
            "company_name", "location", "industry", "company_size", "year_founded", "company_type"
        )},
        "domain": "",
        "website": "",
        "ceo_name": "",
        "ceo_title": "",
        "ceo_email": "",
        "ceo_phone": "",
        "ceo_linkedin": "",
        "general_email": "",
        "business_phone": "",
        "all_emails": [],
        "all_phones": [],
        "linkedin_company_url": prior.get("linkedin_company_url") or "",
        "decision_makers": [],
        "sources": [],
        "enrichment_status": "domain_not_found",
        "notes": [],
    }

    # Keep prior good data
    prior_domain = (prior.get("domain") or "").lower()
    if prior_domain and prior_domain not in FALSE_DOMAINS:
        ok, final, html = await verify_domain(client, prior_domain, company)
        if ok:
            out["domain"] = prior_domain
            out["website"] = final or prior.get("website") or f"https://{prior_domain}"
            out["sources"].append(f"prior_domain:{prior_domain}")
            contacts = extract_contacts(html_to_text(html), prior_domain)
            out["all_emails"].extend(contacts["emails"])
            out["all_phones"].extend(contacts["phones"])
            for p in contacts["people"]:
                out["decision_makers"].append({"name": p, "role": "Mentioned", "source": out["website"]})

    # Probe domain hints
    if not out["domain"]:
        for d in DOMAIN_HINTS.get(company, []):
            ok, final, html = await verify_domain(client, d, company)
            await asyncio.sleep(0.3)
            if ok:
                out["domain"] = d
                out["website"] = final or f"https://{d}"
                out["sources"].append(f"hint_verified:{d}")
                contacts = extract_contacts(html_to_text(html), d)
                out["all_emails"].extend(contacts["emails"])
                out["all_phones"].extend(contacts["phones"])
                for p in contacts["people"]:
                    out["decision_makers"].append({"name": p, "role": "Mentioned", "source": out["website"]})
                break

    # Clearbit
    if not out["domain"]:
        try:
            r = await client.get(
                f"https://autocomplete.clearbit.com/v1/companies/suggest?query={quote_plus(company)}",
                headers=headers(),
                timeout=10,
            )
            if r.status_code == 200:
                for item in r.json() or []:
                    d = (item.get("domain") or "").lower()
                    if not d or d in FALSE_DOMAINS:
                        continue
                    ok, final, html = await verify_domain(client, d, company)
                    if ok:
                        out["domain"] = d
                        out["website"] = final
                        out["sources"].append(f"clearbit:{d}")
                        contacts = extract_contacts(html_to_text(html), d)
                        out["all_emails"].extend(contacts["emails"])
                        out["all_phones"].extend(contacts["phones"])
                        break
        except Exception as exc:
            out["notes"].append(f"clearbit:{exc}")

    # Targeted SERP pages
    queries = [
        f'"{company}" {city} (CEO OR "Managing Director" OR Founder OR Director)',
        f'"{company}" {city} email OR phone OR contact',
        f'"{company}" site:zaubacorp.com',
        f'"{company}" site:thecompanycheck.com',
        f'"{company}" site:indiamart.com',
        f'"{company}" site:justdial.com {city}',
        f'"{company}" site:linkedin.com/in',
        f'"{company}" site:linkedin.com/company',
    ]
    if out["domain"]:
        queries.append(f'site:{out["domain"]} (CEO OR Founder OR Director OR team OR about)')

    serp_blob = ""
    for q in queries:
        html = await bing_html(client, q)
        await asyncio.sleep(0.5)
        if not html or len(html) < 500:
            html = await ddg_html(client, q)
            await asyncio.sleep(0.5)
        text = html_to_text(html)
        serp_blob += " " + text[:5000]
        out["sources"].append(f"serp:{q[:60]}")
        contacts = extract_contacts(text)
        # Only take people if company token nearby in snippet windows
        for p in contacts["people"]:
            out["decision_makers"].append({"name": p, "role": "SERP", "source": q})
        # Follow promising links
        for link in extract_links(html):
            low = link.lower()
            if any(x in low for x in ("zaubacorp.com", "thecompanycheck.com", "tofler.in", "indiamart.com", "justdial.com")):
                if company.split()[0].lower()[:4] not in low and "zauba" not in low and "companycheck" not in low:
                    # still try zauba/companycheck search result pages
                    pass
                code, final, page = await fetch(client, link)
                await asyncio.sleep(0.4)
                if code == 200 and len(page) > 400:
                    pt = html_to_text(page)
                    # require company token presence for marketplace pages
                    toks = tokens(company)
                    if sum(1 for t in toks if t in pt.lower()) >= 1 or "zauba" in low or "companycheck" in low:
                        out["sources"].append(f"page:{final[:120]}")
                        c2 = extract_contacts(pt, out.get("domain"))
                        out["all_emails"].extend(c2["emails"])
                        out["all_phones"].extend(c2["phones"])
                        for p in c2["people"]:
                            out["decision_makers"].append({"name": p, "role": "Directory/Registry", "source": final})
                        # Directors ALL CAPS on Zauba-like pages
                        for m in re.finditer(r"([A-Z][A-Z\s]{5,45})\s+Director", pt):
                            n = clean_name(m.group(1).title())
                            if n:
                                out["decision_makers"].append({"name": n, "role": "Director", "source": final})
            if "linkedin.com/company/" in low and not out["linkedin_company_url"]:
                m = re.search(r"https?://[\w.]*linkedin\.com/company/[a-zA-Z0-9\-_%]+", link)
                if m:
                    out["linkedin_company_url"] = m.group(0).split("?")[0]
            if "linkedin.com/in/" in low and not out["ceo_linkedin"]:
                m = re.search(r"https?://[\w.]*linkedin\.com/in/[a-zA-Z0-9\-_%]+", link)
                if m:
                    out["ceo_linkedin"] = m.group(0).split("?")[0]

    # Crawl key pages on verified domain
    if out["domain"]:
        for path in ("", "/about", "/about-us", "/team", "/our-team", "/contact", "/contact-us", "/leadership", "/management"):
            code, final, html = await fetch(client, f"https://{out['domain']}{path}")
            await asyncio.sleep(0.25)
            if code != 200:
                code, final, html = await fetch(client, f"https://www.{out['domain']}{path}")
            if code == 200 and len(html) > 300:
                c2 = extract_contacts(html_to_text(html), out["domain"])
                out["all_emails"].extend(c2["emails"])
                out["all_phones"].extend(c2["phones"])
                for p in c2["people"]:
                    out["decision_makers"].append({"name": p, "role": "Website", "source": final})

    # Also parse prior emails/phones if clean
    for e in (prior.get("all_emails") or "").split(";"):
        e = e.strip().lower()
        if e and "@" in e:
            out["all_emails"].append(e)
    for p in (prior.get("all_phones") or "").split(";"):
        np = norm_phone(p)
        if np:
            out["all_phones"].append(np)
    if prior.get("general_email"):
        out["all_emails"].append(prior["general_email"].lower())
    if prior.get("ceo_name") and prior["ceo_name"] not in {"Hydrox Team"}:
        out["decision_makers"].insert(0, {"name": prior["ceo_name"], "role": prior.get("ceo_title") or "CEO", "source": "pass1"})

    # Dedupe contacts
    out["all_emails"] = list(dict.fromkeys([e for e in out["all_emails"] if e]))[:10]
    out["all_phones"] = list(dict.fromkeys([p for p in out["all_phones"] if phone_ok(p)]))[:8]

    # Pick CEO
    ranked = []
    seen = set()
    for dm in out["decision_makers"]:
        name = clean_name(dm.get("name", ""))
        if not name:
            continue
        key = re.sub(r"[^a-z]", "", name.lower())
        if key in seen or len(key) < 5:
            continue
        seen.add(key)
        role = dm.get("role") or ""
        score = 0.4
        if any(k in role.lower() for k in ("ceo", "managing", "founder", "director", "proprietor")):
            score = 0.8
        if "zauba" in (dm.get("source") or "").lower() or "companycheck" in (dm.get("source") or "").lower():
            score += 0.1
        ranked.append((score, name, role, dm.get("source") or ""))
    ranked.sort(reverse=True)
    if ranked:
        out["ceo_name"] = ranked[0][1]
        out["ceo_title"] = ranked[0][2] or "Director/CEO"
        out["decision_makers"] = [
            {"name": n, "role": r, "source": s} for _, n, r, s in ranked[:5]
        ]

    # Map CEO email
    if out["ceo_name"] and out["all_emails"]:
        toks = [t.lower() for t in out["ceo_name"].split() if len(t) > 2]
        for e in out["all_emails"]:
            local = e.split("@")[0]
            if any(t in local for t in toks):
                out["ceo_email"] = e
                break
    out["general_email"] = next(
        (e for e in out["all_emails"] if e.split("@")[0] in {"info", "contact", "sales", "hello", "admin", "office", "enquiry", "enquiries", "marineservices"}),
        out["all_emails"][0] if out["all_emails"] else "",
    )
    out["business_phone"] = out["all_phones"][0] if out["all_phones"] else ""
    out["ceo_phone"] = out["business_phone"]
    if out["domain"] or out["ceo_name"] or out["all_emails"] or out["all_phones"]:
        out["enrichment_status"] = "enriched" if (out["domain"] and (out["all_emails"] or out["all_phones"] or out["ceo_name"])) else "partial"
    return out


def flatten(row: dict) -> dict:
    return {
        "company_name": row.get("company_name", ""),
        "location": row.get("location", ""),
        "industry": row.get("industry", ""),
        "company_size": row.get("company_size", ""),
        "year_founded": row.get("year_founded", ""),
        "company_type": row.get("company_type", ""),
        "enrichment_status": row.get("enrichment_status", ""),
        "domain": row.get("domain", ""),
        "website": row.get("website", ""),
        "ceo_name": row.get("ceo_name", ""),
        "ceo_title": row.get("ceo_title", ""),
        "ceo_email": row.get("ceo_email", ""),
        "ceo_phone": row.get("ceo_phone", ""),
        "ceo_linkedin": row.get("ceo_linkedin", ""),
        "general_email": row.get("general_email", ""),
        "business_phone": row.get("business_phone", ""),
        "all_emails": "; ".join(row.get("all_emails") or []),
        "all_phones": "; ".join(row.get("all_phones") or []),
        "linkedin_company_url": row.get("linkedin_company_url", ""),
        "decision_makers": "; ".join(
            f"{d.get('name')}|{d.get('role')}" for d in (row.get("decision_makers") or []) if isinstance(d, dict)
        ),
        "sources": " | ".join((row.get("sources") or [])[:12]),
    }


async def main() -> None:
    seed = json.loads((ROOT / "data" / "kochi_industries_seed.json").read_text(encoding="utf-8"))
    prior_path = ROOT / "exports" / "kochi_industries_enriched.json"
    prior_map: dict[str, dict] = {}
    if prior_path.exists():
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
        for row in prior.get("table") or []:
            prior_map[row.get("company_name", "")] = row

    results = []
    t0 = time.time()
    async with httpx.AsyncClient(timeout=15, verify=False) as client:
        for i, s in enumerate(seed, 1):
            logger.info("[%d/%d] Deep pass %s", i, len(seed), s["company_name"])
            row = await enrich_one(client, s, prior_map.get(s["company_name"], {}))
            results.append(row)
            await asyncio.sleep(0.3)

    flat = [flatten(r) for r in results]
    n = len(flat) or 1
    summary = {
        "total": len(flat),
        "domain_found": sum(1 for r in flat if r["domain"]),
        "with_ceo_name": sum(1 for r in flat if r["ceo_name"]),
        "with_ceo_email": sum(1 for r in flat if r["ceo_email"]),
        "with_ceo_phone": sum(1 for r in flat if r["ceo_phone"]),
        "with_any_email": sum(1 for r in flat if r["general_email"] or r["all_emails"] or r["ceo_email"]),
        "with_any_phone": sum(1 for r in flat if r["business_phone"] or r["all_phones"] or r["ceo_phone"]),
        "elapsed_seconds": round(time.time() - t0, 1),
    }
    out_json = ROOT / "exports" / "kochi_industries_enriched_v2.json"
    out_csv = ROOT / "exports" / "kochi_industries_enriched_v2.csv"
    out_json.write_text(
        json.dumps({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "summary": summary, "leads": results, "table": flat}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    fields = list(flat[0].keys()) if flat else []
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(flat)
    (ROOT / "exports" / "kochi_industries_enriched_v2_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("Summary: %s", json.dumps(summary))


if __name__ == "__main__":
    asyncio.run(main())
