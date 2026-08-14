"""Website Understanding — crawl official site pages (max 25). Evidence only."""

from __future__ import annotations

import re
from html import unescape
from typing import Any, Callable
from urllib.parse import urljoin, urlparse

from company_intelligence.models.types import UNKNOWN, WebsiteCorpus, WebsitePage

Fetcher = Callable[[str], tuple[int, str]]

PAGE_PATHS: tuple[str, ...] = (
    "",
    "about",
    "company",
    "products",
    "solutions",
    "services",
    "pricing",
    "contact",
    "careers",
    "team",
    "customers",
    "case-studies",
    "blog",
    "resources",
    "integrations",
    "enterprise",
    "security",
    "developers",
    "docs",
    "api",
    "partners",
    "demo",
    "book-demo",
    "about-us",
    "pricing",
)

MAX_PAGES = 25
_TAG_RE = re.compile(r"<[^>]+>", re.I)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_META_DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
    re.I,
)
_META_DESC_RE2 = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
    re.I,
)
_H_RE = re.compile(r"<h[1-3][^>]*>(.*?)</h[1-3]>", re.I | re.S)
_OG_RE = re.compile(
    r'<meta[^>]+property=["\']og:([^"\']+)["\'][^>]+content=["\']([^"\']+)["\']',
    re.I,
)
_JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)
_NAV_RE = re.compile(r"<nav[^>]*>(.*?)</nav>", re.I | re.S)
_FOOTER_RE = re.compile(r"<footer[^>]*>(.*?)</footer>", re.I | re.S)
_A_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)


def _text(html: str) -> str:
    cleaned = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    return re.sub(r"\s+", " ", unescape(_TAG_RE.sub(" ", cleaned))).strip()


def _strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(_TAG_RE.sub(" ", value or ""))).strip()


class WebsiteUnderstandingEngine:
    def collect(
        self,
        payload: dict[str, Any],
        *,
        fetcher: Fetcher | None = None,
    ) -> WebsiteCorpus:
        website = str(
            payload.get("official_website")
            or payload.get("website")
            or (payload.get("metadata") or {}).get("official_website")
            or ""
        ).strip()
        domain = str(payload.get("domain") or "").strip().lower().removeprefix("www.")
        if not website and domain:
            website = f"https://{domain}"
        if website and not website.startswith("http"):
            website = f"https://{website}"
        if not domain and website:
            domain = urlparse(website).netloc.lower().removeprefix("www.")

        # Payload-provided pages (tests / prior crawl) — never invent content
        preloaded = payload.get("website_pages") or payload.get("pages") or []
        if isinstance(preloaded, list) and preloaded:
            pages = [self._page_from_dict(p, website=website) for p in preloaded if isinstance(p, dict)]
            pages = [p for p in pages if p][:MAX_PAGES]
            return WebsiteCorpus(
                website=website or UNKNOWN,
                domain=domain or UNKNOWN,
                pages=pages,
                page_count=len(pages),
                crawled=True,
                evidence=[f"preloaded_pages:{len(pages)}", f"website:{website}"],
            )

        if not website or website == UNKNOWN:
            return WebsiteCorpus(website=UNKNOWN, domain=domain or UNKNOWN, evidence=["no_website"])

        if not payload.get("fetch_website") and fetcher is None:
            # Homepage stub from payload text only
            html = str(payload.get("website_html") or payload.get("homepage_html") or "")
            if html:
                page = self._parse_page(website, "/", html)
                return WebsiteCorpus(
                    website=website,
                    domain=domain,
                    pages=[page],
                    page_count=1,
                    crawled=True,
                    evidence=["homepage_html_only"],
                )
            return WebsiteCorpus(
                website=website,
                domain=domain,
                crawled=False,
                evidence=["crawl_not_requested"],
            )

        pages: list[WebsitePage] = []
        seen: set[str] = set()
        base = website.rstrip("/")
        for path in PAGE_PATHS:
            if len(pages) >= MAX_PAGES:
                break
            url = base if not path else f"{base}/{path.lstrip('/')}"
            if url in seen:
                continue
            seen.add(url)
            try:
                status, html = self._fetch(url, fetcher=fetcher)
            except Exception:  # noqa: BLE001
                continue
            if status >= 400 or not html or len(html) < 40:
                continue
            pages.append(self._parse_page(url, f"/{path}" if path else "/", html))

        return WebsiteCorpus(
            website=website,
            domain=domain,
            pages=pages,
            page_count=len(pages),
            crawled=bool(pages),
            evidence=[f"crawled_pages:{len(pages)}", f"max:{MAX_PAGES}", f"website:{website}"],
        )

    def _fetch(self, url: str, *, fetcher: Fetcher | None) -> tuple[int, str]:
        if fetcher:
            return fetcher(url)
        import httpx

        with httpx.Client(
            timeout=6.0,
            follow_redirects=True,
            headers={"User-Agent": "BeaconCIR/1.0 (+https://beacon.ai)"},
        ) as client:
            resp = client.get(url)
            return resp.status_code, resp.text

    def _parse_page(self, url: str, path: str, html: str) -> WebsitePage:
        title_m = _TITLE_RE.search(html)
        title = _strip_tags(title_m.group(1)) if title_m else UNKNOWN
        desc_m = _META_DESC_RE.search(html) or _META_DESC_RE2.search(html)
        description = desc_m.group(1).strip() if desc_m else UNKNOWN
        headings = [_strip_tags(h) for h in _H_RE.findall(html)][:20]
        og = {k.lower(): v for k, v in _OG_RE.findall(html)}
        structured: list[dict[str, Any]] = []
        for block in _JSONLD_RE.findall(html)[:5]:
            structured.append({"raw": block.strip()[:2000], "source": "json-ld"})
        nav_bits: list[str] = []
        for nav in _NAV_RE.findall(html)[:2]:
            nav_bits.extend(_A_RE.findall(nav)[:30])
        footer_m = _FOOTER_RE.search(html)
        footer = _text(footer_m.group(1))[:500] if footer_m else UNKNOWN
        text = _text(html)[:8000]
        return WebsitePage(
            url=url,
            path=path,
            title=title or UNKNOWN,
            description=description or UNKNOWN,
            headings=[h for h in headings if h],
            text=text,
            structured_data=structured,
            open_graph=og,
            navigation=nav_bits[:40],
            footer=footer,
            metadata={"chars": len(text)},
            evidence=[f"url:{url}", f"title:{title}", f"headings:{len(headings)}"],
        )

    def _page_from_dict(self, data: dict[str, Any], *, website: str) -> WebsitePage | None:
        url = str(data.get("url") or website or "")
        if not url:
            return None
        path = str(data.get("path") or urlparse(url).path or "/")
        text = str(data.get("text") or data.get("content") or "")
        return WebsitePage(
            url=url,
            path=path,
            title=str(data.get("title") or UNKNOWN),
            description=str(data.get("description") or UNKNOWN),
            headings=list(data.get("headings") or []),
            text=text,
            structured_data=list(data.get("structured_data") or []),
            open_graph=dict(data.get("open_graph") or {}),
            navigation=list(data.get("navigation") or []),
            footer=str(data.get("footer") or UNKNOWN),
            metadata=dict(data.get("metadata") or {}),
            evidence=list(data.get("evidence") or [f"url:{url}"]),
        )
