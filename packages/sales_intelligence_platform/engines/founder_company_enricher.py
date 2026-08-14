"""Founder + company enrichment — domain discover → crawl → intel → public profiles.

Lawful public sources only: DuckDuckGo/Bing SERPs and company website pages.
Never invents domains or emails. No LinkedIn login / private profile scrape.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import asdict, dataclass, field
from html import unescape
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import httpx

from .real_contact_enricher import (
    THIRD_PARTY_DOMAINS,
    USER_AGENTS,
    RealContactEnricher,
)

logger = logging.getLogger(__name__)

_HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_LINKEDIN_IN_RE = re.compile(
    r"https?://(?:[\w.-]+\.)?linkedin\.com/in/([a-zA-Z0-9\-_%]+)", re.IGNORECASE
)
_LINKEDIN_CO_RE = re.compile(
    r"https?://(?:[\w.-]+\.)?linkedin\.com/company/([a-zA-Z0-9\-_%]+)", re.IGNORECASE
)

# Extra hosts that must never become the company domain
_SEARCH_NOISE_DOMAINS = frozenset(
    {
        "duckduckgo.com",
        "bing.com",
        "google.com",
        "google.co.in",
        "yahoo.com",
        "yandex.com",
        "apollo.io",
        "zoominfo.com",
        "crunchbase.com",
        "pitchbook.com",
        "indeed.com",
        "glassdoor.com",
        "justdial.com",
        "indiamart.com",
        "sulekha.com",
        "facebook.com",
        "instagram.com",
        "twitter.com",
        "x.com",
        "youtube.com",
        "wikipedia.org",
        "medium.com",
        "reddit.com",
        "amazonaws.com",
        "cloudflare.com",
        "wix.com",
        "squarespace.com",
        "wordpress.com",
        "blogspot.com",
        "shopify.com",
        "play.google.com",
        "apps.apple.com",
        "mega.io",
        "mega.nz",
        "canva.com",
        "dribbble.com",
        "behance.net",
    }
)


@dataclass
class FounderCompanyResult:
    founder_name: str = ""
    company_name: str = ""
    location: str = ""
    industry: str = ""
    job_title: str = ""
    company_size: str | int | None = None
    domain: str | None = None
    website: str | None = None
    enrichment_status: str = "domain_not_found"
    pages_scraped: int = 0
    emails: list[dict[str, Any]] = field(default_factory=list)
    phones: list[dict[str, Any]] = field(default_factory=list)
    founder_email: str = ""
    business_phone: str = ""
    support_email: str = ""
    general_email: str = ""
    linkedin_person_url: str = ""
    linkedin_company_url: str = ""
    linkedin_urls: list[str] = field(default_factory=list)
    profile_snippets: list[dict[str, str]] = field(default_factory=list)
    about_excerpt: str = ""
    team_excerpt: str = ""
    decision_makers: list[dict[str, Any]] = field(default_factory=list)
    discovery_queries: list[str] = field(default_factory=list)
    discovery_trail: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FounderCompanyEnricher:
    """Orchestrates enrichment from founder + company (+ location) alone."""

    def __init__(
        self,
        *,
        timeout: float = 10.0,
        delay: float = 1.5,
        max_concurrent: int = 1,
        max_pages: int = 15,
    ) -> None:
        self.timeout = timeout
        self.delay = delay
        self.max_concurrent = max_concurrent
        self.max_pages = max_pages
        self.contact = RealContactEnricher(
            timeout=timeout,
            delay=delay,
            max_concurrent=max_concurrent,
            allow_guesses=False,
            max_pages=max_pages,
            light_search=True,
        )

    def _headers(self) -> dict[str, str]:
        import random

        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def enrich(
        self,
        *,
        founder_name: str,
        company_name: str,
        location: str = "",
        industry: str = "",
        job_title: str = "",
        company_size: str | int | None = None,
    ) -> FounderCompanyResult:
        out = FounderCompanyResult(
            founder_name=(founder_name or "").strip(),
            company_name=(company_name or "").strip(),
            location=(location or "").strip(),
            industry=(industry or "").strip(),
            job_title=(job_title or "").strip(),
            company_size=company_size,
        )
        if not out.company_name:
            out.errors.append("missing_company_name")
            out.enrichment_status = "domain_not_found"
            return out

        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            domain, website, trail = await self._discover_domain(client, out)
            out.discovery_trail = trail
            if domain:
                out.domain = domain
                out.website = website or f"https://{domain}"
            else:
                out.errors.append("domain_not_found")
                # Still try public LinkedIn SERP without a domain
                await self._search_public_profiles(client, out)
                out.enrichment_status = (
                    "partial" if out.linkedin_person_url or out.linkedin_company_url else "domain_not_found"
                )
                return out

            await self._search_public_profiles(client, out)

        # Crawl + extract via hardened contact enricher
        try:
            contact_result = await self.contact.enrich(
                domain,
                out.company_name,
                founder_name=out.founder_name,
                allow_guesses=False,
            )
            self._merge_contact_result(out, contact_result)
            # Capture a short about excerpt from homepage HTML if available
            await self._capture_about_excerpt(client=None, out=out, domain=domain)
        except Exception as exc:  # noqa: BLE001
            logger.exception("contact enrich failed for %s", domain)
            out.errors.append(f"crawl_failed:{exc}")

        # Intelligence filter pass
        self._intelligence_filter(out)

        # High-precision domain QA (reject generic brand collisions)
        try:
            from .csv_batch_enrichment import domain_passes_qa

            if out.domain and not domain_passes_qa(out.company_name, out.domain):
                out.errors.append(f"qa_rejected_domain:{out.domain}")
                out.domain = None
                out.website = None
                out.emails = []
                out.phones = []
                out.founder_email = ""
                out.general_email = ""
                out.support_email = ""
                out.business_phone = ""
                out.enrichment_status = "domain_not_found"
                return out
        except ImportError:
            pass

        if out.emails or out.phones or out.linkedin_person_url or out.about_excerpt:
            out.enrichment_status = "enriched"
        else:
            out.enrichment_status = "partial"

        return out

    async def _capture_about_excerpt(
        self, *, client: httpx.AsyncClient | None, out: FounderCompanyResult, domain: str
    ) -> None:
        if out.about_excerpt:
            return
        own = client is None
        http = client or httpx.AsyncClient(timeout=self.timeout, verify=False)
        try:
            for path in ("/about", "/about-us", ""):
                url = f"https://{domain}{path}"
                try:
                    r = await http.get(url, headers=self._headers(), follow_redirects=True)
                except Exception:
                    continue
                if r.status_code >= 400 or len(r.text) < 400:
                    continue
                text = self._html_to_text(r.text[:80000])
                if len(text) < 80:
                    continue
                # Prefer sentences mentioning company or founder
                needle = (out.company_name or "").split()[0:2]
                lower = text.lower()
                idx = -1
                for n in needle:
                    if len(n) >= 3 and n.lower() in lower:
                        idx = lower.find(n.lower())
                        break
                if idx < 0:
                    idx = 0
                start = max(0, idx - 40)
                out.about_excerpt = text[start : start + 280].strip()
                if out.about_excerpt:
                    return
        finally:
            if own:
                await http.aclose()

    async def _discover_domain(
        self, client: httpx.AsyncClient, out: FounderCompanyResult
    ) -> tuple[str | None, str | None, list[str]]:
        city = self._city_hint(out.location)
        queries = [
            f'"{out.company_name}" official website',
            f'"{out.company_name}" {city} website' if city else "",
            f'"{out.company_name}" "{out.founder_name}"' if out.founder_name else "",
        ]
        queries = [q for q in queries if q]
        out.discovery_queries = list(queries)
        trail: list[str] = []
        candidates: list[tuple[str, str, float]] = []

        # Fast path 1: Clearbit public autocomplete
        cb = await self._clearbit_suggest(client, out.company_name)
        trail.append(f"clearbit:hits={len(cb)}")
        for item in cb:
            domain = self._normalize_domain(item.get("domain") or "")
            if not domain or self._is_noise_domain(domain):
                continue
            score = self._domain_score(domain, f"https://{domain}", out.company_name, out.founder_name)
            score += 0.25
            if score > 0:
                candidates.append((domain, f"https://{domain}", score))

        # Fast path 2: verified slug hypotheses (most reliable for niche agencies)
        slug_hits = await self._probe_slug_candidates(client, out)
        trail.append(f"slug_probe:hits={len(slug_hits)}")
        candidates.extend(slug_hits)

        # Early accept if we already have a verified slug/clearbit hit
        if candidates:
            picked = await self._pick_verified(client, candidates, out, trail)
            if picked[0]:
                return picked

        # Slow path: Bing RSS only (HTML SERPs are usually bot-challenged)
        for query in queries[:1]:
            urls = await self._search_bing_rss(client, query)
            await asyncio.sleep(min(self.delay, 0.8))
            trail.append(f"bing_rss:hits={len(urls)}:{query[:40]}")
            for url in urls:
                domain = self._normalize_domain(url)
                if not domain or self._is_noise_domain(domain):
                    continue
                score = self._domain_score(domain, url, out.company_name, out.founder_name)
                if score > 0:
                    candidates.append((domain, f"https://{domain}", score))

        if not candidates:
            trail.append("no_verified_domain")
            return None, None, trail

        return await self._pick_verified(client, candidates, out, trail)

    async def _pick_verified(
        self,
        client: httpx.AsyncClient,
        candidates: list[tuple[str, str, float]],
        out: FounderCompanyResult,
        trail: list[str],
    ) -> tuple[str | None, str | None, list[str]]:
        best: dict[str, tuple[str, str, float]] = {}
        for domain, url, score in candidates:
            prev = best.get(domain)
            if not prev or score > prev[2]:
                best[domain] = (domain, url, score)
        ranked = sorted(best.values(), key=lambda x: x[2], reverse=True)
        for domain, url, score in ranked[:6]:
            ok, reason = await self._verify_domain_page(client, domain, out)
            trail.append(f"verify:{domain}:score={score:.2f}:{reason}")
            if ok:
                trail.append(f"selected:{domain}:score={score:.2f}")
                return domain, url, trail
        trail.append("no_verified_domain")
        return None, None, trail

    async def _clearbit_suggest(
        self, client: httpx.AsyncClient, company_name: str
    ) -> list[dict[str, Any]]:
        try:
            url = (
                "https://autocomplete.clearbit.com/v1/companies/suggest"
                f"?query={quote_plus(company_name)}"
            )
            r = await client.get(url, headers=self._headers(), follow_redirects=True)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    return [x for x in data if isinstance(x, dict)]
        except Exception as exc:
            logger.debug("clearbit failed: %s", exc)
        return []

    async def _search_bing_rss(self, client: httpx.AsyncClient, query: str) -> list[str]:
        try:
            import xml.etree.ElementTree as ET

            url = f"https://www.bing.com/search?q={quote_plus(query)}&format=rss"
            r = await client.get(
                url,
                headers={**self._headers(), "Accept": "application/rss+xml,application/xml"},
                follow_redirects=True,
            )
            if r.status_code != 200 or "<item>" not in r.text:
                return []
            root = ET.fromstring(r.text)
            return [item.findtext("link") or "" for item in root.findall(".//item") if item.findtext("link")]
        except Exception as exc:
            logger.debug("bing rss failed: %s", exc)
            return []

    def _slug_candidates(self, company_name: str) -> list[str]:
        """Generate domain hypotheses from company name (must be verified before use)."""
        tokens = self._company_tokens(company_name)
        if not tokens:
            return []
        joined = "".join(tokens)
        hyphen = "-".join(tokens)
        compact = re.sub(r"[^a-z0-9]", "", company_name.lower())
        # Prefer full brand forms first; avoid probing lone first-token (.com parks)
        ordered_bases: list[str] = []
        for base in (joined, hyphen, compact):
            if base and base not in ordered_bases and 3 <= len(base) <= 40:
                ordered_bases.append(base)
        if len(tokens) >= 2:
            for base in (tokens[0] + tokens[1], f"{tokens[0]}-{tokens[1]}"):
                if base not in ordered_bases and 3 <= len(base) <= 40:
                    ordered_bases.append(base)
        # Only add single-token brand if company is already one token (e.g. SnowSEO, Frick)
        if len(tokens) == 1 and tokens[0] not in ordered_bases and len(tokens[0]) >= 4:
            ordered_bases.append(tokens[0])

        tlds = (".com", ".in", ".co.in", ".agency", ".digital")
        out: list[str] = []
        for base in ordered_bases:
            for tld in tlds:
                out.append(f"{base}{tld}")
        return out[:18]

    async def _probe_slug_candidates(
        self, client: httpx.AsyncClient, out: FounderCompanyResult
    ) -> list[tuple[str, str, float]]:
        hits: list[tuple[str, str, float]] = []
        for domain in self._slug_candidates(out.company_name):
            if self._is_noise_domain(domain):
                continue
            ok, reason = await self._verify_domain_page(client, domain, out)
            if ok:
                score = 0.55 + self._domain_score(
                    domain, f"https://{domain}", out.company_name, out.founder_name
                )
                hits.append((domain, f"https://{domain}", score))
                # First verified high-quality slug is enough
                if "company_strong" in reason or "founder" in reason:
                    break
        return hits

    async def _verify_domain_page(
        self, client: httpx.AsyncClient, domain: str, out: FounderCompanyResult
    ) -> tuple[bool, str]:
        """Accept domain only if live page mentions company or founder tokens."""
        company_tokens = self._company_tokens(out.company_name)
        founder_tokens = [t.lower() for t in out.founder_name.split() if len(t) > 2]
        # Also match compact brand (e.g. kredworks)
        compact = re.sub(r"[^a-z0-9]", "", out.company_name.lower())
        for url in (f"https://{domain}", f"https://www.{domain}"):
            try:
                r = await client.get(url, headers=self._headers(), follow_redirects=True)
                if r.status_code >= 400:
                    continue
                raw = r.text[:250000].lower()
                # Prefer title / meta for signal (JS-heavy sites bury copy)
                title_m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.I | re.S)
                title = _TAG_RE.sub(" ", title_m.group(1)).lower() if title_m else ""
                metas = " ".join(
                    re.findall(
                        r'<meta[^>]*(?:name|property)=["\'](?:og:title|og:site_name|description|application-name)["\'][^>]*content=["\']([^"\']+)',
                        raw,
                        re.I,
                    )
                ).lower()
                text = self._html_to_text(r.text[:120000]).lower()
                blob = f"{title} {metas} {text} {raw[:80000]}"

                company_hits = sum(1 for t in company_tokens if t in blob)
                if compact and len(compact) >= 4 and compact in blob:
                    company_hits = max(company_hits, 2)
                founder_hits = sum(1 for t in founder_tokens if t in blob)
                # Reject parking / marketplace shells
                if any(
                    p in blob
                    for p in (
                        "domain is for sale",
                        "buy this domain",
                        "godaddy",
                        "hugedomains",
                        "sedo.com",
                        "this domain may be for sale",
                    )
                ):
                    return False, "parked"
                strong = company_hits >= max(1, min(2, len(company_tokens)))
                if strong and founder_hits:
                    return True, "company_strong+founder"
                if strong:
                    return True, "company_strong"
                if company_hits >= 1 and founder_hits >= 1:
                    return True, "company+founder"
                if company_hits >= 1 and any(
                    k in blob
                    for k in (
                        "marketing", "agency", "digital", "brand", "media", "founder", "creative",
                        "engineering", "energy", "biotech", "biotechnology", "pharma", "pharmaceutical",
                        "chemical", "oil", "gas", "manufacturing", "consult", "pipeline", "director",
                        "private limited", "pvt", "llp", "kochi", "kerala",
                    )
                ):
                    return True, "company+context"
            except Exception:
                continue
        return False, "no_match"

    def _domain_score(
        self, domain: str, url: str, company_name: str, founder_name: str
    ) -> float:
        tokens = self._company_tokens(company_name)
        if not tokens:
            return 0.0
        host = domain.lower()
        slug = host.split(".")[0]
        joined = "".join(tokens)
        score = 0.0
        # Token overlap with domain slug
        hits = sum(1 for t in tokens if t in slug or t in host)
        if hits == 0 and joined and joined not in slug:
            return 0.0
        score += 0.4 * (hits / max(len(tokens), 1))
        if joined and joined in slug:
            score += 0.35
        # Prefer .in / .com / .co for Indian agencies
        tld = host.rsplit(".", 1)[-1]
        if tld in {"com", "in", "co", "io", "net", "agency", "digital"}:
            score += 0.1
        if founder_name:
            first = founder_name.split()[0].lower()
            if len(first) >= 3 and first in host:
                score += 0.05
        if any(n in host for n in ("blog", "news", "careers", "jobs")):
            score -= 0.2
        return score

    def _company_tokens(self, company_name: str) -> list[str]:
        stop = {
            "the", "and", "of", "a", "an", "pvt", "ltd", "llc", "inc", "co",
            "private", "limited", "solutions", "solution", "media", "digital",
            "marketing", "agency", "studio", "studios", "group", "services",
            "service", "company", "technologies", "technology", "tech",
            "india", "official", "page", "llp", "pvtltd",
        }
        raw = re.sub(r"[^a-zA-Z0-9\s]", " ", company_name.lower())
        tokens = [t for t in raw.split() if len(t) >= 2 and t not in stop]
        return tokens[:5]

    def _city_hint(self, location: str) -> str:
        if not location:
            return ""
        parts = [p.strip() for p in location.split(",") if p.strip()]
        if not parts:
            return ""
        # Skip continent / country-only
        first = parts[0]
        if first.lower() in {"india", "asia", "united states", "us", "usa"}:
            return "India" if "india" in location.lower() else ""
        return first

    def _is_noise_domain(self, domain: str) -> bool:
        host = domain.lower().removeprefix("www.")
        if host in _SEARCH_NOISE_DOMAINS or host in THIRD_PARTY_DOMAINS:
            return True
        try:
            from intelligence.entity_resolution.platform_domains import is_platform_domain

            if is_platform_domain(host):
                return True
        except ImportError:
            pass
        return any(host.endswith(f".{d}") for d in _SEARCH_NOISE_DOMAINS)

    def _normalize_domain(self, url: str) -> str | None:
        try:
            cleaned = self._unwrap_redirect(url)
            parsed = urlparse(cleaned if "://" in cleaned else f"https://{cleaned}")
            host = (parsed.hostname or "").lower().removeprefix("www.")
            if not host or "." not in host:
                return None
            return host
        except Exception:
            return None

    def _unwrap_redirect(self, url: str) -> str:
        """Unwrap Bing/DDG redirect wrappers to the real destination."""
        try:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            for key in ("uddg", "u", "url", "q"):
                if key in qs and qs[key]:
                    return unquote(qs[key][0])
            # Bing: /ck/a?...&u=a1aHR0cHM6Ly...
            if "bing.com" in (parsed.hostname or "") and "u=" in url:
                m = re.search(r"[?&]u=a1([^&]+)", url)
                if m:
                    import base64

                    raw = unquote(m.group(1)) + "=="
                    try:
                        return base64.b64decode(raw).decode("utf-8", errors="ignore")
                    except Exception:
                        pass
            return url
        except Exception:
            return url

    def _extract_result_urls(self, html: str) -> list[str]:
        urls: list[str] = []
        for href in _HREF_RE.findall(html):
            href = unescape(href)
            if not href.startswith("http"):
                continue
            if any(x in href.lower() for x in ("javascript:", "mailto:", "duckduckgo.com/y.js")):
                continue
            urls.append(href)
        # Also catch bare linkedin / http in text
        for m in re.findall(r"https?://[^\s\"'<>]+", html):
            if m not in urls:
                urls.append(m)
        return urls[:40]

    async def _search_duckduckgo(self, client: httpx.AsyncClient, query: str) -> str:
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            r = await client.get(url, headers=self._headers(), follow_redirects=True)
            if r.status_code == 200:
                return r.text[:120000]
        except Exception as exc:
            logger.debug("DDG failed: %s", exc)
        return ""

    async def _search_bing(self, client: httpx.AsyncClient, query: str) -> str:
        try:
            url = f"https://www.bing.com/search?q={quote_plus(query)}&count=10"
            r = await client.get(url, headers=self._headers(), follow_redirects=True)
            if r.status_code == 200:
                return r.text[:120000]
        except Exception as exc:
            logger.debug("Bing failed: %s", exc)
        return ""

    async def _search_public_profiles(self, client: httpx.AsyncClient, out: FounderCompanyResult) -> None:
        queries = []
        city = self._city_hint(out.location)
        if out.founder_name:
            queries.append(f'"{out.founder_name}" "{out.company_name}" site:linkedin.com/in')
        else:
            # Company-only: hunt public CEO / MD / founder profiles
            queries.append(f'"{out.company_name}" (CEO OR "Managing Director" OR Founder OR Director) {city}'.strip())
            queries.append(f'"{out.company_name}" CEO site:linkedin.com/in')
        queries.append(f'"{out.company_name}" site:linkedin.com/company')

        for query in queries:
            # Prefer Bing; DDG HTML is frequently challenge-walled (202)
            html = await self._search_bing(client, query)
            await asyncio.sleep(min(self.delay, 0.8))
            if not html:
                html = await self._search_duckduckgo(client, query)
                await asyncio.sleep(min(self.delay, 0.8))
            if not html:
                continue
            text = self._html_to_text(html)
            for m in _LINKEDIN_IN_RE.finditer(html):
                url = f"https://www.linkedin.com/in/{m.group(1).rstrip('/')}"
                if url not in out.linkedin_urls:
                    out.linkedin_urls.append(url)
                if not out.linkedin_person_url and out.founder_name:
                    slug = m.group(1).lower()
                    tokens = [t.lower() for t in out.founder_name.split() if len(t) > 2]
                    if any(t in slug for t in tokens):
                        out.linkedin_person_url = url
            for m in _LINKEDIN_CO_RE.finditer(html):
                url = f"https://www.linkedin.com/company/{m.group(1).rstrip('/')}"
                if url not in out.linkedin_urls:
                    out.linkedin_urls.append(url)
                if not out.linkedin_company_url:
                    out.linkedin_company_url = url
            snippet = text[:400].strip()
            if snippet and len(out.profile_snippets) < 4:
                out.profile_snippets.append({"query": query, "snippet": snippet[:300]})

        if not out.linkedin_person_url and out.linkedin_urls:
            for u in out.linkedin_urls:
                if "/in/" in u:
                    out.linkedin_person_url = u
                    break

    def _merge_contact_result(self, out: FounderCompanyResult, contact_result: Any) -> None:
        out.pages_scraped = contact_result.pages_scraped
        out.founder_email = contact_result.founder_email or ""
        out.support_email = contact_result.support_email or ""
        out.general_email = contact_result.general_email or ""
        out.business_phone = contact_result.business_phone or ""
        out.errors.extend(contact_result.errors or [])

        for e in contact_result.emails:
            if e.source_url == "pattern_guess" or e.confidence < 0.5:
                continue
            out.emails.append(
                {
                    "value": e.value,
                    "label": e.label,
                    "source_url": e.source_url,
                    "confidence": e.confidence,
                }
            )
        for p in contact_result.phones:
            if p.confidence < 0.5:
                continue
            out.phones.append(
                {
                    "value": p.value,
                    "label": p.label,
                    "source_url": p.source_url,
                    "confidence": p.confidence,
                }
            )
        for dm in contact_result.decision_makers:
            out.decision_makers.append(
                {
                    "name": dm.name,
                    "role": dm.role,
                    "linkedin_url": dm.linkedin_url,
                    "source_url": dm.source_url,
                    "confidence": dm.confidence,
                }
            )
        for u in contact_result.linkedin_urls:
            if u not in out.linkedin_urls:
                out.linkedin_urls.append(u)
            if "/in/" in u and not out.linkedin_person_url:
                if out.founder_name:
                    tokens = [t.lower() for t in out.founder_name.split() if len(t) > 2]
                    if any(t in u.lower() for t in tokens):
                        out.linkedin_person_url = u
                else:
                    out.linkedin_person_url = u
            if "/company/" in u and not out.linkedin_company_url:
                out.linkedin_company_url = u

    def _intelligence_filter(self, out: FounderCompanyResult) -> None:
        """Keep only real, attributable data; drop noise and unmatched people."""
        # Dedupe emails/phones
        seen_e: set[str] = set()
        filtered_e = []
        for e in out.emails:
            val = e["value"].lower()
            domain = val.split("@")[-1]
            if domain in THIRD_PARTY_DOMAINS or self._is_noise_domain(domain):
                continue
            if val in seen_e:
                continue
            seen_e.add(val)
            filtered_e.append(e)
        out.emails = filtered_e

        seen_p: set[str] = set()
        filtered_p = []
        for p in out.phones:
            val = p["value"]
            digits = "".join(ch for ch in val if ch.isdigit())
            # Drop placeholder / obviously fake numbers
            if digits.endswith("00000000") or digits.endswith("0000000"):
                continue
            if len(set(digits[-8:])) <= 2:
                continue
            if val in seen_p:
                continue
            seen_p.add(val)
            filtered_p.append(p)
        out.phones = filtered_p
        if out.business_phone:
            bp_digits = "".join(ch for ch in out.business_phone if ch.isdigit())
            if bp_digits.endswith("00000000") or len(set(bp_digits[-8:])) <= 2:
                out.business_phone = filtered_p[0]["value"] if filtered_p else ""

        # Prefer decision makers matching seed founder name
        if out.founder_name:
            tokens = [t.lower() for t in out.founder_name.split() if len(t) > 1]
            matched = []
            others = []
            for dm in out.decision_makers:
                name_l = dm["name"].lower()
                if any(t in name_l for t in tokens):
                    matched.append(dm)
                else:
                    others.append(dm)
            out.decision_makers = matched + others[:3]

        # Refresh classified fields from filtered lists
        if not out.founder_email:
            for e in out.emails:
                if e.get("label") == "founder":
                    out.founder_email = e["value"]
                    break
        if not out.general_email:
            for e in out.emails:
                if e.get("label") in {"general", "business"}:
                    out.general_email = e["value"]
                    break
        if not out.business_phone and out.phones:
            out.business_phone = out.phones[0]["value"]

    @staticmethod
    def _html_to_text(html: str) -> str:
        without = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
        text = _TAG_RE.sub(" ", without)
        return _WS_RE.sub(" ", unescape(text)).strip()
