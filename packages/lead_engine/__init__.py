"""Lead Engine — Volume + ICP-strict + Intent.

Hard gates: mega brands, already-sent, clear ICP misses, unusable mailboxes.
Intent gate: only keep leads with real pitch signals (ranked highest).
Volume: multi-wave live discovery + adjacent-ICP backfill to hit limit.
"""

from __future__ import annotations

import csv
import json
import logging
import re
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
EXPORT_ROOT = ROOT / "exports" / "lead_engine_runs"
SEEN_PATH = EXPORT_ROOT / "_seen_emails.json"  # permanently excluded (sent)
LAST_RUN_PATH = EXPORT_ROOT / "_last_run_emails.json"  # rotated each Start Engine
POOL_PATH = EXPORT_ROOT / "_outreach_pool.json"  # accumulating NEW high-intent for bulk send
SURFACED_PATH = EXPORT_ROOT / "_surfaced_emails.json"  # already shown in engine (not re-shown)
TRIED_DOMAINS_PATH = EXPORT_ROOT / "_live_tried_domains.json"  # live-scrape attempts
AUTO_STATE_PATH = EXPORT_ROOT / "_auto_scheduler.json"

# Hard mega / scale-up brands — never pitch as 5–40 headcount ComAI ICP
COMAI_EXCLUDE_SUBSTR = (
    "mamaearth",
    "nykaa",
    "boat-lifestyle",
    "boatlifestyle",
    "boat.in",
    "lenskart",
    "bewakoof",
    "myntra",
    "ajio",
    "flipkart",
    "amazon",
    "sugarcosmetics",
    "sugar cosmetics",
    "plumgoodness",
    "plum goodness",
    "bluestone",
    "thesouledstore",
    "souled store",
    "mokobara",
    "bellavita",
    "bella vita",
    "damensch",
    "dotandkey",
    "dot & key",
    "dot and key",
    "faebeauty",
    "fae beauty",
    "snitch",
    "giva",
    "wakefit",
    "supertails",
    "mcaffeine",
    "minimalist",
    "beminimalist",
    "foxtale",
    "rare rabbit",
    "faballey",
    "chumbak",
    "melorra",
    "senco",
    "countrydelight",
    "sleepyowl",
    "bombayshirt",
    "huemn",
    "headsupfortails",
    "tatacliq",
    "shoppersstop",
    "reliancetrends",
    "pantaloons",
    "limeroad",
    "manyavar",
    "caratlane",
    "tanishq",
    "healthkart",
    "muscleblaze",
    "himalaya",
    "lakme",
    # Enterprise / conglomerate fashion & beauty
    "levi",
    "levis",
    "louisphilippe",
    "louis philippe",
    "allensolly",
    "allen solly",
    "peterengland",
    "peter england",
    "vanheusen",
    "van heusen",
    "parkavenue",
    "park avenue",
    "raymond",
    "blackberrys",
    "blackberry",
    "jackjones",
    "jack & jones",
    "jack and jones",
    "biba",
    "bibaindia",
    "indianterrain",
    "indian terrain",
    "killerjeans",
    "killer jeans",
    "abfrl",
    "beinghuman",
    "being human",
    "soch",
    "wforwoman",
    "w for woman",
    "aurelia",
    "globaldesi",
    "global desi",
    "veromoda",
    "vero moda",
    "pepejeans",
    "pepe jeans",
    "arrowlife",
    "fireboltt",
    "fire-boltt",
    "gonoise",
    "noise",
    "atomberg",
    "portronics",
    "boult",
    "myglamm",
    "colorbar",
    "facescanada",
    "biotique",
    "vlcc",
    "lotusherbals",
    "cetaphil",
    "cerave",
    "thefaceshop",
    "innisfree",
    "kamaayurveda",
    "kama ayurveda",
    "forestessentials",
    "forest essentials",
    "clovia",
    "zivame",
    "houseofindya",
    "indya",
    "perniaspopup",
    "meenabazaar",
    "candere",
    "zaveri",
    "johnjacobs",
    "thesleepcompany",
    "sleepyhead",
    "manmatters",
    "beardo",
    "ustraa",
    "themancompany",
    "epigamia",
    "gocolors",
    "libas",
    "cheryls",
    "sugarpop",
    "blueheaven",
    "bajajnomarks",
    "dermaco",
    "thedermaco",
    "wowskin",
    "buywow",
)

# Conglomerate / shared care domains — never pitch
CONGLOMERATE_EMAIL_DOMAINS = (
    "abfrl.in",
    "raymond.in",
    "levi.in",
    "lakmeindia.com",
    "himalayawellness.in",
    "tata.com",
    "reliance.com",
    "adityabirla.com",
)

# When CSV size is blank, known floors (employees) — used for hard headcount checks
KNOWN_SIZE_FLOOR: dict[str, int] = {
    "bellavita": 200,
    "damensch": 100,
    "dot & key": 150,
    "dotandkey": 150,
    "fae beauty": 50,
    "snitch": 200,
    "giva": 200,
    "mamaearth": 500,
    "sugar cosmetics": 300,
    "plum goodness": 200,
    "foxtale": 80,
    "minimalist": 150,
    "bewakoof": 300,
    "the souled store": 300,
    "bluestone": 400,
    "wakefit": 500,
    "levi": 1000,
    "louis philippe": 800,
    "allen solly": 800,
    "peter england": 800,
    "van heusen": 800,
    "park avenue": 500,
    "raymond": 2000,
    "blackberry": 400,
    "jack & jones": 500,
    "biba": 800,
    "indian terrain": 400,
    "killer jeans": 300,
    "being human": 200,
    "soch": 400,
    "manyavar": 1000,
    "w for woman": 400,
    "aurelia": 300,
    "global desi": 300,
    "fire-boltt": 300,
    "noise": 400,
    "atomberg": 300,
    "myglamm": 400,
    "biotique": 500,
    "vlcc": 1000,
    "himalaya": 2000,
    "lakme": 1000,
    "kama ayurveda": 300,
    "forest essentials": 400,
    "clovia": 300,
    "zivame": 400,
    "candere": 300,
}

# Unusable for founder outreach even in volume mode
HARD_REJECT_LOCALPARTS = (
    "noreply",
    "no-reply",
    "donotreply",
    "do-not-reply",
    "mailer-daemon",
    "postmaster",
    "careers",
    "career",
    "hr",
    "jobs",
    "recruit",
    "recruitment",
    "privacy",
    "legal",
    "compliance",
    "unsubscribe",
    "bounce",
    "customersupport",
    "customer.support",
    "customercare",
    "customer.care",
    "consumercare",
    "consumercarecell",
    "feedback",
    "happytohelp",
    "ncustomerservice",
    "customerservice",
)

# Soft generics — brand hello/care/info OK but demoted; support desk is weak for founder ICP
SOFT_GENERIC_LOCALPARTS = (
    "hello",
    "hi",
    "care",
    "wecare",
    "contact",
    "info",
    "collab",
    "collaborate",
    "team",
    "orders",
    "shop",
    "enquiry",
    "inquiry",
    "sales",
    "marketing",
    "support",  # mid-D2C brand support@ allowed but demoted; corporate *care* still hard-rejected
    "help",
)

# Weak for COMAI founder pitch (keep only if nothing better; heavy demotion)
WEAK_OUTREACH_LOCALPARTS = (
    "franchise",
    "franchising",
    "community",
    "press",
    "media",
    "pr",
    "news",
    "blog",
    "investors",
    "investor",
    "ir",
    "partners",
    "vendor",
    "vendors",
    "alerts",
    "noreply",
    "notifications",
    "notify",
)

FREEMAIL_HOSTS = (
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
)

# Desk inboxes that are never pitchable (conglomerate care cells)
DESK_REJECT_LOCALPARTS = (
    "customersupport",
    "customer.support",
    "customercare",
    "customer.care",
    "consumercare",
    "consumercarecell",
    "feedback",
    "happytohelp",
    "ncustomerservice",
    "customerservice",
)

# Agency / non-D2C markers when ICP asks for d2c_brand
AGENCY_MARKERS = (
    "agency",
    "mediacom",
    "media com",
    "digital marketing",
    "performance marketing",
    "consulting",
    "consultancy",
    "solutions pvt",
    "it services",
    "software services",
    "web design",
    "ad agency",
)

_JOBS: dict[str, dict[str, Any]] = {}


