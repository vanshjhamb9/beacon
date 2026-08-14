from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse

from revenue_quality_recovery.models.types import (
    AttributedField,
    CrawlDiscovery,
    WebsiteCrawlResult,
    UNKNOWN,
)

PAGE_HINTS: dict[str, tuple[str, ...]] = {
    "contact": ("contact", "get-in-touch", "reach-us"),
    "team": ("team", "our-team", "people"),
    "leadership": ("leadership", "executives", "management"),
    "careers": ("careers", "jobs", "join-us", "hiring"),
    "about": ("about", "about-us", "company"),
    "pricing": ("pricing", "plans", "packages"),
    "privacy": ("privacy", "privacy-policy"),
    "footer": ("footer",),
    "header": ("header", "nav"),
}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
SOCIAL_HOSTS = {
    "linkedin": ("linkedin.com",),
    "twitter": ("twitter.com", "x.com"),
    "github": ("github.com",),
    "facebook": ("facebook.com",),
    "instagram": ("instagram.com",),
    "youtube": ("youtube.com", "youtu.be"),
}
MAILTO_RE = re.compile(r"mailto:([^\s\"'<>]+)", re.I)
TEL_RE = re.compile(r"tel:([^\s\"'<>]+)", re.I)
HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)
JSONLD_RE = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)
OG_RE = re.compile(r'property=["\']og:([^"\']+)["\'][^>]*content=["\']([^"\']+)["\']', re.I)
OG_RE_ALT = re.compile(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:([^"\']+)["\']', re.I)
ROLE_HINTS = ("founder", "ceo", "cto", "coo", "chief", "vp ", "head of", "director")


class WebsiteCrawlerEngine:
    """Rule 3 — discover contact/team/about pages and extract public contact artifacts from HTML."""

    def crawl(self, payload: dict[str, Any]) -> WebsiteCrawlResult:
        base = str(payload.get("website") or payload.get("primary_domain") or "")
        html = str(payload.get("website_html") or payload.get("html") or "")
        pages_meta = payload.get("discovered_pages") or payload.get("pages") or {}
        collected_at = payload.get("collected_at") or payload.get("last_seen_at")
        source = str(payload.get("source") or "website_crawler")

        pages: list[CrawlDiscovery] = []
        corpus = html.lower()
        hrefs = HREF_RE.findall(html) if html else []

        for page_type, hints in PAGE_HINTS.items():
            url = UNKNOWN
            found = False
            if isinstance(pages_meta, dict) and pages_meta.get(page_type):
                found = True
                url = str(pages_meta[page_type])
            else:
                for href in hrefs:
                    low = href.lower()
                    if any(h in low for h in hints):
                        found = True
                        url = urljoin(self._base_url(base), href) if base else href
                        break
                if not found and any(h in corpus for h in hints):
                    found = True
                    url = f"{self._base_url(base)}/{hints[0]}" if base else hints[0]
            pages.append(CrawlDiscovery(page_type=page_type, url=url if found else UNKNOWN, found=found, evidence=[f"page:{page_type}:{found}"]))

        emails: list[AttributedField] = []
        phones: list[AttributedField] = []
        for m in MAILTO_RE.findall(html):
            emails.append(AttributedField.of(m, source=source, collected_at=collected_at, confidence=90.0, verification="mailto_link", evidence=["mailto"]))
        for m in EMAIL_RE.findall(html):
            if any(e.value == m for e in emails):
                continue
            if m.lower().endswith(("@example.com", "@sentry.io", "@wixpress.com")):
                continue
            emails.append(AttributedField.of(m, source=source, collected_at=collected_at, confidence=75.0, verification="html_extract", evidence=["email_regex"]))
        for m in TEL_RE.findall(html):
            phones.append(AttributedField.of(m, source=source, collected_at=collected_at, confidence=88.0, verification="tel_link", evidence=["tel"]))
        for m in PHONE_RE.findall(html):
            cleaned = re.sub(r"[^\d+]", "", m)
            if len(cleaned) < 8:
                continue
            if any(p.value == m for p in phones):
                continue
            phones.append(AttributedField.of(m.strip(), source=source, collected_at=collected_at, confidence=65.0, verification="html_extract", evidence=["phone_regex"]))

        # Also accept pre-extracted lists
        for e in payload.get("emails") or []:
            if e and not any(x.value == e for x in emails):
                emails.append(AttributedField.of(e, source=source, collected_at=collected_at, confidence=70.0, verification="payload", evidence=["payload_email"]))
        for p in payload.get("phones") or []:
            if p and not any(x.value == p for x in phones):
                phones.append(AttributedField.of(p, source=source, collected_at=collected_at, confidence=70.0, verification="payload", evidence=["payload_phone"]))

        social: dict[str, AttributedField] = {}
        for network, hosts in SOCIAL_HOSTS.items():
            for href in hrefs:
                host = (urlparse(href).hostname or "").lower()
                if any(h in host for h in hosts):
                    social[network] = AttributedField.of(
                        href, source=source, collected_at=collected_at, confidence=85.0, verification="href", evidence=[f"social:{network}"]
                    )
                    break
            if network not in social and isinstance(payload.get("social"), dict) and payload["social"].get(network):
                social[network] = AttributedField.of(
                    payload["social"][network], source=source, collected_at=collected_at, confidence=80.0, verification="payload", evidence=[f"social:{network}"]
                )

        schema = self._parse_jsonld(html) or dict(payload.get("schema_org") or payload.get("organization_schema") or {})
        og: dict[str, Any] = dict(payload.get("open_graph") or {})
        for prop, content in OG_RE.findall(html):
            og[prop] = content
        for content, prop in OG_RE_ALT.findall(html):
            og.setdefault(prop, content)

        founders: list[AttributedField] = []
        executives: list[AttributedField] = []
        for person in payload.get("people") or payload.get("team") or []:
            if not isinstance(person, dict):
                continue
            name = person.get("name")
            role = str(person.get("role") or person.get("title") or "").lower()
            if not name:
                continue
            field = AttributedField.of(
                {"name": name, "role": person.get("role") or person.get("title")},
                source=source,
                collected_at=collected_at,
                confidence=float(person.get("confidence") or 70),
                verification="page_extract",
                evidence=[f"person:{name}"],
            )
            if "founder" in role:
                founders.append(field)
            if any(h in role for h in ROLE_HINTS):
                executives.append(field)

        evidence = [
            f"pages_found:{sum(1 for p in pages if p.found)}",
            f"emails:{len(emails)}",
            f"phones:{len(phones)}",
            f"social:{len(social)}",
        ]
        return WebsiteCrawlResult(
            pages=pages,
            emails=emails[:20],
            phones=phones[:20],
            social=social,
            founders=founders,
            executives=executives,
            schema_org=schema,
            open_graph=og,
            evidence=evidence,
        )

    def _base_url(self, website: str) -> str:
        if not website:
            return ""
        raw = website if "://" in website else f"https://{website}"
        parsed = urlparse(raw)
        return f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else raw

    def _parse_jsonld(self, html: str) -> dict[str, Any]:
        if not html:
            return {}
        import json

        for block in JSONLD_RE.findall(html):
            try:
                data = json.loads(block.strip())
            except Exception:  # noqa: BLE001
                continue
            if isinstance(data, dict):
                return data
            if isinstance(data, list) and data and isinstance(data[0], dict):
                return data[0]
        return {}
