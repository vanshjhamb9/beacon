"""CSV batch enrichment helpers — parse Apollo-style CSVs and export results."""

from __future__ import annotations

import csv
import io
import re
from typing import Any

from .founder_company_enricher import FounderCompanyEnricher, FounderCompanyResult

# Flexible header aliases for Apollo / custom exports
_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "founder_name": (
        "founder_name", "founder", "name", "full_name", "fullname name",
        "contact_name", "person", "lead_name", "first_name",
    ),
    "company_name": (
        "company_name", "company", "organization", "org", "account",
        "account_name", "company name",
    ),
    "job_title": (
        "job_title", "title", "role", "job title", "position", "designation",
    ),
    "location": (
        "location", "city", "geo", "hq", "headquarters", "region", "address",
    ),
    "industry": ("industry", "company_industry", "company industry", "sector"),
    "company_size": (
        "company_size", "employees", "employee_count", "company size", "headcount",
    ),
}

_COMMON_FALSE_SLUGS = frozenset(
    {
        "bot", "point", "aura", "reset", "twist", "trek", "brave", "odd", "ginger",
        "leaf", "nest", "care", "fire", "vision", "corner", "weave", "pixel", "plus",
        "gen", "tea", "rose", "empire", "social", "digital", "media", "brand", "ads",
        "walas", "lowkey", "mega", "apple", "google", "meta", "amazon",
    }
)

_STOP = {
    "the", "and", "of", "a", "an", "pvt", "ltd", "llc", "inc", "co",
    "private", "limited", "solutions", "solution", "media", "digital",
    "marketing", "agency", "studio", "studios", "group", "services",
    "service", "company", "technologies", "technology", "tech",
}

EXPORT_FIELDS = [
    "founder_name",
    "company_name",
    "job_title",
    "location",
    "industry",
    "company_size",
    "enrichment_status",
    "domain",
    "website",
    "pages_scraped",
    "founder_email",
    "general_email",
    "support_email",
    "business_phone",
    "emails",
    "phones",
    "linkedin_person_url",
    "linkedin_company_url",
    "linkedin_urls",
    "decision_makers",
    "about_excerpt",
    "errors",
]


def _norm_header(value: str) -> str:
    return re.sub(r"[\s\-]+", "_", value.strip().lower())


def _map_headers(fieldnames: list[str] | None) -> dict[str, str]:
    """Map canonical field → actual CSV header."""
    if not fieldnames:
        return {}
    available = {_norm_header(h): h for h in fieldnames}
    mapping: dict[str, str] = {}
    for canonical, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            key = _norm_header(alias)
            if key in available:
                mapping[canonical] = available[key]
                break
    return mapping