def _load_sent_emails() -> set[str]:
    """Permanently exclude successfully contacted emails only."""
    seen: set[str] = set()
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    if SEEN_PATH.exists():
        try:
            data = json.loads(SEEN_PATH.read_text(encoding="utf-8"))
            for e in data.get("emails") or []:
                if isinstance(e, str) and "@" in e:
                    seen.add(e.lower().strip())
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed reading sent ledger: %s", exc)

    for path in (
        ROOT / "exports" / "comai_icp_founder_outreach_report.json",
        ROOT / "exports" / "comai_icp_wave2_outreach_report.json",
        ROOT / "exports" / "dual_lane_fresh_outreach_report.json",
        ROOT / "exports" / "inowix_high_intent_outreach_report.json",
    ):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rows = data.get("results") or data.get("leads") or data.get("sent") or []
            if isinstance(rows, list):
                for r in rows:
                    if not isinstance(r, dict):
                        continue
                    e = (r.get("to_email") or r.get("email") or "").lower().strip()
                    if e and "@" in e and r.get("success") is True:
                        seen.add(e)
        except Exception:  # noqa: BLE001
            continue

    master = ROOT / "exports" / "comai_all_collected_leads_master.csv"
    if master.exists():
        try:
            with master.open(encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    status = (row.get("outreach_status") or "").lower()
                    if "sent" in status:
                        e = (row.get("email") or row.get("to_email") or "").lower().strip()
                        if e:
                            seen.add(e)
        except Exception:  # noqa: BLE001
            pass
    return seen


def _load_json_email_set(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {str(e).lower().strip() for e in (data.get("emails") or []) if e and "@" in str(e)}
    except Exception:  # noqa: BLE001
        return set()


def _save_json_email_set(path: Path, emails: set[str] | list[str], *, merge: bool = True) -> None:
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    current = _load_json_email_set(path) if merge else set()
    current.update(e.lower().strip() for e in emails if e and "@" in e)
    path.write_text(
        json.dumps(
            {
                "updated_at": datetime.now(UTC).isoformat(),
                "count": len(current),
                "emails": sorted(current),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _load_surfaced_emails() -> set[str]:
    """Emails already shown/pooled — soft memory only (file), no historical CSV bootstrap.

    Historical bootstrap was emptying the funnel to 1 lead. Permanently blocked
    contacts live in the sent ledger instead.
    """
    return _load_json_email_set(SURFACED_PATH)


def _persist_surfaced_emails(emails: set[str] | list[str]) -> None:
    _save_json_email_set(SURFACED_PATH, emails, merge=True)


def _load_tried_domains() -> set[str]:
    if not TRIED_DOMAINS_PATH.exists():
        return set()
    try:
        data = json.loads(TRIED_DOMAINS_PATH.read_text(encoding="utf-8"))
        return {str(d).lower().strip() for d in (data.get("domains") or []) if d}
    except Exception:  # noqa: BLE001
        return set()


def _persist_tried_domains(domains: set[str] | list[str]) -> None:
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    current = _load_tried_domains()
    current.update(d.lower().strip() for d in domains if d)
    TRIED_DOMAINS_PATH.write_text(
        json.dumps(
            {
                "updated_at": datetime.now(UTC).isoformat(),
                "count": len(current),
                "domains": sorted(current),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def load_outreach_pool() -> list[dict[str, Any]]:
    if not POOL_PATH.exists():
        return []
    try:
        data = json.loads(POOL_PATH.read_text(encoding="utf-8"))
        return list(data.get("leads") or [])
    except Exception:  # noqa: BLE001
        return []


def save_outreach_pool(leads: list[dict[str, Any]]) -> None:
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    POOL_PATH.write_text(
        json.dumps(
            {
                "updated_at": datetime.now(UTC).isoformat(),
                "count": len(leads),
                "leads": leads,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def merge_into_outreach_pool(new_leads: list[dict[str, Any]]) -> int:
    """Append NEW high-intent leads not already in pool / sent. Returns added count."""
    sent = _load_sent_emails()
    pool = load_outreach_pool()
    have = {(x.get("email") or "").lower().strip() for x in pool}
    added = 0
    for lead in new_leads:
        email = (lead.get("email") or "").lower().strip()
        if not email or email in sent or email in have:
            continue
        if float(lead.get("intent_score") or 0) < 45:
            continue
        if lead.get("already_contacted"):
            continue
        row = dict(lead)
        row["pooled_at"] = datetime.now(UTC).isoformat()
        row["outreach_status"] = "pooled"
        pool.append(row)
        have.add(email)
        added += 1
    save_outreach_pool(pool)
    return added


def take_from_outreach_pool(limit: int = 40) -> list[dict[str, Any]]:
    """Return up to `limit` pooled leads that are still unsent (for Start Outreach)."""
    sent = _load_sent_emails()
    pool = load_outreach_pool()
    keep: list[dict[str, Any]] = []
    taken: list[dict[str, Any]] = []
    for lead in pool:
        email = (lead.get("email") or "").lower().strip()
        if not email or email in sent:
            continue
        if len(taken) < limit:
            taken.append(lead)
        else:
            keep.append(lead)
    # leave remaining in pool (taken stay until sent)
    save_outreach_pool(taken + keep)
    return taken


_AUTO: dict[str, Any] = {
    "enabled": False,
    "interval_sec": 600,
    "product": "comai",
    "limit": 40,
    "icp": {},
    "task": None,
    "last_run_id": None,
    "last_started_at": None,
    "last_error": None,
    "runs_completed": 0,
}


def get_auto_status() -> dict[str, Any]:
    pool = load_outreach_pool()
    sent = _load_sent_emails()
    fresh_pool = [x for x in pool if (x.get("email") or "").lower() not in sent]
    return {
        "enabled": bool(_AUTO.get("enabled")),
        "interval_sec": int(_AUTO.get("interval_sec") or 600),
        "product": _AUTO.get("product") or "comai",
        "limit": int(_AUTO.get("limit") or 40),
        "last_run_id": _AUTO.get("last_run_id"),
        "last_started_at": _AUTO.get("last_started_at"),
        "last_error": _AUTO.get("last_error"),
        "runs_completed": int(_AUTO.get("runs_completed") or 0),
        "pool_count": len(fresh_pool),
        "pool_ready": sum(
            1 for x in fresh_pool if float(x.get("intent_score") or 0) >= 55
        ),
    }


async def _auto_loop() -> None:
    import asyncio

    while _AUTO.get("enabled"):
        try:
            job = create_run(
                product=str(_AUTO.get("product") or "comai"),
                icp=dict(_AUTO.get("icp") or {}),
                limit=int(_AUTO.get("limit") or 40),
            )
            _AUTO["last_run_id"] = job["run_id"]
            _AUTO["last_started_at"] = time.time()
            _AUTO["last_error"] = None
            await run_pipeline(job["run_id"])
            _AUTO["runs_completed"] = int(_AUTO.get("runs_completed") or 0) + 1
            EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
            AUTO_STATE_PATH.write_text(
                json.dumps({k: v for k, v in get_auto_status().items()}, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Auto lead-engine run failed")
            _AUTO["last_error"] = str(exc)
        # wait interval (interruptible)
        for _ in range(int(_AUTO.get("interval_sec") or 600)):
            if not _AUTO.get("enabled"):
                break
            await asyncio.sleep(1)


def start_auto_scheduler(
    *,
    product: str = "comai",
    icp: dict[str, Any] | None = None,
    limit: int = 40,
    interval_sec: int = 600,
) -> dict[str, Any]:
    import asyncio

    _AUTO["enabled"] = True
    _AUTO["product"] = (product or "comai").lower()
    _AUTO["icp"] = icp or {}
    _AUTO["limit"] = max(1, min(int(limit), 150))
    _AUTO["interval_sec"] = max(120, int(interval_sec))
    task = _AUTO.get("task")
    if task is None or getattr(task, "done", lambda: True)():
        _AUTO["task"] = asyncio.create_task(_auto_loop())
    return get_auto_status()


def stop_auto_scheduler() -> dict[str, Any]:
    _AUTO["enabled"] = False
    return get_auto_status()


_YC_HIRING_URL = "https://yc-oss.github.io/api/companies/hiring.json"
_YC_TOP_URL = "https://yc-oss.github.io/api/companies/top.json"
_yc_cache: list[dict[str, Any]] | None = None
_yc_cache_ts: float = 0.0


def _fetch_yc_companies() -> list[dict[str, Any]]:
    """Fetch YC companies from the public OSS mirror. Cached for 6 hours."""
    global _yc_cache, _yc_cache_ts  # noqa: PLW0603
    import time
    now = time.time()
    if _yc_cache is not None and (now - _yc_cache_ts) < 21600:
        return _yc_cache
    try:
        import httpx
        rows: list[dict[str, Any]] = []
        for url in (_YC_HIRING_URL, _YC_TOP_URL):
            try:
                resp = httpx.get(url, timeout=30.0, headers={"User-Agent": "BeaconLeadEngine/1.0"})
                if resp.status_code >= 400:
                    continue
                data = resp.json()
                if isinstance(data, list):
                    rows.extend(data)
                elif isinstance(data, dict) and isinstance(data.get("companies"), list):
                    rows.extend(data["companies"])
            except Exception:  # noqa: BLE001
                continue
        _yc_cache = rows
        _yc_cache_ts = now
        logger.info("YC OSS: fetched %d companies", len(rows))
        return rows
    except Exception as exc:  # noqa: BLE001
        logger.warning("YC OSS fetch failed: %s", exc)
        return _yc_cache or []


def _yc_to_leads(industries: list[str], cities: list[str]) -> list[dict[str, Any]]:
    """Convert YC OSS data to lead dicts matching the verified brands format."""
    from packages.ecommerce_leads.models import RawEcommerceLead
    rows = _fetch_yc_companies()
    leads: list[dict[str, Any]] = []
    seen_domains: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        website = row.get("website") or ""
        if not website:
            continue
        if not website.startswith("http"):
            website = f"https://{website}"
        domain = website.replace("https://", "").replace("http://", "").rstrip("/")
        if not domain or domain in seen_domains:
            continue
        seen_domains.add(domain)
        # Extract industry from YC data
        yc_industries = row.get("industries") or []
        if isinstance(yc_industries, list) and yc_industries:
            industry = str(yc_industries[0]).lower()
        else:
            industry = str(row.get("industry") or "saas").lower()
        # Map YC industry tags to ICP-friendly terms
        industry_map = {
            "ai": "artificial intelligence",
            "fintech": "fintech",
            "health": "healthtech",
            "education": "edtech",
            "ecommerce": "marketplace",
            "productivity": "productivity",
            "devtools": "developer tools",
            "developer tools": "developer tools",
            "design": "design tools",
            "security": "cybersecurity",
            "infrastructure": "developer tools",
        }
        industry = industry_map.get(industry, industry)
        location = str(row.get("all_locations") or row.get("location") or "")
        city = location.split(",")[0].strip() if location else ""
        is_hiring = bool(row.get("isHiring") or row.get("is_hiring"))
        batch = str(row.get("batch") or "")
        founders = []
        for f in row.get("founders") or []:
            if isinstance(f, dict) and (f.get("full_name") or f.get("name")):
                founders.append({
                    "name": str(f.get("full_name") or f.get("name")),
                    "role": str(f.get("title") or f.get("role") or "Founder"),
                })
        lead = {
            "company": name,
            "company_name": name,
            "domain": domain,
            "website": website,
            "industry": industry,
            "city": city,
            "source": "yc_oss",
            "yc_batch": batch,
            "yc_is_hiring": is_hiring,
            "yc_founders": founders,
            "company_type": "saas_product",
        }
        leads.append(lead)
    return leads


_HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search_by_date"
_HN_SAAS_QUERIES = [
    '"Show HN" SaaS startup',
    '"Show HN" launched',
    '"Show HN" MVP',
    '"Ask HN" hiring engineer',
    '"Ask HN" looking for co-founder',
    '"Ask HN" need developer',
    'building SaaS',
    'launched today startup',
    'YC startup hiring',
    'looking for technical co-founder',
    'founding engineer hire',
    'need full stack developer',
    'seeking CTO co-founder',
]
_hn_saas_cache: list[dict[str, Any]] | None = None
_hn_saas_cache_ts: float = 0.0


async def _fetch_hn_saas_signals(client: httpx.AsyncClient, limit: int = 30) -> list[dict[str, Any]]:
    """Fetch recent HN posts about SaaS startups/hiring. Cached for 2 hours."""
    global _hn_saas_cache, _hn_saas_cache_ts  # noqa: PLW0603
    import time
    now = time.time()
    if _hn_saas_cache is not None and (now - _hn_saas_cache_ts) < 7200:
        return _hn_saas_cache[:limit]
    import time as _time
    since = int(_time.time()) - (90 * 86400)  # 90 days
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for query in _HN_SAAS_QUERIES:
        if len(results) >= limit:
            break
        try:
            resp = await client.get(
                _HN_ALGOLIA_URL,
                params={
                    "query": query,
                    "tags": "story",
                    "hitsPerPage": 10,
                    "numericFilters": f"created_at_i>{since}",
                },
                timeout=15.0,
            )
            if resp.status_code >= 400:
                continue
            data = resp.json()
            for hit in data.get("hits") or []:
                if not isinstance(hit, dict):
                    continue
                object_id = hit.get("objectID", "")
                if not object_id or object_id in seen_ids:
                    continue
                seen_ids.add(object_id)
                title = str(hit.get("title") or hit.get("story_title") or "").strip()
                url = str(hit.get("url") or "") or None
                author = str(hit.get("author") or "") or None
                body = str(hit.get("story_text") or hit.get("comment_text") or "")[:2000]
                created = hit.get("created_at")
                published = None
                if isinstance(created, str):
                    published = created if created.endswith("Z") else f"{created}Z" if "T" in created else created
                website = None
                if url:
                    try:
                        from urllib.parse import urlparse as _urlparse
                        host = _urlparse(url).netloc.lower().removeprefix("www.")
                        if host and "ycombinator.com" not in host and "github.com" not in host:
                            website = f"https://{host}"
                    except Exception:  # noqa: BLE001
                        pass
                results.append({
                    "title": title,
                    "url": f"https://news.ycombinator.com/item?id={object_id}",
                    "author": author,
                    "body": body,
                    "published": published,
                    "website": website,
                    "source": "hn_algolia_saas",
                    "query": query,
                })
        except Exception:  # noqa: BLE001
            continue
    _hn_saas_cache = results
    _hn_saas_cache_ts = now
    logger.info("HN Algolia SaaS: found %d posts", len(results))
    return results[:limit]


def _hn_to_leads(signals: list[dict[str, Any]], industries: list[str], cities: list[str]) -> list[dict[str, Any]]:
    """Convert HN SaaS signals to lead dicts."""
    leads: list[dict[str, Any]] = []
    for sig in signals:
        website = sig.get("website")
        if not website:
            continue
        domain = website.replace("https://", "").replace("http://", "").rstrip("/")
        if not domain:
            continue
        title = sig.get("title", "")
        company = title
        for prefix in ("Show HN: ", "Ask HN: ", "Tell HN: ", "Launch HN: "):
            if company.startswith(prefix):
                company = company[len(prefix):]
        body_lower = (sig.get("body") or "").lower()
        industry = "saas"
        if any(k in body_lower for k in ("ai", "machine learning", "llm", "gpt")):
            industry = "artificial intelligence"
        elif any(k in body_lower for k in ("fintech", "payments", "banking")):
            industry = "fintech"
        elif any(k in body_lower for k in ("health", "medical", "clinical")):
            industry = "healthtech"
        elif any(k in body_lower for k in ("developer", "devtools", "api", "infrastructure")):
            industry = "developer tools"
        elif any(k in body_lower for k in ("design", "figma", "ui")):
            industry = "design tools"
        elif any(k in body_lower for k in ("education", "learning", "teaching")):
            industry = "edtech"
        industry_map = {
            "ai": "artificial intelligence",
            "machine learning": "artificial intelligence",
            "llm": "artificial intelligence",
        }
        industry = industry_map.get(industry, industry)
        city = ""
        is_hiring = any(k in body_lower for k in ("hiring", "looking for", "need engineer", "need developer", "co-founder", "join us"))
        leads.append({
            "company": company,
            "company_name": company,
            "domain": domain,
            "website": website,
            "industry": industry,
            "city": city,
            "source": "hn_algolia_saas",
            "hn_url": sig.get("url"),
            "hn_author": sig.get("author"),
            "hn_published": sig.get("published"),
            "hn_is_hiring": is_hiring,
            "company_type": "saas_product",
        })
    return leads


async def _live_discover_new(
    product: str,
    icp: dict[str, Any],
    *,
    exclude_emails: set[str],
    batch_limit: int = 40,
) -> list[dict[str, Any]]:
    """Live website enrichment for verified mid D2C brands matching ICP specialties."""
    try:
        from packages.ecommerce_leads.models import is_valid_email
        from packages.qualification_engine.enrichment import enrich_leads_batch
        if product == "inowix":
            from packages.qualification_engine.saas_verified_brands import get_saas_verified_leads as get_verified_leads
        else:
            from packages.qualification_engine.verified_brands import get_verified_leads
    except Exception as exc:  # noqa: BLE001
        logger.warning("Live discovery imports failed: %s", exc)
        return []

    industries = [
        str(x).lower()
        for x in list(icp.get("industries") or []) + list(icp.get("specialties") or [])
    ]
    cities = [str(x).lower() for x in (icp.get("headquarters_cities") or [])]
    tried = _load_tried_domains()
    # When cities are selected: HARD — only preferred_city (+ adjacent_city for industry).
    # Never soft-fill Pune/Mumbai/etc. under a Delhi-only ICP.
    preferred_city: list[Any] = []
    adjacent_city: list[Any] = []
    for vb in reversed(get_verified_leads()):
        name = vb.company_name or ""
        domain = (vb.domain or "").lower()
        if not domain or domain in tried:
            continue
        if _is_mega(name, domain):
            continue
        ind = (vb.industry or "").lower()
        city_ok = (not cities) or _city_match(vb.city or "", cities)
        if cities and not city_ok:
            continue  # hard skip other metros when HQ cities selected
        if not industries:
            preferred_city.append(vb)
        elif _industry_match(ind, industries):
            preferred_city.append(vb)
        elif _industry_adjacent(ind, industries):
            adjacent_city.append(vb)
        if len(preferred_city) >= batch_limit:
            break

    candidates: list[Any] = []
    for bucket in (preferred_city, adjacent_city):
        for vb in bucket:
            candidates.append(vb)
            if len(candidates) >= batch_limit:
                break
        if len(candidates) >= batch_limit:
            break

    # For Inowix: supplement with YC OSS companies not already in verified list
    if product == "inowix" and len(candidates) < batch_limit:
        try:
            yc_leads = _yc_to_leads(industries, cities)
            existing_domains = {c.domain.lower() for c in candidates if hasattr(c, 'domain')}
            existing_domains.update(tried)
            for ycl in yc_leads:
                if len(candidates) >= batch_limit:
                    break
                yd = ycl.get("domain", "").lower()
                yname = ycl.get("company_name") or ycl.get("company") or ""
                if not yd or yd in existing_domains:
                    continue
                if _is_mega(yname, yd):
                    continue
                yind = ycl.get("industry", "").lower()
                ycity = ycl.get("city", "").lower()
                if cities and not _city_match(ycity, cities):
                    continue
                if industries and not (
                    _industry_match(yind, industries) or _industry_adjacent(yind, industries)
                ):
                    continue
                # Wrap in a simple object for compatibility
                class _YCLead:
                    __slots__ = ("company_name", "domain", "industry", "city", "website", "raw")
                    def __init__(self, d: dict[str, Any]):
                        self.company_name = d.get("company_name") or d.get("company")
                        self.domain = d.get("domain", "")
                        self.industry = d.get("industry", "")
                        self.city = d.get("city", "")
                        self.website = d.get("website", "")
                        self.raw = d
                candidates.append(_YCLead(ycl))
                existing_domains.add(yd)
            logger.info("YC OSS: added %d candidates for inowix", len(candidates) - len(preferred_city) - len(adjacent_city))
        except Exception as exc:  # noqa: BLE001
            logger.warning("YC OSS integration failed: %s", exc)

    # For Inowix: supplement with HN Algolia SaaS signals
    if product == "inowix" and len(candidates) < batch_limit:
        try:
            import httpx as _httpx
            async with _httpx.AsyncClient(timeout=20.0, headers={"User-Agent": "BeaconLeadEngine/1.0"}) as hn_client:
                hn_signals = await _fetch_hn_saas_signals(hn_client, limit=20)
            hn_leads = _hn_to_leads(hn_signals, industries, cities)
            existing_domains = {c.domain.lower() for c in candidates if hasattr(c, 'domain')}
            existing_domains.update(tried)
            for hnl in hn_leads:
                if len(candidates) >= batch_limit:
                    break
                hd = hnl.get("domain", "").lower()
                hname = hnl.get("company_name") or hnl.get("company") or ""
                if not hd or hd in existing_domains:
                    continue
                if _is_mega(hname, hd):
                    continue
                hind = hnl.get("industry", "").lower()
                hcity = hnl.get("city", "").lower()
                if cities and hcity and not _city_match(hcity, cities):
                    continue
                if industries and not (
                    _industry_match(hind, industries) or _industry_adjacent(hind, industries)
                ):
                    continue
                class _HNLead:
                    __slots__ = ("company_name", "domain", "industry", "city", "website", "raw")
                    def __init__(self, d: dict[str, Any]):
                        self.company_name = d.get("company_name") or d.get("company")
                        self.domain = d.get("domain", "")
                        self.industry = d.get("industry", "")
                        self.city = d.get("city", "")
                        self.website = d.get("website", "")
                        self.raw = d
                candidates.append(_HNLead(hnl))
                existing_domains.add(hd)
            logger.info("HN Algolia SaaS: added %d candidates for inowix", len(candidates) - len(preferred_city) - len(adjacent_city))
        except Exception as exc:  # noqa: BLE001
            logger.warning("HN Algolia SaaS integration failed: %s", exc)

    if not candidates:
        if tried:
            logger.info("Live discovery: tried set exhausted (%s) — clearing for next wave", len(tried))
            TRIED_DOMAINS_PATH.write_text(
                json.dumps({"updated_at": datetime.now(UTC).isoformat(), "count": 0, "domains": []}, indent=2),
                encoding="utf-8",
            )
            # Also clear YC and HN caches to get fresh data
            global _yc_cache, _yc_cache_ts, _hn_saas_cache, _hn_saas_cache_ts  # noqa: PLW0603
            _yc_cache = None
            _yc_cache_ts = 0.0
            _hn_saas_cache = None
            _hn_saas_cache_ts = 0.0
            for vb in reversed(get_verified_leads()):
                name = vb.company_name or ""
                domain = (vb.domain or "").lower()
                if not domain or _is_mega(name, domain):
                    continue
                if cities and not _city_match(vb.city or "", cities):
                    continue  # still respect city HARD after reset
                ind = (vb.industry or "").lower()
                if industries and not (
                    _industry_match(ind, industries) or _industry_adjacent(ind, industries)
                ):
                    continue
                candidates.append(vb)
                if len(candidates) >= batch_limit:
                    break
        if not candidates:
            return []

    _persist_tried_domains([c.domain for c in candidates if c.domain])
    enriched = await enrich_leads_batch(candidates, batch_size=8, timeout=12.0)
    out: list[dict[str, Any]] = []
    for e in enriched:
        company = e.raw.company_name if e.raw else ""
        domain = (e.raw.domain if e.raw else "") or ""
        # Prefer brand-domain inboxes; skip off-domain / weak franchise desks
        email_candidates = []
        for cand in (e.founder_email, e.email):
            c = (cand or "").strip().lower()
            if c and c not in email_candidates:
                email_candidates.append(c)
        email = ""
        for cand in email_candidates:
            if cand in exclude_emails:
                continue
            if not is_valid_email(cand):
                continue
            if _is_generic_email(cand) or _is_garbage_email(cand):
                continue
            if not _email_matches_brand_domain(cand, domain):
                continue
            if _is_weak_outreach_email(cand) and any(
                _email_matches_brand_domain(x, domain)
                and not _is_weak_outreach_email(x)
                and not _is_generic_email(x)
                for x in email_candidates
                if x
            ):
                continue
            email = cand
            break
        if not email:
            continue
        if _is_mega(company, domain):
            continue
        city = (e.raw.city if e.raw else "") or ""
        # Final city hard gate after enrich (seed city may differ)
        if cities and city and not _city_match(city, cities):
            continue
        why_bits = []
        chat = getattr(e, "chatbot_state", None)
        chat_absent = False
        # COMAI-specific: chatbot/WhatsApp observations
        if product == "comai":
            if chat is not None and "ABSENT" in str(chat).upper():
                why_bits.append("No chatbot automation on site")
                chat_absent = True
            elif chat is not None and "PRESENT" in str(chat).upper():
                why_bits.append("Web chatbot present on site")

            # WhatsApp chat links are ignored. Only note true WA *bot* vendors.
            techs_early = [str(t).lower() for t in (getattr(e, "technologies", None) or []) if t]
            wa_ev = str(getattr(e, "whatsapp_evidence", "") or "").lower()
            has_wa_bot = "whatsapp_bot" in techs_early or (
                "bot" in wa_ev and "PRESENT" in str(getattr(e, "whatsapp_state", "") or "").upper()
            )
            if has_wa_bot:
                why_bits.append("WhatsApp bot/automation vendor detected")
        else:
            techs_early = [str(t).lower() for t in (getattr(e, "technologies", None) or []) if t]

        # Pain points: only for comai (faq_volume, whatsapp_pain, etc.)
        pains = getattr(e, "pain_points", None) or []
        pain_types: list[str] = []
        if product == "comai":
            for p in pains[:5]:
                if isinstance(p, dict):
                    ptype = str(p.get("type") or "")
                    if ptype:
                        pain_types.append(ptype)
                    if ptype == "faq_volume":
                        continue
                    ev = str(p.get("evidence") or ptype)[:80]
                    if ev:
                        why_bits.append(ev)
                else:
                    s = str(p)
                    if "faq" in s.lower() and "whatsapp" not in s.lower():
                        continue
                    why_bits.append(s[:80])

        growth_raw = getattr(e, "growth_signals", None) or []
        growth_signals: list[dict[str, Any]] = [g for g in growth_raw if isinstance(g, dict)]
        buying_raw = getattr(e, "buying_signals", None) or []
        buying_signals: list[dict[str, Any]] = [b for b in buying_raw if isinstance(b, dict)]
        for g in growth_signals[:4]:
            gtype = str(g.get("type") or "")
            gev = str(g.get("evidence") or gtype)[:80]
            if gtype and gev:
                why_bits.append(f"{gtype}: {gev}")
        for b in buying_signals[:3]:
            bev = str(b.get("evidence") or b.get("type") or "")[:80]
            if bev:
                why_bits.append(bev)

        techs_list = getattr(e, "technologies", None) or []
        if isinstance(techs_list, list) and techs_list:
            technologies = [str(t).lower() for t in techs_list if t]
        else:
            technologies = list(techs_early)
        platform = ""
        if getattr(e, "platform", None):
            platform = str(e.platform)
            if platform and platform not in technologies:
                technologies = [platform] + technologies
        elif technologies:
            platform = next((t for t in technologies if t in ("shopify", "woocommerce")), technologies[0])
        if technologies:
            why_bits.append("stack: " + ", ".join(technologies[:6]))

        emp = getattr(e, "employee_count", None)
        size = str(emp) if isinstance(emp, int) and emp > 0 else ""

        # For inowix: add SaaS-specific keywords to why_bits so inowix_signal fires
        # and build product-appropriate hooks for email drafts
        if product == "inowix":
            cat = (getattr(e.raw, "industry", "") or "").lower()
            why_bits.append("saas")
            if any(k in cat for k in ("saas", "software", "tech", "b2b", "enterprise")):
                why_bits.append("engineer")
            if any(t in technologies for t in ("flutter", "react native", "swift", "ios", "android")):
                why_bits.append("mobile")
            if any(t in technologies for t in ("api", "rest", "graphql", "fastapi", "django", "express")):
                why_bits.append("api")
            # Product-appropriate observations for email hooks
            for g in growth_signals[:3]:
                gtype = str(g.get("type") or "")
                if gtype == "hiring":
                    gev = str(g.get("evidence") or "")[:80]
                    why_bits.append(f"hiring: {gev}" if gev else "hiring engineers")
                elif gtype == "funding":
                    why_bits.append("recently funded")
                elif gtype == "new_products":
                    why_bits.append("shipping new product")
            # Note thin bench signals
            if emp and isinstance(emp, int) and emp <= 15:
                why_bits.append("small team likely needs eng capacity")

        founder = _sanitize_founder_name(e.founder_name or "", company)
        # Base intent from growth / chat automation — WhatsApp links ignored
        base_intent = 46.0
        if chat_absent:
            base_intent += 5
        if any(str(g.get("type")) == "hiring" for g in growth_signals):
            base_intent += 5
        if any(str(g.get("type")) == "funding" for g in growth_signals):
            base_intent += 6
        if any(str(g.get("type")) == "advertising" for g in growth_signals):
            base_intent += 4
        if any(str(g.get("type")) in ("expansion", "new_products") for g in growth_signals):
            base_intent += 3
        if founder:
            base_intent += 3
        if _is_weak_outreach_email(email):
            base_intent -= 6
        yf = getattr(e, "year_founded", None)
        if yf is None and e.raw is not None:
            yf = getattr(e.raw, "year_founded", None)
        out.append(
            {
                "company": company,
                "founder_name": founder,
                "founder_role": e.founder_role or ("Founder" if founder else ""),
                "email": email,
                "phone": e.founder_phone or getattr(e, "phone", "") or "",
                "website": e.raw.website if e.raw else "",
                "domain": domain,
                "city": city,
                "category": (e.raw.industry if e.raw else "") or "",
                "size": size,
                "platform": platform,
                "technologies": technologies,
                "pain_types": pain_types,
                "growth_signals": growth_signals,
                "buying_signals": buying_signals,
                "chat_gap": chat_absent,
                "whatsapp_bot": has_wa_bot,
                "why": " · ".join(why_bits) or "Live-enriched Indian D2C contact",
                "signal": "live_discovery",
                "intent_score": min(58.0, base_intent),
                "source": "live_verified_enrichment",
                "company_type": "d2c_brand" if product != "inowix" else "saas_company",
                "enriched": True,
                # Legacy flag kept false — WA chat links no longer demote
                "whatsapp_already": False,
                "weak_outreach_email": _is_weak_outreach_email(email),
                "year_founded": yf if isinstance(yf, int) else None,
            }
        )
    return out


def _persist_sent_emails(extra: set[str] | list[str]) -> None:
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    current = _load_sent_emails()
    current.update(e.lower().strip() for e in extra if e and "@" in e)
    SEEN_PATH.write_text(
        json.dumps(
            {
                "updated_at": datetime.now(UTC).isoformat(),
                "count": len(current),
                "emails": sorted(current),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _persist_last_run_emails(emails: set[str] | list[str]) -> None:
    """Replace (not accumulate) — next run avoids these, later runs can revisit."""
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    cleaned = sorted({e.lower().strip() for e in emails if e and "@" in e})
    LAST_RUN_PATH.write_text(
        json.dumps(
            {
                "updated_at": datetime.now(UTC).isoformat(),
                "count": len(cleaned),
                "emails": cleaned,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _load_last_run_emails() -> set[str]:
    return _load_json_email_set(LAST_RUN_PATH)


# Back-compat aliases
def _load_seen_emails() -> set[str]:
    return _load_sent_emails() | _load_last_run_emails()


def _persist_seen_emails(extra: set[str] | list[str]) -> None:
    _persist_last_run_emails(extra)


def get_job(run_id: str) -> dict[str, Any] | None:
    return _JOBS.get(run_id)


def list_jobs(limit: int = 20) -> list[dict[str, Any]]:
    rows = sorted(_JOBS.values(), key=lambda j: j.get("created_at") or 0, reverse=True)
    return rows[:limit]


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _is_mega(company: str, domain: str) -> bool:
    blob = f"{company} {domain}".lower()
    norm = _norm(blob)
    for x in COMAI_EXCLUDE_SUBSTR:
        xl = x.lower().strip()
        if not xl:
            continue
        # Short tokens need word-ish boundaries to avoid "soch"∈"social"
        if len(xl) <= 4:
            if re.search(rf"(?<![a-z0-9]){re.escape(xl)}(?![a-z0-9])", blob):
                return True
            if _norm(xl) and _norm(xl) in norm and len(_norm(xl)) >= 4:
                # normalized contains only if token long enough after norm
                pass
            continue
        if xl in blob or _norm(xl) in norm:
            return True
    return False


def _known_size_floor(company: str, domain: str) -> int | None:
    keys = (_norm(company),)
    for k, floor in KNOWN_SIZE_FLOOR.items():
        kn = _norm(k)
        if kn and (kn in _norm(company) or kn in _norm(domain)):
            return floor
    for k in keys:
        if k in {_norm(x) for x in KNOWN_SIZE_FLOOR}:
            return KNOWN_SIZE_FLOOR.get(company.lower())  # unused
    return None


def _parse_headcount(size_raw: str) -> tuple[int | None, int | None]:
    """Return (low, high) employee estimate from size strings."""
    t = (size_raw or "").lower().strip()
    if not t:
        return None, None
    if any(w in t for w in ("micro", "solo", "1 person", "bootstrapped founder")):
        return 1, 8
    if "founder-led" in t or "early" in t or "family" in t:
        return 2, 12
    if "small/mid" in t or "small / mid" in t or "small-mid" in t:
        return 12, 40
    if re.search(r"\bsmall\b", t) and "mid" not in t:
        return 5, 18
    if "mid" in t or "medium" in t:
        return 30, 120
    if "large" in t or "enterprise" in t or "mega" in t:
        return 200, 2000
    nums = [int(x) for x in re.findall(r"\d+", t)]
    if not nums:
        return None, None
    if len(nums) == 1:
        return nums[0], nums[0]
    return min(nums[0], nums[1]), max(nums[0], nums[1])


def _estimate_employees(lead: dict[str, Any]) -> tuple[int | None, str]:
    """Best single employee estimate (midpoint) + provenance."""
    size_raw = str(lead.get("size") or lead.get("company_size") or "")
    low, high = _parse_headcount(size_raw)
    if low is not None and high is not None:
        return (low + high) // 2, f"size_field:{size_raw}"
    company = str(lead.get("company") or "")
    domain = str(lead.get("domain") or lead.get("website") or "")
    blob = f"{company} {domain}".lower()
    for k, v in KNOWN_SIZE_FLOOR.items():
        if k in blob or _norm(k) in _norm(company):
            return v, f"known_brand_floor:{v}"
    why = str(lead.get("why") or lead.get("why_intent") or lead.get("signal") or "")
    wlow, whigh = _parse_headcount(why)
    if wlow is not None and whigh is not None:
        return (wlow + whigh) // 2, "why_text"
    return None, "unknown"


def _headcount_ok(est: int, emp_min: int | None, emp_max: int | None, size_raw: str) -> bool:
    """True if estimate fits ICP band."""
    if emp_min is not None and est < int(emp_min):
        return False
    if emp_max is not None and est > int(emp_max):
        return False
    # numeric bands like 10-20 must not sit entirely above emp_max
    low, high = _parse_headcount(size_raw)
    if low is not None and high is not None and emp_max is not None:
        if low > int(emp_max):
            return False
    return True


def _email_local(email: str) -> str:
    return (email or "").split("@", 1)[0].lower().strip()


def _email_host(email: str) -> str:
    if not email or "@" not in email:
        return ""
    return email.split("@", 1)[-1].lower().strip().replace("www.", "")


def _brand_root(domain: str) -> str:
    d = (domain or "").lower().replace("www.", "")
    d = re.sub(r"^https?://", "", d).split("/")[0]
    return d


def _email_matches_brand_domain(email: str, website_or_domain: str) -> bool:
    """True when mailbox belongs to the brand (or freemail founder)."""
    host = _email_host(email)
    if not host:
        return False
    if host in FREEMAIL_HOSTS:
        return True
    brand = _brand_root(website_or_domain)
    if not brand:
        return True  # unknown brand domain — don't hard-kill seed rows
    if host == brand or host.endswith("." + brand):
        return True
    # brand.com vs brand.in / brand.co.in
    b_labels = brand.split(".")
    h_labels = host.split(".")
    if len(b_labels) >= 2 and len(h_labels) >= 2 and b_labels[0] == h_labels[0] and len(b_labels[0]) >= 4:
        return True
    return False


def _is_weak_outreach_email(email: str) -> bool:
    local = _email_local(email)
    return local in WEAK_OUTREACH_LOCALPARTS or any(
        local.startswith(p + "+") or local.startswith(p + ".") for p in WEAK_OUTREACH_LOCALPARTS
    )


def _is_garbage_email(email: str) -> bool:
    """HTML-entity / scrape junk mailboxes."""
    e = (email or "").lower().strip()
    if not e or "@" not in e:
        return True
    local = _email_local(e)
    if "u003e" in e or "u003c" in e or "&lt;" in e or "&gt;" in e or "%3c" in e or "%3e" in e:
        return True
    # Check for decoded angle brackets in local part
    if ">" in local or "<" in local:
        return True
    if local.startswith(("http", "www", "img", "png", "jpg", "css", "js", ".")):
        return True
    if local in {"unknown", "null", "undefined", "n/a", "na", "none", "test", "sample", "email", "user"}:
        return True
    if len(local) > 40:
        return True
    return False


def _is_generic_email(email: str) -> bool:
    """True for unusable mailboxes (noreply / careers / corporate care desks)."""
    local = _email_local(email)
    if not local:
        return True
    if local in HARD_REJECT_LOCALPARTS or local in DESK_REJECT_LOCALPARTS:
        return True
    # Use word-boundary-aware startswith: "hr" should NOT catch "hradmin"
    # Only match "hr", "hr.something", "hr-something", "hr_something"
    if any(local == p or local.startswith(p + ".") or local.startswith(p + "-") or local.startswith(p + "_") for p in HARD_REJECT_LOCALPARTS):
        return True
    if any(local == p or local.startswith(p + ".") or local.startswith(p + "-") or local.startswith(p + "_") for p in DESK_REJECT_LOCALPARTS):
        return True
    host = (email or "").split("@", 1)[-1].lower().strip()
    if any(host == d or host.endswith("." + d) for d in CONGLOMERATE_EMAIL_DOMAINS):
        return True
    # Third-party support platforms (not brand inbox)
    if host in ("gist-apps.com", "zendesk.com", "freshdesk.com"):
        return True
    return False


def _is_soft_generic_email(email: str) -> bool:
    if _is_generic_email(email):
        return False
    local = _email_local(email)
    return local in SOFT_GENERIC_LOCALPARTS or any(
        local.startswith(p + "+") or local.startswith(p + ".") for p in SOFT_GENERIC_LOCALPARTS
    )


def _sanitize_founder_name(name: str, company: str) -> str:
    """Drop historical/brand placeholder founders (e.g. Levi Strauss)."""
    n = (name or "").strip()
    if not n:
        return ""
    low = n.lower()
    company_tokens = [t for t in re.split(r"\W+", (company or "").lower()) if len(t) >= 3]
    # Entire name is just brand tokens
    name_tokens = [t for t in re.split(r"\W+", low) if t]
    if company_tokens and name_tokens and all(
        any(ct in nt or nt in ct for ct in company_tokens) for nt in name_tokens
    ):
        return ""
    placeholders = (
        "levi strauss",
        "unknown",
        "founder",
        "team",
        "admin",
        "support",
        "customer care",
    )
    if low in placeholders:
        return ""
    return n


def _looks_like_agency(company: str, category: str = "", email: str = "") -> bool:
    blob = f"{company} {category} {email}".lower()
    return any(m in blob for m in AGENCY_MARKERS)


def _industry_adjacent(industry: str, wanted: list[str]) -> bool:
    """Same commercial neighborhood (e.g. beauty↔fashion, saas↔devtools) but not an exact ICP hit."""
    if not wanted or not industry:
        return False
    if _industry_match(industry, wanted):
        return False
    families = {
        "beauty": {"beauty", "skincare", "personal care", "cosmetics", "fragrance", "wellness", "ayurveda", "haircare"},
        "skincare": {"beauty", "skincare", "personal care", "cosmetics", "wellness"},
        "fashion": {"fashion", "apparel", "clothing", "lifestyle", "accessories", "footwear", "jewellery", "jewelry"},
        "jewellery": {"jewellery", "jewelry", "fashion", "accessories", "lifestyle"},
        "electronics": {"electronics", "accessories", "gadgets", "wearables", "audio"},
        "food": {"food", "beverage", "snacks", "health", "organic", "fmcg"},
        "home": {"home", "home_decor", "decor", "lifestyle", "furniture"},
        "lifestyle": {"lifestyle", "fashion", "beauty", "home", "fragrance"},
        "d2c": {"d2c", "ecommerce", "retail", "fashion", "beauty", "food", "home"},
        "ecommerce": {"ecommerce", "d2c", "retail", "fashion", "beauty", "food", "home"},
        "retail": {"retail", "ecommerce", "d2c", "fashion", "beauty"},
        "saas": {"saas", "software", "b2b", "enterprise", "cloud", "platform"},
        "developer tools": {"developer tools", "devtools", "dev tools", "infrastructure", "devops", "platform", "api", "open source"},
        "design tools": {"design tools", "design", "ui", "ux", "figma", "creative tools"},
        "software services": {"software services", "consulting", "agency", "digital agency", "tech services"},
        "data tools": {"data tools", "analytics", "business intelligence", "bi", "data platform"},
        "no-code": {"no-code", "nocode", "low-code", "lowcode", "automation", "workflow"},
        "ai": {"ai", "artificial intelligence", "machine learning", "ml", "deep learning", "nlp", "computer vision"},
        "fintech": {"fintech", "payments", "banking", "finance", "insurtech", "wealthtech"},
        "healthtech": {"healthtech", "health tech", "medtech", "digital health", "telemedicine", "health"},
        "edtech": {"edtech", "education", "e-learning", "online learning", "learning platform"},
        "marketplace": {"marketplace", "platform", "network", "community"},
        "productivity": {"productivity", "project management", "collaboration", "workspace", "notes"},
        "cybersecurity": {"cybersecurity", "security", "infosec", "appsec", "devsecops"},
        "climate tech": {"climate tech", "cleantech", "greentech", "sustainability", "carbon"},
    }
    ind = industry.lower()
    wanted_fam: set[str] = set()
    for w in wanted:
        wanted_fam |= families.get(w.lower(), {w.lower()})
    ind_fam: set[str] = set()
    for k, fam in families.items():
        if k in ind or any(x in ind for x in fam):
            ind_fam |= fam
            ind_fam.add(k)
    if not ind_fam:
        ind_fam = {ind}
    return bool(wanted_fam & ind_fam)


def _is_founderish_email(email: str, founder_name: str) -> bool:
    if not email or "@" not in email:
        return False
    if _is_generic_email(email):
        return False
    local = _email_local(email)
    # personal gmail / named localpart
    if email.lower().endswith(("@gmail.com", "@googlemail.com", "@yahoo.com", "@outlook.com")):
        return True
    if founder_name:
        parts = [p for p in re.split(r"\W+", founder_name.lower()) if len(p) >= 3]
        if any(p in local for p in parts):
            return True
    # first.last@ or first@ brand domains
    if "." in local or len(local) <= 12:
        return True
    return not _is_generic_email(email)


def _industry_match(industry: str, wanted: list[str]) -> bool:
    if not wanted:
        return True
    ind = (industry or "").lower().strip()
    if not ind:
        return True  # soft: unknown category kept if other ICP passes
    aliases = {
        "ecommerce": ("ecommerce", "d2c", "retail", "fashion", "beauty", "skincare", "jewellery", "jewelry", "food", "home", "lifestyle", "personal care", "apparel", "cosmetics", "fragrance", "electronics", "accessories", "wellness", "health", "fitness", "pets", "baby", "kids"),
        "retail": ("retail", "ecommerce", "d2c", "fashion", "beauty", "jewellery", "jewelry", "food", "home", "electronics"),
        "d2c": ("d2c", "ecommerce", "fashion", "beauty", "skincare", "jewellery", "jewelry", "food", "home", "lifestyle", "electronics", "apparel"),
        "consumer": ("consumer", "d2c", "beauty", "fashion", "food", "lifestyle", "electronics"),
        "beauty": ("beauty", "skincare", "personal care", "cosmetics", "fragrance", "perfume", "haircare", "wellness", "ayurveda", "makeup"),
        "skincare": ("skincare", "beauty", "personal care", "cosmetics", "ayurveda"),
        "fashion": ("fashion", "apparel", "clothing", "saree", "lifestyle", "jewellery", "jewelry", "accessories"),
        "jewellery": ("jewellery", "jewelry", "jewels", "accessories", "fashion"),
        "jewelry": ("jewellery", "jewelry", "jewels", "accessories", "fashion"),
        "food": ("food", "beverage", "snacks", "millet", "fmcg", "organic"),
        "home": ("home", "home_decor", "decor", "lifestyle", "candles", "furniture"),
        "lifestyle": ("lifestyle", "home", "fragrance", "beauty", "fashion", "wellness"),
        "personal care": ("personal care", "beauty", "skincare", "haircare", "wellness"),
        "electronics": ("electronics", "accessories", "gadgets", "wearables", "tech accessories", "audio", "mobile"),
        "saas": ("saas", "software", "ai", "tech"),
        "software": ("software", "saas", "ai"),
    }
    expanded: set[str] = set()
    for w in wanted:
        expanded.add(w)
        expanded.update(aliases.get(w, ()))
    return any(e in ind or ind in e for e in expanded)


def _city_match(city: str, wanted: list[str]) -> bool:
    if not wanted:
        return True
    c = (city or "").lower().strip()
    # National / unknown HQ: soft-pass when filtering Indian metros
    if not c or c in ("india", "in", "pan-india", "pan india"):
        return True
    aliases = {
        "delhi": ("delhi", "new delhi", "ncr", "gurgaon", "gurugram", "noida", "delhi ncr"),
        "new delhi": ("delhi", "new delhi", "ncr"),
        "bangalore": ("bangalore", "bengaluru"),
        "bengaluru": ("bangalore", "bengaluru"),
        "mumbai": ("mumbai", "bombay", "thane"),
        "hyderabad": ("hyderabad", "secunderabad"),
        "pune": ("pune",),
        "surat": ("surat",),
        "ahmedabad": ("ahmedabad", "amdavad"),
        "chennai": ("chennai", "madras"),
        "kolkata": ("kolkata", "calcutta"),
    }
    for w in wanted:
        wl = w.lower()
        opts = aliases.get(wl, (wl,))
        if any(o in c for o in opts):
            return True
    return False


# Known Indian metro/tier-2 cities — soft-pass even if not in ICP list
_INDIAN_CITIES = {
    "mumbai", "delhi", "new delhi", "ncr", "gurgaon", "gurugram", "noida", "delhi ncr",
    "bangalore", "bengaluru", "hyderabad", "chennai", "pune", "kolkata", "calcutta",
    "ahmedabad", "amdavad", "surat", "jaipur", "lucknow", "chandigarh", "indore",
    "coimbatore", "kochi", "kochi", "bhopal", "nagpur", "visakhapatnam", "vizag",
    "vadodara", "rajkot", "nashik", "thanjavur", "mysore", "mysuru", "goa",
    "patna", "ranchi", "guwahati", "imphal", "shillong", "aizawl", "kohima",
    "dehradun", "haridwar", "udaipur", "jodhpur", "varanasi", "prayagraj",
    "kanpur", "agra", "meerut", "bareilly", "allahabad", "gorakhpur",
    "mangalore", "hubli", "belgaum", "bellary", "tiruchirappalli", "madurai",
    "tirunelveli", "salem", "erode", "thanjavur", "pollachi", "kumbakonam",
    "kakinada", "guntur", "warangal", "nellore", "tirupati", "kurnool",
    "raipur", "bilaspur", "jamshedpur", "ranchi", "dhanbad", "bokaro",
    "siliguri", "darjeeling", "gangtok", "shimla", "manali", "mussoorie",
}


def _is_indian_city(city_lower: str) -> bool:
    """Check if a city name looks like an Indian city (metro or tier-2/3)."""
    if not city_lower:
        return False
    c = city_lower.strip()
    # Exact match
    if c in _INDIAN_CITIES:
        return True
    # Partial match — "sector 5 gurugram" etc.
    for ic in _INDIAN_CITIES:
        if ic in c or c in ic:
            return True
    # Indian state suffixes / patterns
    if any(c.endswith(s) for s in ("pur", "garh", "abad", "nagar", "ganj", "dham", "patnam")):
        return True
    return False


def _parse_year_founded(lead: dict[str, Any]) -> int | None:
    """Best-effort founded year from lead fields (never invent)."""
    for key in ("year_founded", "founded_year", "founded", "founding_year"):
        raw = lead.get(key)
        if raw is None or raw == "":
            continue
        try:
            y = int(float(str(raw).strip()[:4]))
            if 1800 <= y <= 2100:
                return y
        except (TypeError, ValueError):
            pass
    blob = " ".join(
        str(lead.get(k) or "")
        for k in ("why", "signal", "size", "description")
    )
    m = re.search(r"\b(19|20)\d{2}\b", blob)
    if m:
        y = int(m.group(0))
        if 1990 <= y <= 2030:
            return y
    return None


def apply_icp_filters(
    leads: list[dict[str, Any]],
    icp: dict[str, Any],
    product: str,
    *,
    prefer_founder: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, int]]:
    """ICP-strict filter with adjacent tier for volume.

    HARD reject: mega, wrong country, clear industry miss (non-adjacent),
    clear city miss when HQ cities selected, year founded outside band,
    agency when D2C required, headcount far outside band, unusable email.
    SOFT flag (kept): blank city under HQ filter, soft-generic inbox,
    adjacent industry, unknown size/year default.
    Returns: (kept, hard_rejects, soft_flags).
    """
    industries = [
        str(x).lower()
        for x in list(icp.get("industries") or []) + list(icp.get("specialties") or [])
    ]
    industries = list(dict.fromkeys(industries))
    cities = [str(x).lower() for x in (icp.get("headquarters_cities") or [])]
    countries = [str(x).lower() for x in (icp.get("countries") or [])]
    tech = [str(x).lower() for x in (icp.get("technology_stack") or [])]
    domains = [
        str(x).lower().replace("https://", "").replace("http://", "").strip("/")
        for x in (icp.get("domains") or [])
    ]
    name_contains = [str(x).lower() for x in (icp.get("company_name_contains") or [])]
    emp_min = icp.get("employee_count_min")
    if emp_min is None:
        emp_min = icp.get("company_size_min")
    emp_max = icp.get("employee_count_max")
    if emp_max is None:
        emp_max = icp.get("company_size_max")
    yf_min = icp.get("year_founded_min")
    yf_max = icp.get("year_founded_max")
    types = [str(x).lower() for x in (icp.get("company_types") or [])]
    linkedin_pref = bool(icp.get("linkedin_url_required"))
    prefer_founder_soft = prefer_founder or linkedin_pref or product == "comai"
    want_d2c = any("d2c" in t for t in types) or product == "comai"

    rejects: dict[str, int] = {
        "mega_brand": 0,
        "headcount": 0,
        "unknown_size": 0,
        "industry": 0,
        "city": 0,
        "country": 0,
        "domain": 0,
        "name": 0,
        "type": 0,
        "agency": 0,
        "generic_email": 0,
        "no_email": 0,
        "no_founder": 0,
        "tech": 0,
        "year_founded": 0,
        "already_seen": 0,
        "already_sent": 0,
        "prior_run": 0,
        "low_intent": 0,
    }
    soft_flags: dict[str, int] = {
        "industry_adjacent": 0,
        "city_unknown": 0,
        "year_unknown": 0,
        "soft_generic_email": 0,
        "headcount_soft": 0,
    }

    out: list[dict[str, Any]] = []
    for lead in leads:
        company = str(lead.get("company") or lead.get("company_name") or "")
        domain = str(lead.get("domain") or lead.get("website") or "").lower()
        industry = str(lead.get("category") or lead.get("industry") or "").lower()
        city = str(lead.get("city") or lead.get("hq") or "")
        country = str(lead.get("country") or "").lower()
        platform = str(lead.get("platform") or "").lower()
        email = (lead.get("email") or lead.get("to_email") or "").strip().lower()
        founder = _sanitize_founder_name(str(lead.get("founder_name") or ""), company)
        lead["founder_name"] = founder

        # Reset per-lead soft flags if object reused
        for k in (
            "industry_soft_miss",
            "industry_adjacent",
            "city_soft_miss",
            "type_soft_miss",
            "headcount_soft_miss",
            "soft_generic_email",
            "weak_outreach_email",
            "off_domain_email",
            "named_founder",
            "icp_tier",
            "whatsapp_already",
            "year_founded_soft_miss",
        ):
            lead.pop(k, None)

        if product == "comai" and _is_mega(company, domain):
            rejects["mega_brand"] += 1
            continue

        if domains and not any(d in domain for d in domains):
            rejects["domain"] += 1
            continue
        if name_contains and not any(n in company.lower() for n in name_contains):
            rejects["name"] += 1
            continue

        # Industry — HARD on clear miss; ADJACENT kept for volume tier
        if industries and industry:
            if _industry_match(industry, industries):
                lead["icp_tier"] = "core"
            elif _industry_adjacent(industry, industries):
                lead["industry_adjacent"] = True
                lead["icp_tier"] = "adjacent"
                soft_flags["industry_adjacent"] += 1
            else:
                rejects["industry"] += 1
                continue
        elif industries and not industry:
            lead["industry_adjacent"] = True
            lead["icp_tier"] = "unknown_category"
            soft_flags["industry_adjacent"] += 1
        else:
            lead["icp_tier"] = "core"

        # City — SOFT-pass for any Indian city; HARD only for non-Indian metros.
        # Indian metros not in ICP list should still get through for volume.
        if cities:
            c_norm = (city or "").lower().strip()
            if not c_norm or c_norm in ("india", "in", "pan-india", "pan india"):
                soft_flags["city_unknown"] += 1
            elif _city_match(city, cities):
                pass  # exact match, no flag
            elif _is_indian_city(c_norm):
                # Indian city but not in ICP list — soft-pass for volume
                lead["city_soft_miss"] = True
                soft_flags["city_unknown"] += 1
            else:
                rejects["city"] += 1
                continue

        if countries and country and not any(c in country for c in countries):
            rejects["country"] += 1
            continue

        # Year founded — HARD when known and outside band; unknown soft-kept
        if yf_min is not None or yf_max is not None:
            yf = _parse_year_founded(lead)
            if yf is not None:
                lead["year_founded"] = yf
                if yf_min is not None and yf < int(yf_min):
                    rejects["year_founded"] += 1
                    continue
                if yf_max is not None and yf > int(yf_max):
                    rejects["year_founded"] += 1
                    continue
            else:
                soft_flags["year_unknown"] += 1
                lead["year_founded_soft_miss"] = True

        # Type / agency — HARD when D2C required (but allow agencies if ICP includes them)
        ctype = str(lead.get("company_type") or lead.get("lane") or "d2c_brand").lower()
        if "saas" in ctype or lead.get("lane") == "INOWIX":
            ctype = "saas_product"
        elif "partner" in ctype or "agency" in ctype:
            ctype = "agency_partner"
        else:
            ctype = "d2c_brand" if "d2c" in ctype or ctype in ("", "comai_direct") else ctype

        # Only reject agencies if ICP doesn't include agency_partner type
        agency_in_types = any("agency" in t or "partner" in t for t in types)
        if want_d2c and not agency_in_types and (_looks_like_agency(company, industry, email) or ctype == "agency_partner"):
            rejects["agency"] += 1
            continue
        if types and not any(t in ctype for t in types):
            if ctype == "saas_product" and want_d2c:
                rejects["type"] += 1
                continue
            lead["type_soft_miss"] = True

        if tech:
            why = str(lead.get("why") or "").lower()
            blob = f"{platform} {why}"
            lead["tech_match"] = any(t.replace(" ", "") in blob.replace(" ", "") for t in tech)

        # Headcount — default unknown to ICP midpoint; HARD if clearly oversized
        if emp_min is not None or emp_max is not None:
            est, provenance = _estimate_employees(lead)
            if est is None and not _is_mega(company, domain):
                lo = int(emp_min or 5)
                hi = int(emp_max or 40)
                est = max(lo, min(hi, (lo + hi) // 2))
                provenance = "icp_midpoint_default"
            lead["employee_estimate"] = est
            lead["employee_estimate_source"] = provenance
            if est is None:
                rejects["unknown_size"] += 1
                continue
            size_raw = str(lead.get("size") or "")
            emax = int(emp_max) if emp_max is not None else None
            emin = int(emp_min) if emp_min is not None else None
            if emax is not None and est > int(emax * 1.5):
                rejects["headcount"] += 1
                continue
            if emin is not None and est < max(1, int(emin * 0.5)):
                rejects["headcount"] += 1
                continue
            if emax is not None and est > emax:
                lead["headcount_soft_miss"] = True
                soft_flags["headcount_soft"] += 1
            if emin is not None and est < emin:
                lead["headcount_soft_miss"] = True
                soft_flags["headcount_soft"] += 1
            if size_raw and not _headcount_ok(est, emin, emax, size_raw):
                low, high = _parse_headcount(size_raw)
                if low is not None and emax is not None and low > emax:
                    rejects["headcount"] += 1
                    continue
                lead["headcount_soft_miss"] = True
                soft_flags["headcount_soft"] += 1

        if not email or "@" not in email:
            rejects["no_email"] += 1
            continue
        if email.endswith("@example.com") or _is_generic_email(email) or _is_garbage_email(email):
            rejects["generic_email"] += 1
            continue
        # Off-domain mailbox (Caprese→vipbags) — hard reject for outreach quality
        if not _email_matches_brand_domain(email, domain or str(lead.get("website") or "")):
            lead["off_domain_email"] = True
            rejects["generic_email"] += 1
            continue
        if _is_weak_outreach_email(email):
            lead["weak_outreach_email"] = True

        if prefer_founder_soft:
            if _is_soft_generic_email(email):
                lead["soft_generic_email"] = True
                soft_flags["soft_generic_email"] += 1
            if founder:
                lead["named_founder"] = True

        lead["email"] = email
        lead["to_email"] = email
        out.append(lead)

    return out, rejects, soft_flags


# Back-compat name
def _apply_icp_filters(leads: list[dict[str, Any]], icp: dict[str, Any], product: str) -> list[dict[str, Any]]:
    kept, _, _ = apply_icp_filters(leads, icp, product)
    return kept


def _row_to_lead(r: dict[str, Any], source: str) -> dict[str, Any]:
    return {
        "company": r.get("company") or r.get("company_name") or r.get("brand") or "",
        "founder_name": r.get("founder_name") or r.get("founder") or "",
        "founder_role": r.get("founder_role") or "Founder",
        "email": r.get("email") or r.get("to_email") or "",
        "phone": r.get("phone") or "",
        "website": r.get("website") or "",
        "domain": (r.get("website") or r.get("domain") or "").lower(),
        "city": r.get("city") or r.get("hq") or "",
        "category": r.get("category") or r.get("industry") or "",
        "size": r.get("size") or r.get("company_size") or "",
        "platform": r.get("platform") or "",
        "why": r.get("why") or r.get("why_pitchable") or r.get("why_intent") or r.get("signal") or "",
        "signal": r.get("signal") or "",
        "intent_score": float(
            r.get("intent_score") or r.get("pitch_score") or r.get("buyability_score") or 0 or 0
        ),
        "source": source,
        "company_type": r.get("company_type") or ("saas_product" if "inowix" in source else "d2c_brand"),
        "lane": r.get("lane") or "",
    }


def _load_csv_leads(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    try:
        if path.suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            rows = data if isinstance(data, list) else data.get("leads") or data.get("results") or []
            for r in rows:
                if isinstance(r, dict):
                    out.append(_row_to_lead(r, path.name))
        else:
            with path.open(encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    out.append(_row_to_lead(r, path.name))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed loading %s: %s", path, exc)
    return out


def _extract_cybersecurity_leads(icp: dict[str, Any]) -> list[dict[str, Any]]:
    """Load cybersecurity leads from exports and map to LeadEngineLead format."""
    cyb_exports = ROOT / "exports" / "cybersecurity"
    paths = [
        cyb_exports / "cybersecurity_sales_ready.json",
        cyb_exports / "cybersecurity_outreach_queue.json",
    ]
    # Also glob any additional cybersecurity JSON files
    if cyb_exports.exists():
        for extra in sorted(cyb_exports.glob("*.json")):
            if extra not in paths and "rejected" not in extra.name and "evidence_audit" not in extra.name:
                paths.append(extra)

    leads: list[dict[str, Any]] = []
    seen_emails: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rows = data if isinstance(data, list) else data.get("leads") or []
            for r in rows:
                if not isinstance(r, dict):
                    continue
                # Nested structure: company is an object, contact is an object
                company_obj = r.get("company") or {}
                if isinstance(company_obj, str):
                    company_obj = {"name": company_obj}
                contact = r.get("contact") or {}
                if isinstance(contact, str):
                    contact = {"name": contact}
                email = contact.get("email") or r.get("email") or ""
                if not email or "@" not in email:
                    continue
                email = email.lower().strip()
                if email in seen_emails:
                    continue
                seen_emails.add(email)
                company_name = company_obj.get("name") or r.get("company") or ""
                domain = company_obj.get("url") or r.get("domain") or ""
                if domain and not domain.startswith("http"):
                    domain = "https://" + domain
                services = r.get("services_needed") or []
                if isinstance(services, list) and services:
                    service_str = ", ".join(services[:5])
                else:
                    service_str = str(services) if services else ""
                ev_conf = (r.get("evidence_confidence") or "").upper()
                score_map = {"HIGH": 85, "MEDIUM": 65, "LOW": 45}
                intent_score = score_map.get(ev_conf, 50)
                verdict = (r.get("final_verdict") or r.get("verdict") or "").upper()
                grade = "SALES_READY" if verdict == "SALES_READY" else "QUALIFIED" if verdict == "QUALIFIED" else "NURTURE"
                why_bits = []
                be = r.get("buying_event") or {}
                if isinstance(be, dict):
                    if be.get("description"):
                        why_bits.append(be["description"][:120])
                    if be.get("services_needed"):
                        svc = be["services_needed"]
                        if isinstance(svc, list):
                            why_bits.append(f"Services: {', '.join(svc[:3])}")
                ev_chain = r.get("evidence_chain") or r.get("evidence") or []
                if isinstance(ev_chain, list):
                    for ev in ev_chain[:3]:
                        if isinstance(ev, dict) and ev.get("snippet"):
                            why_bits.append(ev["snippet"][:100])
                leads.append({
                    "company": company_name,
                    "founder_name": contact.get("name") or "",
                    "founder_role": contact.get("title") or contact.get("role") or "",
                    "email": email,
                    "phone": contact.get("phone") or "",
                    "website": domain,
                    "domain": re.sub(r"^https?://(www\.)?", "", domain).split("/")[0].lower(),
                    "city": company_obj.get("city") or r.get("city") or "",
                    "category": company_obj.get("industry") or r.get("industry") or "Cybersecurity",
                    "size": str(company_obj.get("company_size") or company_obj.get("employee_count") or ""),
                    "platform": "",
                    "why": " · ".join(why_bits) or f"Cybersecurity lead: {service_str}",
                    "signal": verdict or "cybersecurity_verified",
                    "intent_score": float(intent_score),
                    "source": "cybersecurity_engine",
                    "company_type": "saas_product",
                    "icp_tier": "core",
                })
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed loading cybersecurity leads from %s: %s", path, exc)
    return leads


def _extract_leads(product: str, icp: dict[str, Any]) -> list[dict[str, Any]]:
    """Parameter-driven extraction: founder-quality seeds first, then wave CSVs.

    Dual-lane mega/generic master is last and will usually fail hard ICP.
    Also merges verified-brand discovery domains that match industry/city,
    attaching contacts only when we already have a verified email in seeds.
    """
    if product == "cybersecurity":
        return _extract_cybersecurity_leads(icp)
    if product == "comai":
        paths = [
            ROOT / "exports" / "comai_icp_founder_leads.csv",
            ROOT / "exports" / "comai_icp_wave2_leads.csv",
            ROOT / "exports" / "comai_all_collected_leads_master.csv",
            ROOT / "exports" / "comai_buyability_results.json",
            ROOT / "exports" / "dual_lane_fresh_leads_master.csv",
            ROOT / "exports" / "dual_lane_fresh_leads_enriched.csv",
            ROOT / "exports" / "dual_lane_pending_queue.csv",
            ROOT / "exports" / "kochi_mfr_distributor_leads_final.csv",
        ]
        # Extra intent exports / reports with contact rows
        for extra in sorted((ROOT / "exports").glob("comai*.csv")):
            if extra not in paths:
                paths.append(extra)
        for extra in sorted((ROOT / "exports").glob("*buyability*.json")):
            if extra not in paths:
                paths.append(extra)
        for extra in sorted((ROOT / "exports").glob("*fresh*leads*.csv")):
            if extra not in paths:
                paths.append(extra)
        # Prior engine runs — skip (often polluted with mega Soft stamps); use clean exports + live only
        # (kept intentionally empty for quality)
    else:
        paths = [
            ROOT / "exports" / "inowix_high_intent_pitchable.csv",
            ROOT / "exports" / "inowix_saas_fresh_opportunities.csv",
        ]
        for extra in sorted((ROOT / "exports").glob("inowix*.csv")):
            if extra not in paths:
                paths.append(extra)
        # skip prior lead_engine_runs for quality

    seeds: list[dict[str, Any]] = []
    for path in paths:
        seeds.extend(_load_csv_leads(path))

    # Discover additional brand shells from verified list matching ICP (no invented emails)
    try:
        if product == "inowix":
            from packages.qualification_engine.saas_verified_brands import get_saas_verified_leads as get_verified_leads
        else:
            from packages.qualification_engine.verified_brands import get_verified_leads

        industries = [str(x).lower() for x in (icp.get("industries") or icp.get("specialties") or [])]
        cities = [str(x).lower() for x in (icp.get("headquarters_cities") or [])]
        by_domain = {
            re.sub(r"^https?://(www\.)?", "", (s.get("website") or "").lower()).strip("/"): s for s in seeds
        }
        for vb in get_verified_leads():
            name = vb.company_name
            domain = (vb.domain or "").lower()
            if product == "comai" and _is_mega(name, domain):
                continue
            if industries and not _industry_match((vb.industry or "").lower(), industries):
                continue
            if cities and not _city_match(vb.city or "", cities):
                continue
            # only surface if we already have a contact seed for this domain
            key = domain
            if key in by_domain:
                continue  # already have
            # skip shells without contacts — never invent
    except Exception as exc:  # noqa: BLE001
        logger.debug("Verified discovery merge skipped: %s", exc)

    return seeds


def _load_seed_leads(product: str) -> list[dict[str, Any]]:
    return _extract_leads(product, {})


def _dedupe(leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dedupe by email; prefer founderish + higher intent + has size."""
    best: dict[str, dict[str, Any]] = {}
    for lead in leads:
        email = (lead.get("email") or lead.get("to_email") or "").lower().strip()
        if not email:
            continue
        lead["email"] = email
        lead["to_email"] = email
        lead["id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, email))
        score = float(lead.get("intent_score") or 0)
        if _is_founderish_email(email, str(lead.get("founder_name") or "")):
            score += 20
        if lead.get("founder_name"):
            score += 10
        if lead.get("size"):
            score += 5
        if lead.get("source") == "live_verified_enrichment":
            score += 35  # prefer fresh structured intent over stale CSV
        if lead.get("growth_signals") or lead.get("technologies"):
            score += 8
        lead["_dedupe_rank"] = score
        prev = best.get(email)
        if not prev or score > float(prev.get("_dedupe_rank") or 0):
            best[email] = lead
    return list(best.values())


def _strong_comai_signals(lead: dict[str, Any], product: str) -> list[str]:
    """Strong pitch signals only — FAQ volume alone never qualifies.

    Intelligence rules:
    - WhatsApp *chat links* are ignored (not a bot / not a buy gate)
    - Primary gaps: missing chatbot automation, ops pain, growth+ads without CX stack
    - Prefer structured growth/tech/pain fields over fragile why-text alone
    """
    why = str(lead.get("why") or lead.get("signal") or "").lower()
    platform = str(lead.get("platform") or "").lower()
    email = str(lead.get("email") or "")
    founder = str(lead.get("founder_name") or lead.get("named_founder") or "").strip()
    local = _email_local(email)
    out: list[str] = []

    techs = {
        str(t).lower()
        for t in (lead.get("technologies") or [])
        if t
    }
    if platform:
        techs.add(platform)
    for part in re.split(r"[,|/]", platform):
        if part.strip():
            techs.add(part.strip().lower())

    growth = lead.get("growth_signals") or []
    growth_types = {
        str(g.get("type") or "").lower()
        for g in growth
        if isinstance(g, dict)
    }
    buying = lead.get("buying_signals") or []
    buying_types = {
        str(b.get("type") or "").lower()
        for b in buying
        if isinstance(b, dict)
    }
    pain_types = {
        str(p).lower()
        for p in (lead.get("pain_types") or [])
        if p
    }
    for p in lead.get("pain_points") or []:
        if isinstance(p, dict) and p.get("type"):
            pain_types.add(str(p.get("type")).lower())

    # Ignore legacy WA chat-link flags entirely for ranking
    lead["whatsapp_already"] = False

    chat_absent = bool(lead.get("chat_gap")) or "no chatbot" in why or (
        "chatbot" in why and "absent" in why
    ) or "without chatbot" in why or "no chatbot automation" in why
    if chat_absent:
        out.append("chat_gap")

    if "hiring" in growth_types or "cx_hiring" in growth_types:
        out.append("hiring_intent")
    if (
        "cx_hiring" in growth_types
        or any(k in why for k in ("sla", "slow support"))
        or re.search(r"\b(24|48)\s*(h|hr|hrs|hour|hours)\b", why)
    ):
        out.append("slow_support_sla")

    if "funding" in growth_types or "recent_funding_window" in buying_types:
        out.append("funding_intent")

    if "expansion" in growth_types or "new_products" in growth_types:
        out.append("growth_motion")

    if "advertising" in growth_types or techs & {"meta_pixel", "google_ads", "gtm"}:
        out.append("ads_active")

    if techs & {"shiprocket", "razorpay", "klaviyo", "judgeme", "yotpo"}:
        out.append("ops_stack")

    if lead.get("whatsapp_bot") or "whatsapp_bot" in techs:
        out.append("whatsapp_bot_present")  # soft evidence only — not a gate

    ops_pain_hit = bool(
        pain_types & {"return_policy", "shipping_info", "cod_available"}
        or "ops_support_gap" in buying_types
        or (
            re.search(r"\b(returns?|refunds?|cod|return_policy)\b", why)
            and (
                re.search(r"\b(customer\s*support|support\s*team|support\s*sla)\b", why)
                or chat_absent
            )
        )
    )
    if ops_pain_hit:
        out.append("ops_pain")

    has_commerce = bool(
        product == "comai"
        and (
            any(k in why or k in platform for k in ("shopify", "woocommerce"))
            or "shopify" in techs
            or "woocommerce" in techs
            or lead.get("tech_match")
        )
    )
    if has_commerce:
        if chat_absent or "slow_support_sla" in out or "hiring_intent" in out or "ops_pain" in out:
            out.append("stack_plus_gap")
        else:
            out.append("commerce_stack")

    if ("ads_active" in out and chat_absent and has_commerce) or (
        "automation_gap_on_ads_brand" in buying_types
    ):
        out.append("ads_plus_automation_gap")

    if (
        ("hiring_intent" in out or "funding_intent" in out or "growth_motion" in out or "ads_active" in out)
        and (chat_absent or "ops_pain" in out)
    ):
        out.append("high_intent_composite")

    if product == "inowix" and any(k in why for k in ("engineer", "flutter", "ios", "saas", "api")):
        out.append("inowix_signal")

    if founder and _is_founderish_email(email, founder):
        out.append("founder_reachable")
    elif founder and not _is_soft_generic_email(email) and not _is_generic_email(email) and not _is_weak_outreach_email(email):
        out.append("named_founder_inbox")
    elif founder and local in ("hello", "hi", "care", "wecare", "contact", "info", "support", "help"):
        out.append("named_founder_brand_inbox")

    if local in ("hello", "hi", "care", "wecare", "contact", "info") and not _is_generic_email(email):
        out.append("brand_inbox")
        if founder or lead.get("phone") or "shopify" in platform or "woocommerce" in platform or "shopify" in techs:
            out.append("brand_inbox_plus_cue")

    if local in ("support", "help") and not _is_generic_email(email):
        if founder or lead.get("phone") or lead.get("tech_match") or "shopify" in platform or "shopify" in techs:
            out.append("brand_support_plus_cue")

    if lead.get("phone") and (founder or chat_absent or local in ("hello", "care", "info")):
        out.append("phone_plus_context")

    if lead.get("source") == "live_verified_enrichment" and (
        chat_absent or founder or "hiring_intent" in out or "funding_intent" in out or "ads_active" in out
    ):
        out.append("live_gap_corroborated")

    return list(dict.fromkeys(out))


def _signal_families(strong: list[str]) -> set[str]:
    """Collapse overlapping signals into intelligence families for grade gates."""
    mapping = {
        "gap": {
            "chat_gap",
            "stack_plus_gap",
            "slow_support_sla",
            "ops_pain",
            "ads_plus_automation_gap",
            "high_intent_composite",
        },
        "reach": {
            "founder_reachable",
            "named_founder_inbox",
            "named_founder_brand_inbox",
            "brand_inbox",
            "brand_inbox_plus_cue",
            "brand_support_plus_cue",
            "phone_plus_context",
        },
        "stack": {
            "commerce_stack",
            "stack_plus_gap",
            "ads_active",
            "ops_stack",
            "ads_plus_automation_gap",
        },
        "growth": {
            "hiring_intent",
            "funding_intent",
            "ads_active",
            "growth_motion",
            "high_intent_composite",
        },
        "product": {"inowix_signal"},
        "live": {"live_gap_corroborated"},
    }
    fams: set[str] = set()
    sset = set(strong)
    for fam, members in mapping.items():
        if sset & members:
            fams.add(fam)
    return fams


def _intent_signal_count(lead: dict[str, Any], product: str) -> int:
    """Strong signals only — no FAQ, no circular intent_score, no live-source freebie."""
    return len(_strong_comai_signals(lead, product))


def _score_leads(leads: list[dict[str, Any]], product: str) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for lead in leads:
        company = str(lead.get("company") or "")
        lead["founder_name"] = _sanitize_founder_name(str(lead.get("founder_name") or ""), company)

        base = float(lead.get("intent_score") or 0)
        # Cap inherited inflated bases from old runs / live stamps
        if product != "inowix" and base > 55:
            base = 45.0
        score = base if base > 0 else 38.0
        why = str(lead.get("why") or lead.get("signal") or "").lower()

        # Cybersecurity-specific scoring
        if product == "cybersecurity":
            strong: list[str] = []
            families: set[str] = set()
            if "SALES_READY" in str(lead.get("signal") or "").upper():
                strong.append("verified_buying_event")
                families.add("gap")
                score = max(score, 80.0)
            elif "QUALIFIED" in str(lead.get("signal") or "").upper():
                strong.append("verified_pain")
                families.add("gap")
                score = max(score, 68.0)
            if lead.get("email") and lead.get("founder_name"):
                strong.append("founder_reachable")
                families.add("reach")
                score += 8
            elif lead.get("email"):
                strong.append("contact_verified")
                families.add("reach")
                score += 4
            if any(k in why for k in ("penetration testing", "vapt", "security audit", "compliance")):
                strong.append("service_match")
                families.add("gap")
                score += 6
            if lead.get("category") and any(
                k in str(lead.get("category")).lower()
                for k in ("saas", "fintech", "healthtech", "ecommerce")
            ):
                strong.append("icp_core")
                score += 5
            lead["intent_signals"] = len(strong)
            lead["strong_signals"] = strong
            lead["signal_families"] = sorted(families)
            family_count = len(families)
            score = min(95.0, max(0.0, score))
            sales_ready = score >= 75 and family_count >= 2 and strong
            qualified = score >= 60 and strong
            grade = "SALES_READY" if sales_ready else "QUALIFIED" if qualified else "NURTURE"
            lead["intent_score"] = round(score, 1)
            lead["grade"] = grade
            lead["evidence"] = [
                x for x in [
                    f"source:{lead.get('source', 'cybersecurity_engine')}",
                    lead.get("category") and f"industry:{lead.get('category')}",
                    *[s for s in strong],
                    f"families:{','.join(sorted(families))}" if families else "",
                ]
                if x
            ]
            scored.append(lead)
            continue
        strong = _strong_comai_signals(lead, product)
        families = _signal_families(strong)
        lead["intent_signals"] = len(strong)
        lead["strong_signals"] = strong
        lead["signal_families"] = sorted(families)

        # Family-aware boosts — chatbot/ops/growth first; WhatsApp links ignored
        gap_boost = 0
        if "chat_gap" in strong:
            gap_boost += 10
        if "slow_support_sla" in strong:
            gap_boost += 6
        if "ops_pain" in strong:
            gap_boost += 6
        if "high_intent_composite" in strong:
            gap_boost += 8
        score += min(22, gap_boost)

        if "stack_plus_gap" in strong:
            score += 7
        elif "commerce_stack" in strong:
            score += 4

        if "hiring_intent" in strong:
            score += 10
        if "funding_intent" in strong:
            score += 11
        # Combined growth signal: hiring + funding together is strongest intent
        if "hiring_intent" in strong and "funding_intent" in strong:
            score += 8
        # Growth recency: multiple growth signals indicate active company
        growth_count = sum(1 for s in strong if s in ("hiring_intent", "funding_intent", "growth_motion", "ads_active"))
        if growth_count >= 3:
            score += 6
        elif growth_count >= 2:
            score += 3
        if "growth_motion" in strong:
            score += 5
        if "ads_plus_automation_gap" in strong:
            score += 9
        elif "ads_active" in strong:
            score += 5
        if "ops_stack" in strong and ("chat_gap" in strong or "ops_pain" in strong):
            score += 4

        if "founder_reachable" in strong:
            score += 12
        elif "named_founder_inbox" in strong:
            score += 6
        elif "named_founder_brand_inbox" in strong:
            score += 5
        if "brand_inbox_plus_cue" in strong:
            score += 5
        elif "brand_inbox" in strong:
            score += 4
        if "brand_support_plus_cue" in strong:
            score += 3
        if "live_gap_corroborated" in strong:
            score += 2
        if "phone_plus_context" in strong:
            score += 3
        if "inowix_signal" in strong:
            score += 8
        # YC batch signal: recent batches get higher boost
        if lead.get("yc_batch"):
            batch = str(lead["yc_batch"])
            # Extract year from batch (e.g., "W23" -> 2023, "S24" -> 2024)
            try:
                batch_year = 2000 + int(batch[-2:]) if len(batch) >= 2 else 0
                if batch_year >= 2022:
                    score += 15  # Recent YC batch
                elif batch_year >= 2020:
                    score += 10  # Somewhat recent
                else:
                    score += 5   # Older batch
            except (ValueError, IndexError):
                score += 5
        # YC hiring signal: companies actively hiring get extra boost
        if lead.get("yc_is_hiring"):
            score += 10

        soft_penalty = 8
        if "brand_inbox" in strong or "brand_inbox_plus_cue" in strong:
            soft_penalty = 3
        # For Inowix: relax generic email penalty — these are usable contacts
        if product == "inowix" and lead.get("soft_generic_email"):
            soft_penalty = 2

        if "faq" in why:
            score += 1

        if lead.get("icp_tier") == "core":
            score += 5
        elif lead.get("industry_adjacent"):
            score -= 10
        if lead.get("city_soft_miss"):
            score -= 2
        if lead.get("soft_generic_email"):
            score -= soft_penalty
        if lead.get("weak_outreach_email"):
            score -= 8
        if lead.get("headcount_soft_miss"):
            score -= 6
        if lead.get("type_soft_miss"):
            score -= 8
        # WhatsApp chat links intentionally ignored — no demotion

        faq_only = (not strong) and ("faq" in why or not why.strip())
        if faq_only or (lead.get("soft_generic_email") and not strong):
            score = min(score, 52.0)
        if lead.get("weak_outreach_email"):
            score = min(score, 65.0)

        if not strong:
            score = min(score, 54.0)

        # Need gap + reach (or gap + stack/growth) for top grades — not inbox-only stacks
        family_count = len(families - {"live"})
        score = min(88.0, max(0.0, score))
        if family_count >= 2 and "gap" in families and score >= 72:
            score = min(94.0, score + 4)
        if family_count >= 3 and score >= 80:
            score = min(96.0, score + 2)
        # Growth + gap is premium "why now" — allow ceiling bump
        if "growth" in families and "gap" in families and score >= 78:
            score = min(96.0, score + 2)

        sales_ready = (
            score >= 72
            and strong
            and family_count >= 2
            and (
                "gap" in families
                or "growth" in families
                or "founder_reachable" in strong
            )
            and not lead.get("weak_outreach_email")
        )
        qualified = score >= 58 and strong and not lead.get("weak_outreach_email")
        # Volume leads: have contact info + decent score but no strong signals
        _has_email = bool(lead.get("email"))
        volume = (
            not sales_ready
            and not qualified
            and _has_email
            and score >= 35
            and lead.get("icp_tier") == "core"
        )
        grade = "SALES_READY" if sales_ready else "QUALIFIED" if qualified else "VOLUME" if volume else "NURTURE"
        lead["intent_score"] = round(score, 1)
        lead["grade"] = grade
        est = lead.get("employee_estimate")
        lead["evidence"] = [
            x
            for x in [
                lead.get("phone") and f"phone:{lead.get('phone')}",
                est and f"emp~{est}",
                *[s for s in strong],
                f"families:{','.join(sorted(families))}" if families else "",
                lead.get("platform") and f"platform:{lead.get('platform')}",
                lead.get("soft_generic_email") and "soft_generic_inbox",
                lead.get("weak_outreach_email") and "weak_outreach_inbox",
                lead.get("whatsapp_already") and "whatsapp_already_present",
                lead.get("industry_adjacent") and "industry_adjacent",
                lead.get("icp_tier") == "core" and "icp_core",
                faq_only and "faq_weak_only",
            ]
            if x
        ]
        scored.append(lead)

    scored.sort(
        key=lambda x: (
            0 if x.get("icp_tier") == "core" else 1 if x.get("industry_adjacent") else 2,
            0 if "growth" in set(x.get("signal_families") or []) else 1,
            0 if "gap" in set(x.get("signal_families") or []) else 1,
            1 if x.get("weak_outreach_email") else 0,
            -len(x.get("signal_families") or []),
            -int(x.get("intent_signals") or 0),
            -float(x.get("intent_score") or 0),
            1 if x.get("soft_generic_email") else 0,
        )
    )
    return scored


def _select_volume_icp_intent(
    scored: list[dict[str, Any]],
    *,
    limit: int,
    rejects: dict[str, int],
) -> list[dict[str, Any]]:
    """Pick limit leads: core ICP + strong intent first; adjacent only with proof.

    Volume-first: include leads with basic contactability even without strong signals,
    so the engine produces leads on first runs when signal data is sparse.
    """
    core_hi: list[dict[str, Any]] = []
    core_mid: list[dict[str, Any]] = []
    core_lo: list[dict[str, Any]] = []
    adj_hi: list[dict[str, Any]] = []

    for lead in scored:
        score = float(lead.get("intent_score") or 0)
        signals = int(lead.get("intent_signals") or 0)
        tier = lead.get("icp_tier") or "core"
        strong = lead.get("strong_signals") or []
        families = set(lead.get("signal_families") or _signal_families(list(strong)))
        has_email = bool(lead.get("email"))
        has_founder = bool(lead.get("founder_name"))
        has_phone = bool(lead.get("phone"))

        # Weak outreach email without growth/gap signals — still include but lower priority
        if lead.get("weak_outreach_email") and "gap" not in families and "growth" not in families:
            if tier == "core" and has_email and score >= 40:
                core_lo.append(lead)
            else:
                rejects["low_intent"] = rejects.get("low_intent", 0) + 1
            continue

        # High-intent: growth and/or automation gap
        core_hi_ok = (
            tier == "core"
            and score >= 60
            and signals >= 1
            and lead.get("grade") in ("SALES_READY", "QUALIFIED")
            and (
                "high_intent_composite" in strong
                or "ads_plus_automation_gap" in strong
                or ("growth" in families and "gap" in families)
                or ("gap" in families and score >= 65)
                or "founder_reachable" in strong
            )
        )
        core_ok = (
            tier == "core"
            and signals >= 1
            and score >= 50
            and lead.get("grade") in ("SALES_READY", "QUALIFIED")
            and ("gap" in families or "growth" in families or "stack" in families or "product" in families)
        )
        # Volume fallback: core ICP + has contact info + reasonable score
        # This ensures first runs produce leads even without strong signal detection
        # NO grade filter — fallback exists specifically for leads that don't meet hi/mid thresholds
        core_fallback = (
            tier == "core"
            and not core_hi_ok
            and not core_ok
            and has_email
            and score >= 35
        )
        adj_ok = (
            bool(lead.get("industry_adjacent"))
            and score >= 58
            and len(families) >= 1
            and ("gap" in families or "growth" in families or "stack" in families or "product" in families or "reach" in families)
            and lead.get("grade") in ("SALES_READY", "QUALIFIED", "VOLUME")
        )

        if core_hi_ok:
            core_hi.append(lead)
        elif core_ok:
            core_mid.append(lead)
        elif core_fallback:
            core_lo.append(lead)
        elif adj_ok:
            adj_hi.append(lead)
        else:
            rejects["low_intent"] = rejects.get("low_intent", 0) + 1

    out: list[dict[str, Any]] = []
    for bucket in (core_hi, core_mid, core_lo, adj_hi):
        for lead in bucket:
            if len(out) >= limit:
                break
            out.append(lead)
        if len(out) >= limit:
            break
    return out



def _export_run(run_id: str, job: dict[str, Any]) -> None:
    out_dir = EXPORT_ROOT / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    leads = job.get("leads") or []
    csv_path = out_dir / "leads.csv"
    fields = [
        "id",
        "company",
        "founder_name",
        "founder_role",
        "email",
        "phone",
        "website",
        "city",
        "category",
        "size",
        "employee_estimate",
        "employee_estimate_source",
        "platform",
        "technologies",
        "intent_score",
        "grade",
        "signal_families",
        "strong_signals",
        "growth_signals",
        "buying_signals",
        "pain_types",
        "why",
        "signal",
        "subject",
        "body",
        "outreach_status",
        "source",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for lead in leads:
            row = dict(lead)
            if isinstance(row.get("signal_families"), list):
                row["signal_families"] = ",".join(str(x) for x in row["signal_families"])
            if isinstance(row.get("strong_signals"), list):
                row["strong_signals"] = ",".join(str(x) for x in row["strong_signals"])
            w.writerow(row)
    (out_dir / "run.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "product": job.get("product"),
                "status": job.get("status"),
                "stage": job.get("stage"),
                "counts": job.get("counts"),
                "rejects": job.get("rejects"),
                "icp": job.get("icp"),
                "generated_at": datetime.now(UTC).isoformat(),
                "lead_count": len(leads),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    job["export_csv"] = str(csv_path)


async def _run_cyber_discovery_job(job: dict[str, Any], limit: int) -> None:
    """Buyer-first cybersecurity discovery. Does not guess emails or auto-send."""
    from packages.cybersecurity_discovery.exporters import write_exports
    from packages.cybersecurity_discovery.lead_adapter import opportunities_to_lead_engine_rows
    from packages.cybersecurity_discovery.pipeline import run_cybersecurity_discovery
    from packages.cybersecurity_discovery.workspace_sync import sync_to_workspace

    job["stage"] = "extracting"
    job["progress_pct"] = 18
    job["stage_label"] = "Searching public pentest / VAPT / audit buying events…"
    result = await run_cybersecurity_discovery(limit=max(80, min(limit, 200)), enrich=True)
    rows = opportunities_to_lead_engine_rows(result)
    job["counts"]["extracted"] = result.counters.get("TOTAL_DISCOVERED", 0)
    job["counts"]["scored"] = len(rows)
    job["counts"]["ready"] = result.counters.get("SALES_READY", 0)
    job["counts"]["rejected"] = result.counters.get("REJECTED", 0)
    job["counts"]["new_unique"] = len(rows)
    job["leads"] = rows
    job["rejects"] = {"cyber": result.counters}
    job["progress_pct"] = 82
    job["stage"] = "ready"
    job["stage_label"] = (
        f"Cyber lane · {result.counters.get('SALES_READY', 0)} sales-ready · "
        f"{result.counters.get('NEEDS_RESEARCH', 0)} need research"
    )
    out_dir = ROOT / "exports" / "cybersecurity_discovery"
    write_exports(result, out_dir)
    synced = sync_to_workspace(result)
    job["counts"]["workspace_synced"] = synced.get("workspace_leads", 0)
    job["status"] = "completed"
    job["progress_pct"] = 100
    job["finished_at"] = time.time()
    _export_run(job["run_id"], job)


async def run_pipeline(run_id: str) -> None:
    import asyncio

    job = _JOBS[run_id]
    product = job["product"]
    icp = job.get("icp") or {}
    limit = int(job.get("limit") or 80)
    try:
        job["status"] = "running"
        job["stage"] = "extracting"
        job["progress_pct"] = 8
        job["stage_label"] = "Loading discovery sources & intent exports…"
        job["started_at"] = time.time()
        await asyncio.sleep(0.8)

        if product == "cyber":
            await _run_cyber_discovery_job(job, limit)
            return

        seeds = _extract_leads(product, icp)
        job["counts"]["extracted"] = len(seeds)
        job["progress_pct"] = 22
        job["stage_label"] = f"Extracted {len(seeds)} seed candidates"
        await asyncio.sleep(0.4)

        job["stage"] = "enriching"
        job["progress_pct"] = 35
        job["stage_label"] = "Live-discovering NEW brands (may take several minutes)…"

        sent = _load_sent_emails()
        surfaced = _load_surfaced_emails()
        # Multi-wave live discovery until we have enough NEW contacts or waves exhaust
        live_all: list[dict[str, Any]] = []
        # Exclude sent + surfaced emails so live discovery finds truly NEW companies.
        known_emails = set(sent) | surfaced
        for wave in range(1, 4):
            need = max(12, min(24, limit - len(live_all)))
            batch = await _live_discover_new(
                product,
                icp,
                exclude_emails=known_emails,
                batch_limit=min(16, need + 4),
            )
            if not batch:
                # Force domain-memory reset once so later waves re-scrape with stronger contact extraction
                if wave <= 1 and TRIED_DOMAINS_PATH.exists():
                    TRIED_DOMAINS_PATH.write_text(
                        json.dumps(
                            {"updated_at": datetime.now(UTC).isoformat(), "count": 0, "domains": []},
                            indent=2,
                        ),
                        encoding="utf-8",
                    )
                    continue
                break
            live_all.extend(batch)
            for b in batch:
                e = (b.get("email") or "").lower().strip()
                if e:
                    known_emails.add(e)
            job["stage_label"] = f"Live wave {wave} · +{len(batch)} contacts · {len(live_all)} total live"
            job["progress_pct"] = min(58, 35 + wave * 7)
            job["counts"]["live_discovered"] = len(live_all)
            if len(live_all) >= min(limit, 30):
                break

        if live_all:
            seeds.extend(live_all)
            job["counts"]["live_discovered"] = len(live_all)
        else:
            job["counts"]["live_discovered"] = 0

        for lead in seeds:
            lead["enriched"] = bool(
                lead.get("size")
                or lead.get("phone")
                or lead.get("why")
                or lead.get("source") == "live_verified_enrichment"
            )
            lead["outreach_status"] = lead.get("outreach_status") or "ready"
            if not lead.get("phone"):
                m = re.search(
                    r"(\+91[\s-]?\d[\d\s-]{8,16}\d)",
                    str(lead.get("why") or lead.get("signal") or ""),
                )
                if m:
                    lead["phone"] = re.sub(r"\s+", " ", m.group(1)).strip()
        job["counts"]["enriched"] = sum(1 for x in seeds if x.get("enriched"))
        job["progress_pct"] = 62
        job["stage_label"] = f"Enriched · {job['counts']['live_discovered']} live-new · applying ICP…"
        await asyncio.sleep(0.4)

        job["stage"] = "scoring"
        job["progress_pct"] = 72
        job["stage_label"] = "Volume + ICP-strict + Intent ranking…"
        filtered, rejects, soft_flags = apply_icp_filters(seeds, icp, product, prefer_founder=True)
        deduped = _dedupe(filtered)

        # HARD: never re-pitch already-sent. Surfaced-but-unsent can backfill to hit limit.
        never_shown: list[dict[str, Any]] = []
        resurface: list[dict[str, Any]] = []
        for lead in deduped:
            email = (lead.get("email") or "").lower().strip()
            if not email:
                continue
            # For inowix/comai live discovery: skip cross-product seen check (fresh leads)
            is_live_inowix = (
                product == "inowix"
                and lead.get("source") == "live_verified_enrichment"
            )
            is_live_comai = (
                product == "comai"
                and lead.get("source") == "live_verified_enrichment"
            )
            if not is_live_inowix and not is_live_comai and email in sent:
                rejects["already_sent"] = rejects.get("already_sent", 0) + 1
                continue
            if email in surfaced:
                resurface.append(lead)
            else:
                never_shown.append(lead)

        job["rejects"] = rejects
        job["soft_flags"] = soft_flags
        primary = _score_leads(never_shown, product)
        scored = _select_volume_icp_intent(primary, limit=limit, rejects=rejects)
        if len(scored) < limit and resurface:
            secondary = _score_leads(resurface, product)
            need = limit - len(scored)
            fill = _select_volume_icp_intent(secondary, limit=need, rejects=rejects)
            scored.extend(fill)
            rejects["already_surfaced"] = max(0, len(resurface) - len(fill))
        else:
            rejects["already_surfaced"] = len(resurface)

        job["counts"]["scored"] = len(scored)
        job["counts"]["ready"] = len(scored)
        # Hard rejects only — soft_flags are kept leads
        job["counts"]["rejected"] = sum(int(v) for v in rejects.values() if v)
        job["counts"]["soft_flagged"] = sum(int(v) for v in soft_flags.values() if v)
        job["counts"]["icp_core"] = sum(1 for x in scored if x.get("icp_tier") == "core")
        job["counts"]["icp_adjacent"] = sum(1 for x in scored if x.get("industry_adjacent"))
        job["counts"]["new_unique"] = len(
            [x for x in scored if (x.get("email") or "").lower() not in surfaced]
        )
        job["leads"] = scored

        added = merge_into_outreach_pool(scored)
        job["counts"]["pooled_added"] = added
        job["progress_pct"] = 92
        core_n = job["counts"]["icp_core"]
        adj_n = job["counts"]["icp_adjacent"]
        cities_icp = list(icp.get("headquarters_cities") or [])
        if len(scored) == 0 and cities_icp:
            job["stage_label"] = (
                f"0 ready · no matches in {', '.join(str(c) for c in cities_icp[:3])} "
                f"(city HARD) · +{added} pooled"
            )
        else:
            job["stage_label"] = (
                f"{len(scored)} leads · {core_n} ICP-core · {adj_n} adjacent · +{added} pooled"
            )
        await asyncio.sleep(0.3)

        _persist_surfaced_emails({str(x.get("email") or "") for x in scored})
        _persist_last_run_emails({str(x.get("email") or "") for x in scored})

        job["stage"] = "ready"
        job["status"] = "completed"
        job["progress_pct"] = 100
        if len(scored) == 0 and cities_icp:
            job["stage_label"] = (
                f"Ready · 0 new · no {', '.join(str(c) for c in cities_icp[:3])} matches "
                f"(city HARD) · pool {get_auto_status()['pool_count']}"
            )
        else:
            job["stage_label"] = (
                f"Ready · {len(scored)} new · pool size {get_auto_status()['pool_count']}"
            )
        job["finished_at"] = time.time()
        _export_run(run_id, job)
        try:
            activity_path = EXPORT_ROOT / "_workspace_activity.json"
            feed = []
            if activity_path.exists():
                try:
                    feed = list(json.loads(activity_path.read_text(encoding="utf-8")).get("feed") or [])
                except Exception:  # noqa: BLE001
                    feed = []
            feed.insert(
                0,
                {
                    "id": str(uuid.uuid4()),
                    "event": "lead_engine_run",
                    "detail": f"Lead Engine ready · {len(scored)} new leads pooled",
                    "meta": {"run_id": run_id, "ready": len(scored)},
                    "at": datetime.now(UTC).isoformat(),
                },
            )
            EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
            activity_path.write_text(
                json.dumps({"updated_at": datetime.now(UTC).isoformat(), "feed": feed[:80]}, indent=2),
                encoding="utf-8",
            )
        except Exception as sync_exc:  # noqa: BLE001
            logger.debug("Workspace activity update skipped: %s", sync_exc)
        logger.info(
            "Lead engine %s done: kept=%d live=%s pooled=+%s rejected=%s",
            run_id,
            len(scored),
            job["counts"].get("live_discovered"),
            added,
            rejects,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Lead engine run %s failed", run_id)
        job["status"] = "failed"
        job["error"] = str(exc)
        job["stage"] = "failed"
        job["progress_pct"] = 0
        job["stage_label"] = "Failed"
        job["finished_at"] = time.time()


def create_run(*, product: str, icp: dict[str, Any], limit: int = 80) -> dict[str, Any]:
    run_id = str(uuid.uuid4())
    job = {
        "run_id": run_id,
        "product": (product or "comai").lower(),
        "icp": icp or {},
        "limit": max(1, min(int(limit), 200)),
        "status": "queued",
        "stage": "queued",
        "counts": {
            "extracted": 0,
            "enriched": 0,
            "scored": 0,
            "ready": 0,
            "sent": 0,
            "rejected": 0,
            "new_unique": 0,
        },
        "rejects": {},
        "leads": [],
        "drafts": {},
        "error": None,
        "progress_pct": 0,
        "stage_label": "Queued",
        "enrich_status": "idle",
        "enrich_progress_pct": 0,
        "enrich_label": "",
        "created_at": time.time(),
        "started_at": None,
        "finished_at": None,
        "export_csv": None,
    }
    _JOBS[run_id] = job
    return job


def generate_drafts(run_id: str, lead_ids: list[str] | None = None) -> list[dict[str, Any]]:
    from packages.outreach_generator.hyperpersonal import draft_for_product

    job = _JOBS.get(run_id)
    if not job:
        raise KeyError(run_id)
    product = job["product"]
    drafts: list[dict[str, Any]] = []
    for lead in job.get("leads") or []:
        if lead_ids and lead.get("id") not in lead_ids:
            continue
        d = draft_for_product(product, lead)
        lead["subject"] = d.subject
        lead["body"] = d.body
        lead["hook_used"] = d.hook_used
        lead["draft_status"] = "drafted"
        drafts.append(
            {
                "lead_id": lead["id"],
                "company": lead.get("company"),
                "email": lead.get("email"),
                "subject": d.subject,
                "body": d.body,
                "hook_used": d.hook_used,
            }
        )
    job["drafts"] = {d["lead_id"]: d for d in drafts}
    _export_run(run_id, job)
    return drafts


def mark_enriched(run_id: str, lead_ids: list[str]) -> int:
    job = _JOBS.get(run_id)
    if not job:
        raise KeyError(run_id)
    n = 0
    idset = set(lead_ids)
    for lead in job.get("leads") or []:
        if lead.get("id") in idset:
            lead["enriched"] = True
            lead["enrichment_note"] = "manual_enrich_pass"
            n += 1
    job["counts"]["enriched"] = sum(1 for x in (job.get("leads") or []) if x.get("enriched"))
    return n


async def run_enrichment(run_id: str, lead_ids: list[str]) -> None:
    """Async enrichment with progress for selected leads."""
    import asyncio

    job = _JOBS.get(run_id)
    if not job:
        return
    idset = set(lead_ids)
    targets = [x for x in (job.get("leads") or []) if x.get("id") in idset]
    if not targets:
        job["enrich_status"] = "idle"
        job["enrich_progress_pct"] = 0
        job["enrich_label"] = "No leads selected"
        return

    job["enrich_status"] = "running"
    job["enrich_progress_pct"] = 5
    job["enrich_label"] = f"Enriching {len(targets)} leads…"
    total = len(targets)

    for i, lead in enumerate(targets):
        job["enrich_label"] = f"Enriching {lead.get('company') or 'lead'} ({i + 1}/{total})"
        job["enrich_progress_pct"] = int(10 + (i / max(total, 1)) * 80)
        await asyncio.sleep(0.35)

        why = str(lead.get("why") or lead.get("signal") or "")
        if not lead.get("phone"):
            m = re.search(r"(\+91[\s-]?\d[\d\s-]{8,16}\d)", why)
            if m:
                lead["phone"] = re.sub(r"\s+", " ", m.group(1)).strip()
        # evidence chips
        ev = list(lead.get("evidence") or [])
        low = why.lower()
        if lead.get("phone") and not any(str(x).startswith("phone:") for x in ev):
            ev.append(f"phone:{lead['phone']}")
        if "whatsapp" in low and "whatsapp_signal" not in ev:
            ev.append("whatsapp_signal")
        if ("24" in low or "48" in low) and "slow_support_sla" not in ev:
            ev.append("slow_support_sla")
        lead["evidence"] = ev
        lead["enriched"] = True
        lead["enrichment_note"] = "dashboard_enrich_pass"
        lead["enrichment_depth"] = "signals+phone"

    job["counts"]["enriched"] = sum(1 for x in (job.get("leads") or []) if x.get("enriched"))
    job["enrich_status"] = "completed"
    job["enrich_progress_pct"] = 100
    job["enrich_label"] = f"Enriched {total} leads"
    _export_run(run_id, job)
    await asyncio.sleep(0.2)
