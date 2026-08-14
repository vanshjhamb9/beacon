#!/usr/bin/env python3
"""Deep enrich Kochi industry companies → domain, CEO/MD, emails, phones.

Uses FounderCompanyEnricher + extra public CEO/director discovery
(Bing RSS, LinkedIn SERP, ZaubaCorp/TheCompanyCheck snippets, site crawl).
Lawful public sources only — never invents contacts.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import httpx

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "packages" / "sales_intelligence_platform"))
sys.path.insert(0, str(ROOT / "packages"))

from engines.founder_company_enricher import FounderCompanyEnricher  # noqa: E402
from engines.real_contact_enricher import USER_AGENTS  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("enrich_kochi")

CEO_NAME_RE = re.compile(
    r"(?:CEO|C\.E\.O|Managing Director|MD|Founder|Director|Proprietor|"
    r"Chief Executive(?: Officer)?)\s*(?:of|:|-|–|—|,)?\s*"
    r"([A-Z][a-zA-Z\.]+(?:\s+[A-Z][a-zA-Z\.]+){0,3})",
)
NAME_THEN_ROLE_RE = re.compile(
    r"([A-Z][a-zA-Z\.]+(?:\s+[A-Z][a-zA-Z\.]+){1,3})\s*[,|–—-]?\s*"
    r"(?:CEO|Managing Director|MD|Founder|Director)",
)
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(
    r"(?:\+?91[\s\-.]*)?(?:0)?[6-9]\d{9}|\+?91[\s\-.]*(?:\d{2,5}[\s\-.]+){1,3}\d{4,}"
)
ZAUBA_DIR_RE = re.compile(
    r"([A-Z][A-Z\s]{4,40}?)\s+(?:is|was)?\s*(?:the\s+)?(?:Director|Managing Director|CEO)",
    re.I,
)

CSV_FIELDS = [
    "company_name",
    "location",
    "industry",
    "company_size",
    "year_founded",
    "company_type",
    "enrichment_status",
    "domain",
    "website",
    "ceo_name",
    "ceo_title",
    "ceo_email",
    "ceo_phone",
    "ceo_linkedin",
    "general_email",
    "business_phone",
    "all_emails",
    "all_phones",
    "linkedin_company_url",
    "decision_makers",
    "ceo_sources",
    "pages_scraped",
    "errors",
]


def _headers() -> dict[str, str]:
    import random

    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }


def _clean_person_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name or "").strip(" .,;:|-")
    # Drop all-caps corporate noise
    bad = {
        "PRIVATE", "LIMITED", "COMPANY", "INDIA", "KOCHI", "KERALA", "DIRECTOR",
        "MANAGING", "FOUNDER", "CEO", "PVT", "LTD", "LLP", "THE", "AND",
    }
    parts = [p for p in name.split() if p.upper() not in bad and len(p) > 1]
    if len(parts) < 2:
        return ""
    # Prefer Title Case person names
    if sum(1 for p in parts if p[:1].isupper()) < 2 and not name.isupper():
        return ""
    # Reject if looks like company fragment
    joined = " ".join(parts)
    if any(x in joined.lower() for x in ("pvt", "ltd", "llp", "private", "limited", "http")):
        return ""
    if len(joined) > 60:
        return ""
    return " ".join(parts[:4]).title() if joined.isupper() else " ".join(parts[:4])


def _extract_names_from_text(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for m in CEO_NAME_RE.finditer(text):
        n = _clean_person_name(m.group(1))
        if n:
            found.append((n, "CEO/Director"))
    for m in NAME_THEN_ROLE_RE.finditer(text):
        n = _clean_person_name(m.group(1))
        if n:
            found.append((n, "CEO/Director"))
    return found


async def bing_rss_items(client: httpx.AsyncClient, query: str) -> list[dict[str, str]]:
    url = f"https://www.bing.com/search?q={quote_plus(query)}&format=rss"
    try:
        r = await client.get(
            url,
            headers={**_headers(), "Accept": "application/rss+xml,application/xml"},
            follow_redirects=True,
            timeout=12,
        )
        if r.status_code != 200 or "<item>" not in r.text:
            return []
        root = ET.fromstring(r.text)
        items = []
        for item in root.findall(".//item"):
            items.append(
                {
                    "title": item.findtext("title") or "",
                    "link": item.findtext("link") or "",
                    "description": item.findtext("description") or "",
                }
            )
        return items
    except Exception as exc:
        logger.debug("bing rss fail: %s", exc)
        return []


async def fetch_text(client: httpx.AsyncClient, url: str) -> str:
    try:
        r = await client.get(url, headers=_headers(), follow_redirects=True, timeout=12)
        if r.status_code >= 400:
            return ""
        html = r.text[:200000]
        html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
        text = re.sub(r"<[^>]+>", " ", html)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return ""


async def discover_ceo(
    client: httpx.AsyncClient,
    company: str,
    location: str,
    base: dict[str, Any],
) -> dict[str, Any]:
    """Extra public CEO/MD discovery beyond base enricher output."""
    city = (location or "").split(",")[0].strip() or "Kochi"
    sources: list[str] = []
    candidates: list[dict[str, Any]] = []

    # From base decision makers
    for dm in base.get("decision_makers") or []:
        name = _clean_person_name(str(dm.get("name") or ""))
        role = str(dm.get("role") or "Decision Maker")
        if name:
            candidates.append(
                {
                    "name": name,
                    "title": role,
                    "linkedin": dm.get("linkedin_url") or "",
                    "source": dm.get("source_url") or "site_crawl",
                    "score": 0.7 if any(k in role.lower() for k in ("ceo", "founder", "managing", "director")) else 0.45,
                }
            )

    queries = [
        f'"{company}" CEO {city}',
        f'"{company}" "Managing Director" {city}',
        f'"{company}" Founder {city}',
        f'"{company}" director site:zaubacorp.com',
        f'"{company}" director site:thecompanycheck.com',
        f'"{company}" CEO site:linkedin.com/in',
    ]

    for q in queries:
        items = await bing_rss_items(client, q)
        await asyncio.sleep(0.6)
        for it in items:
            blob = f"{it['title']} {it['description']}"
            sources.append(f"serp:{q[:50]}|{it['title'][:80]}")
            for name, role in _extract_names_from_text(blob):
                score = 0.55
                link = it["link"]
                if "linkedin.com/in" in link:
                    score = 0.75
                if "zauba" in link or "companycheck" in link:
                    score = 0.7
                candidates.append(
                    {
                        "name": name,
                        "title": role,
                        "linkedin": link if "linkedin.com/in" in link else "",
                        "source": link or q,
                        "score": score,
                    }
                )
            # Follow high-value registry pages
            if any(h in it["link"] for h in ("zaubacorp.com", "thecompanycheck.com", "indiafilings.com", "tofler.in")):
                page = await fetch_text(client, it["link"])
                await asyncio.sleep(0.4)
                if page:
                    sources.append(f"page:{it['link'][:120]}")
                    for name, role in _extract_names_from_text(page[:8000]):
                        candidates.append(
                            {
                                "name": name,
                                "title": role,
                                "linkedin": "",
                                "source": it["link"],
                                "score": 0.8,
                            }
                        )
                    # Zauba often lists directors in ALL CAPS
                    for m in re.finditer(
                        r"Directors?\s*[:\-]?\s*([A-Z][A-Z\s\.]{5,50})",
                        page[:12000],
                    ):
                        n = _clean_person_name(m.group(1))
                        if n:
                            candidates.append(
                                {
                                    "name": n,
                                    "title": "Director",
                                    "linkedin": "",
                                    "source": it["link"],
                                    "score": 0.85,
                                }
                            )

    # Also scan about excerpt / profile snippets
    for sn in base.get("profile_snippets") or []:
        blob = f"{sn.get('snippet','')}"
        for name, role in _extract_names_from_text(blob):
            candidates.append({"name": name, "title": role, "linkedin": "", "source": "serp_snippet", "score": 0.5})
    if base.get("about_excerpt"):
        for name, role in _extract_names_from_text(base["about_excerpt"]):
            candidates.append({"name": name, "title": role, "linkedin": "", "source": "about_excerpt", "score": 0.6})

    # Rank / dedupe
    best: dict[str, dict[str, Any]] = {}
    for c in candidates:
        key = re.sub(r"[^a-z]", "", c["name"].lower())
        if len(key) < 5:
            continue
        prev = best.get(key)
        if not prev or c["score"] > prev["score"]:
            best[key] = c
        elif prev and c.get("linkedin") and not prev.get("linkedin"):
            prev["linkedin"] = c["linkedin"]

    ranked = sorted(best.values(), key=lambda x: x["score"], reverse=True)
    ceo = ranked[0] if ranked else None

    # If CEO known, try to find personal/business email mentioning CEO name on site / SERP
    ceo_email = ""
    ceo_phone = ""
    ceo_linkedin = ""
    if ceo:
        ceo_linkedin = ceo.get("linkedin") or base.get("linkedin_person_url") or ""
        # Prefer emails whose local-part matches CEO first/last
        tokens = [t.lower() for t in ceo["name"].split() if len(t) > 2]
        for e in base.get("emails") or []:
            val = (e.get("value") if isinstance(e, dict) else str(e)).lower()
            local = val.split("@")[0]
            if any(t in local for t in tokens):
                ceo_email = val
                break
        if not ceo_email:
            items = await bing_rss_items(
                client, f'"{ceo["name"]}" "{company}" email OR contact OR @{ (base.get("domain") or "gmail.com") }'
            )
            await asyncio.sleep(0.5)
            for it in items:
                blob = f"{it['title']} {it['description']}"
                for em in EMAIL_RE.findall(blob):
                    em_l = em.lower()
                    if any(x in em_l for x in ("example.", "sentry.", "wixpress", "schema")):
                        continue
                    local = em_l.split("@")[0]
                    if any(t in local for t in tokens) or (base.get("domain") and base["domain"] in em_l):
                        ceo_email = em_l
                        sources.append(f"ceo_email_serp:{it['link'][:100]}")
                        break
                if ceo_email:
                    break
        # Phone: prefer business phone; try CEO-specific SERP
        ceo_phone = base.get("business_phone") or ""
        if not ceo_phone and (base.get("phones") or []):
            p0 = base["phones"][0]
            ceo_phone = p0.get("value") if isinstance(p0, dict) else str(p0)

    return {
        "ceo_name": ceo["name"] if ceo else "",
        "ceo_title": ceo["title"] if ceo else "",
        "ceo_email": ceo_email,
        "ceo_phone": ceo_phone,
        "ceo_linkedin": ceo_linkedin,
        "ceo_candidates": ranked[:5],
        "ceo_sources": sources[:20],
    }


def flatten_row(seed: dict, base: dict, ceo: dict) -> dict:
    emails = base.get("emails") or []
    phones = base.get("phones") or []
    email_vals = []
    for e in emails:
        email_vals.append(e.get("value") if isinstance(e, dict) else str(e))
    phone_vals = []
    for p in phones:
        phone_vals.append(p.get("value") if isinstance(p, dict) else str(p))
    dms = base.get("decision_makers") or []
    dm_str = "; ".join(
        f"{d.get('name','')}|{d.get('role','')}" for d in dms if isinstance(d, dict)
    )
    general = base.get("general_email") or ""
    if not general and email_vals:
        general = email_vals[0]
    biz_phone = base.get("business_phone") or (phone_vals[0] if phone_vals else "")
    return {
        "company_name": seed.get("company_name", ""),
        "location": seed.get("location", ""),
        "industry": seed.get("industry", ""),
        "company_size": seed.get("company_size", ""),
        "year_founded": seed.get("year_founded", ""),
        "company_type": seed.get("company_type", ""),
        "enrichment_status": base.get("enrichment_status", ""),
        "domain": base.get("domain") or "",
        "website": base.get("website") or "",
        "ceo_name": ceo.get("ceo_name") or "",
        "ceo_title": ceo.get("ceo_title") or "",
        "ceo_email": ceo.get("ceo_email") or "",
        "ceo_phone": ceo.get("ceo_phone") or biz_phone,
        "ceo_linkedin": ceo.get("ceo_linkedin") or "",
        "general_email": general,
        "business_phone": biz_phone,
        "all_emails": "; ".join(email_vals),
        "all_phones": "; ".join(phone_vals),
        "linkedin_company_url": base.get("linkedin_company_url") or "",
        "decision_makers": dm_str,
        "ceo_sources": " | ".join((ceo.get("ceo_sources") or [])[:8]),
        "pages_scraped": base.get("pages_scraped") or 0,
        "errors": "; ".join(base.get("errors") or []),
    }


async def run(seed_path: Path, out_json: Path, out_csv: Path, limit: int | None) -> dict:
    leads = json.loads(seed_path.read_text(encoding="utf-8"))
    if limit is not None:
        leads = leads[:limit]

    enricher = FounderCompanyEnricher(timeout=10.0, delay=0.8, max_concurrent=2, max_pages=10)
    results: list[dict] = []
    flat_rows: list[dict] = []
    checkpoint = out_json.with_suffix(".checkpoint.json")
    t0 = time.time()
    start = 0
    if checkpoint.exists() and limit is None:
        try:
            prev = json.loads(checkpoint.read_text(encoding="utf-8"))
            if isinstance(prev, list) and prev:
                results = prev
                start = len(prev)
                logger.info("Resuming checkpoint at %d", start)
        except Exception:
            results = []
            start = 0

    async with httpx.AsyncClient(timeout=12.0, verify=False) as client:
        for i, lead in enumerate(leads[start:], start + 1):
            company = lead.get("company_name", "")
            logger.info("[%d/%d] Enriching %s", i, len(leads), company)
            try:
                base_obj = await enricher.enrich(
                    founder_name=lead.get("founder_name") or "",
                    company_name=company,
                    location=lead.get("location", ""),
                    industry=lead.get("industry", ""),
                    job_title=lead.get("job_title", ""),
                    company_size=lead.get("company_size"),
                )
                base = base_obj.to_dict()
            except Exception as exc:  # noqa: BLE001
                logger.exception("base enrich failed: %s", company)
                base = {
                    "company_name": company,
                    "enrichment_status": "error",
                    "errors": [str(exc)],
                    "emails": [],
                    "phones": [],
                    "decision_makers": [],
                }

            try:
                ceo = await discover_ceo(client, company, lead.get("location", ""), base)
            except Exception as exc:  # noqa: BLE001
                logger.exception("ceo discover failed: %s", company)
                ceo = {"ceo_name": "", "ceo_email": "", "ceo_phone": "", "ceo_sources": [str(exc)]}

            # If CEO found and base had no founder, optionally re-enrich contacts with founder hint
            if ceo.get("ceo_name") and base.get("domain") and not (base.get("founder_email") or lead.get("founder_name")):
                try:
                    base2 = await enricher.contact.enrich(
                        base["domain"],
                        company,
                        founder_name=ceo["ceo_name"],
                        allow_guesses=False,
                    )
                    # Merge any new emails/phones
                    existing = {(e.get("value") if isinstance(e, dict) else e) for e in (base.get("emails") or [])}
                    for e in base2.emails:
                        if e.confidence >= 0.5 and e.value not in existing and e.source_url != "pattern_guess":
                            base.setdefault("emails", []).append(
                                {
                                    "value": e.value,
                                    "label": e.label,
                                    "source_url": e.source_url,
                                    "confidence": e.confidence,
                                }
                            )
                            existing.add(e.value)
                    if base2.founder_email and not ceo.get("ceo_email"):
                        tokens = [t.lower() for t in ceo["ceo_name"].split() if len(t) > 2]
                        if any(t in base2.founder_email.lower() for t in tokens):
                            ceo["ceo_email"] = base2.founder_email
                    if base2.business_phone and not base.get("business_phone"):
                        base["business_phone"] = base2.business_phone
                        if not ceo.get("ceo_phone"):
                            ceo["ceo_phone"] = base2.business_phone
                except Exception as exc:  # noqa: BLE001
                    base.setdefault("errors", []).append(f"ceo_recrawl:{exc}")

            row = {
                "seed": lead,
                "enrichment": base,
                "ceo": ceo,
                "flat": flatten_row(lead, base, ceo),
            }
            results.append(row)
            flat_rows.append(row["flat"])
            checkpoint.write_text(json.dumps(results, ensure_ascii=False), encoding="utf-8")
            await asyncio.sleep(0.4)

    # Rebuild flat if resumed
    if len(flat_rows) < len(results):
        flat_rows = [r["flat"] if "flat" in r else flatten_row(r.get("seed", {}), r.get("enrichment", {}), r.get("ceo", {})) for r in results]

    out_json.parent.mkdir(parents=True, exist_ok=True)
    summary = _summarize(flat_rows)
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "seed": str(seed_path),
        "total": len(flat_rows),
        "elapsed_seconds": round(time.time() - t0, 1),
        "summary": summary,
        "leads": results,
        "table": flat_rows,
    }
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in flat_rows:
            writer.writerow(row)
    summary_path = out_json.with_name(out_json.stem + "_summary.json")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if checkpoint.exists():
        checkpoint.unlink(missing_ok=True)
    logger.info("Summary: %s", json.dumps(summary))
    return summary


def _summarize(rows: list[dict]) -> dict:
    n = len(rows) or 1
    return {
        "total": len(rows),
        "domain_found": sum(1 for r in rows if r.get("domain")),
        "domain_found_pct": round(100 * sum(1 for r in rows if r.get("domain")) / n, 1),
        "with_ceo_name": sum(1 for r in rows if r.get("ceo_name")),
        "with_ceo_email": sum(1 for r in rows if r.get("ceo_email")),
        "with_ceo_phone": sum(1 for r in rows if r.get("ceo_phone")),
        "with_any_email": sum(1 for r in rows if r.get("general_email") or r.get("all_emails") or r.get("ceo_email")),
        "with_any_phone": sum(1 for r in rows if r.get("business_phone") or r.get("all_phones") or r.get("ceo_phone")),
        "with_linkedin_company": sum(1 for r in rows if r.get("linkedin_company_url")),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=Path, default=ROOT / "data" / "kochi_industries_seed.json")
    p.add_argument("--out-json", type=Path, default=ROOT / "exports" / "kochi_industries_enriched.json")
    p.add_argument("--out-csv", type=Path, default=ROOT / "exports" / "kochi_industries_enriched.csv")
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()
    asyncio.run(run(args.seed, args.out_json, args.out_csv, args.limit))


if __name__ == "__main__":
    main()