def parse_leads_csv(csv_text: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse CSV into lead dicts. Returns (leads, warnings)."""
    warnings: list[str] = []
    reader = csv.DictReader(io.StringIO(csv_text))
    mapping = _map_headers(list(reader.fieldnames or []))
    if "company_name" not in mapping:
        raise ValueError(
            "CSV must include a company column "
            "(company_name / company / organization)."
        )
    if "founder_name" not in mapping:
        warnings.append("No founder/name column found — enriching by company only.")

    leads: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in reader:
        company = str(row.get(mapping["company_name"]) or "").strip()
        if not company:
            continue
        founder = ""
        if "founder_name" in mapping:
            founder = str(row.get(mapping["founder_name"]) or "").strip()
        # Support First Name + Last Name style Apollo exports
        if not founder:
            first = row.get("First Name") or row.get("first_name") or ""
            last = row.get("Last Name") or row.get("last_name") or ""
            founder = f"{first} {last}".strip()

        key = (founder.lower(), company.lower())
        if key in seen:
            continue
        seen.add(key)

        size_raw = row.get(mapping["company_size"]) if "company_size" in mapping else None
        size: str | int | None = None
        if size_raw not in (None, ""):
            try:
                size = int(str(size_raw).strip())
            except ValueError:
                size = str(size_raw).strip()

        leads.append(
            {
                "founder_name": founder,
                "company_name": company,
                "job_title": (
                    str(row.get(mapping["job_title"]) or "").strip()
                    if "job_title" in mapping
                    else ""
                ),
                "location": (
                    str(row.get(mapping["location"]) or "").strip()
                    if "location" in mapping
                    else ""
                ),
                "industry": (
                    str(row.get(mapping["industry"]) or "").strip()
                    if "industry" in mapping
                    else ""
                ),
                "company_size": size,
            }
        )
    if not leads:
        raise ValueError("CSV contained no usable lead rows.")
    return leads, warnings


def domain_passes_qa(company_name: str, domain: str | None) -> bool:
    """High-precision domain check (same policy as batch QA)."""
    if not domain:
        return False
    host = domain.lower().removeprefix("www.")
    if host.endswith((".edu", ".gov", ".gov.in", ".ac.in", ".nic.in")):
        return False
    raw = re.sub(r"[^a-zA-Z0-9\s]", " ", company_name.lower())
    toks = [t for t in raw.split() if len(t) >= 2 and t not in _STOP][:5]
    compact = re.sub(r"[^a-z0-9]", "", company_name.lower())
    slug = host.split(".")[0]
    host_flat = host.replace(".", "")
    joined = "".join(toks)

    if slug in _COMMON_FALSE_SLUGS:
        if not (joined and len(joined) >= len(slug) + 3 and joined in host_flat):
            return False
    if compact and len(compact) >= 6 and compact in host_flat:
        return True
    if joined and len(joined) >= 5 and joined in host_flat:
        return True
    if len(toks) >= 2:
        first_two = toks[0] + toks[1]
        return len(first_two) >= 6 and first_two in host_flat
    if len(toks) == 1 and len(toks[0]) >= 5 and toks[0] == slug and slug not in _COMMON_FALSE_SLUGS:
        return True
    return False


def apply_result_qa(result: FounderCompanyResult) -> FounderCompanyResult:
    if result.domain and not domain_passes_qa(result.company_name, result.domain):
        result.errors.append(f"qa_rejected_domain:{result.domain}")
        result.domain = None
        result.website = None
        result.pages_scraped = 0
        result.emails = []
        result.phones = []
        result.founder_email = ""
        result.general_email = ""
        result.support_email = ""
        result.business_phone = ""
        result.enrichment_status = "domain_not_found"
    # Clean broken emails
    cleaned = []
    for e in result.emails:
        val = str(e.get("value") or "").strip().lstrip("-")
        if not val or " " in val or val.startswith("%") or "google@" in val or len(val) > 80:
            continue
        e = dict(e)
        e["value"] = val
        cleaned.append(e)
    result.emails = cleaned
    return result


def results_to_csv(results: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=EXPORT_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for row in results:
        flat = {k: row.get(k, "") for k in EXPORT_FIELDS}
        for key in ("emails", "phones", "linkedin_urls", "decision_makers", "errors"):
            val = row.get(key) or []
            if isinstance(val, list):
                if key in ("emails", "phones") and val and isinstance(val[0], dict):
                    flat[key] = "; ".join(str(i.get("value", "")) for i in val)
                elif key == "decision_makers" and val and isinstance(val[0], dict):
                    flat[key] = "; ".join(
                        f"{i.get('name', '')}|{i.get('role', '')}" for i in val
                    )
                else:
                    flat[key] = "; ".join(str(x) for x in val)
        writer.writerow(flat)
    return buf.getvalue()


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(results) or 1
    domain_found = sum(1 for r in results if r.get("domain"))
    email = sum(
        1
        for r in results
        if r.get("emails") or r.get("founder_email") or r.get("general_email")
    )
    phone = sum(1 for r in results if r.get("phones") or r.get("business_phone"))
    li_person = sum(1 for r in results if r.get("linkedin_person_url"))
    li_company = sum(1 for r in results if r.get("linkedin_company_url"))
    return {
        "total": len(results),
        "domain_found": domain_found,
        "domain_found_pct": round(100 * domain_found / n, 1),
        "with_email": email,
        "with_email_pct": round(100 * email / n, 1),
        "with_phone": phone,
        "with_phone_pct": round(100 * phone / n, 1),
        "linkedin_person": li_person,
        "linkedin_company": li_company,
    }


async def enrich_leads_batch(
    leads: list[dict[str, Any]],
    *,
    on_progress: Any | None = None,
    delay: float = 0.8,
    max_pages: int = 8,
) -> list[dict[str, Any]]:
    enricher = FounderCompanyEnricher(
        timeout=8.0, delay=delay, max_concurrent=2, max_pages=max_pages
    )
    results: list[dict[str, Any]] = []
    for i, lead in enumerate(leads, 1):
        try:
            raw = await enricher.enrich(
                founder_name=str(lead.get("founder_name") or ""),
                company_name=str(lead.get("company_name") or ""),
                location=str(lead.get("location") or ""),
                industry=str(lead.get("industry") or ""),
                job_title=str(lead.get("job_title") or ""),
                company_size=lead.get("company_size"),
            )
            raw = apply_result_qa(raw)
            results.append(raw.to_dict())
        except Exception as exc:  # noqa: BLE001
            results.append(
                {
                    **lead,
                    "enrichment_status": "error",
                    "domain": None,
                    "website": None,
                    "pages_scraped": 0,
                    "emails": [],
                    "phones": [],
                    "errors": [str(exc)],
                }
            )
        if on_progress:
            on_progress(i, len(leads), results[-1])
    # Drop polluted phones appearing on many leads
    freq: dict[str, int] = {}
    for r in results:
        for p in r.get("phones") or []:
            val = p.get("value") if isinstance(p, dict) else str(p)
            if val:
                freq[val] = freq.get(val, 0) + 1
    polluted = {p for p, n in freq.items() if n >= 4}
    if polluted:
        for r in results:
            phones = r.get("phones") or []
            r["phones"] = [
                p
                for p in phones
                if (p.get("value") if isinstance(p, dict) else str(p)) not in polluted
            ]
            if r.get("business_phone") in polluted:
                r["business_phone"] = (
                    r["phones"][0]["value"] if r["phones"] else ""
                )
    return results
