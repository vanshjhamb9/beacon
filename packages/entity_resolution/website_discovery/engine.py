"""Official Website Discovery — evidence only. Never guess or fabricate."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any, Callable
from urllib.parse import urlparse

from entity_resolution.models.types import OfficialWebsite, UNKNOWN
from intelligence.entity_resolution.normalization import normalize_domain
from intelligence.entity_resolution.platform_domains import is_platform_domain

Fetcher = Callable[[str], tuple[int, str]]

# Never use these as company identity
FORBIDDEN_IDENTITY_HOSTS = frozenset(
    {
        "producthunt.com",
        "www.producthunt.com",
        "github.com",
        "gist.github.com",
        "reddit.com",
        "old.reddit.com",
        "news.ycombinator.com",
        "hnrss.org",
        "techcrunch.com",
        "theverge.com",
        "dev.to",
        "medium.com",
        "substack.com",
        "linkedin.com",
        "twitter.com",
        "x.com",
        "youtube.com",
        "facebook.com",
        "wikipedia.org",
        "arxiv.org",
        "npmjs.com",
        "pypi.org",
    }
)

HREF_RE = re.compile(r"""href=["'](https?://[^"']+)["']""", re.I)
OG_URL_RE = re.compile(r"""property=["']og:url["']\s+content=["']([^"']+)["']""", re.I)
OG_URL_RE2 = re.compile(r"""content=["']([^"']+)["']\s+property=["']og:url["']""", re.I)
JSONLD_URL_RE = re.compile(r'"(?:url|sameAs)"\s*:\s*"(https?://[^"]+)"', re.I)
CANONICAL_RE = re.compile(r"""rel=["']canonical["']\s+href=["']([^"']+)["']""", re.I)
HOMEPAGE_META_RE = re.compile(
    r"""(?:application-url|og:see_also|twitter:url)["'\s]+content=["'](https?://[^"']+)["']""",
    re.I,
)
GITHUB_HOMEPAGE_RE = re.compile(
    r"""<span[^>]*itemprop=["']url["'][^>]*>\s*<a[^>]+href=["'](https?://[^"']+)["']""",
    re.I,
)
GITHUB_HOMEPAGE_RE2 = re.compile(r"""class=["'][^"']*Link--primary[^"']*["'][^>]*href=["'](https?://(?!github\.com)[^"']+)["']""", re.I)


class OfficialWebsiteDiscoveryEngine:
    """Priority: PH official website → homepage field → GitHub homepage/org → LinkedIn → Dev.to → RSS → JSON-LD/OG."""

    PRIORITY = (
        "product_hunt_official_website",
        "company_homepage_field",
        "github_repository_homepage",
        "github_organization_website",
        "linkedin_company_website",
        "devto_profile_website",
        "rss_canonical_company_website",
        "structured_metadata",
        "json_ld_organization",
        "open_graph",
    )

    def discover(
        self,
        payload: dict[str, Any],
        *,
        fetcher: Fetcher | None = None,
        html_cache: dict[str, str] | None = None,
    ) -> OfficialWebsite:
        evidence: list[str] = []
        html_cache = html_cache or {}

        # 1) Explicit fields already on the signal (never invent)
        for key, source in (
            ("official_website", "company_homepage_field"),
            ("homepage", "company_homepage_field"),
            ("product_website", "product_hunt_official_website"),
            ("website", "structured_metadata"),
            ("company_website", "structured_metadata"),
            ("github_homepage", "github_repository_homepage"),
            ("org_website", "github_organization_website"),
            ("linkedin_website", "linkedin_company_website"),
            ("devto_website", "devto_profile_website"),
            ("canonical_website", "rss_canonical_company_website"),
        ):
            value = payload.get(key) or (payload.get("metadata") or {}).get(key)
            hit = self._accept(value, source=source, evidence=evidence)
            if hit:
                return hit

        # 1b) Product Hunt: resolve /r/p/ redirect from Atom feed (preferred — pages often Cloudflare-blocked)
        source = str(payload.get("source") or "").lower()
        url = payload.get("url")
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if source == "product_hunt":
            redirect = meta.get("ph_redirect_url") or payload.get("ph_redirect_url")
            if not redirect:
                blob = " ".join(
                    str(x or "")
                    for x in (payload.get("body"), payload.get("content"), meta.get("raw_content"), url)
                )
                m = re.search(r"https?://(?:www\.)?producthunt\.com/r/p/\d+[^\"'\s<]*", blob, re.I)
                if m:
                    redirect = m.group(0).replace("&amp;", "&")
            if redirect:
                resolved = self._resolve_redirect(str(redirect), fetcher=fetcher)
                if resolved:
                    hit = self._accept(resolved, source="product_hunt_official_website", evidence=evidence)
                    if hit:
                        evidence.append("ph_redirect_resolution")
                        return hit
                else:
                    evidence.append("ph_redirect_blocked_or_unresolved")

        # 1c) Product Hunt: fetch listing page and extract official site
        if source == "product_hunt" and url:
            html = self._get_html(str(url), fetcher=fetcher, html_cache=html_cache, payload=payload)
            if html:
                for candidate, src in self._extract_from_html(html, prefer_ph=True):
                    hit = self._accept(candidate, source=src, evidence=evidence)
                    if hit:
                        evidence.append("ph_page_discovery")
                        return hit

        # GitHub repo/org page
        if source == "github_trending" and url and "github.com" in str(url):
            html = self._get_html(str(url), fetcher=fetcher, html_cache=html_cache, payload=payload)
            if html:
                for candidate, src in self._extract_github(html):
                    hit = self._accept(candidate, source=src, evidence=evidence)
                    if hit:
                        return hit
            # metadata owner homepage
            meta = payload.get("metadata") or {}
            hit = self._accept(meta.get("repo_homepage") or meta.get("homepage"), source="github_repository_homepage", evidence=evidence)
            if hit:
                return hit

        # Generic HTML on provided website_html / page_html
        for html_key in ("website_html", "page_html", "product_hunt_html", "github_html"):
            html = payload.get(html_key) or (payload.get("metadata") or {}).get(html_key)
            if isinstance(html, str) and html.strip():
                for candidate, src in self._extract_from_html(html, prefer_ph=source == "product_hunt"):
                    hit = self._accept(candidate, source=src, evidence=evidence)
                    if hit:
                        return hit

        # metadata.domain only if not platform/forbidden
        meta_domain = (payload.get("metadata") or {}).get("domain") or payload.get("domain")
        if meta_domain and not self._forbidden(str(meta_domain)):
            # Domain alone is not enough unless marked as official website field
            if payload.get("official_website") or payload.get("homepage") or (payload.get("metadata") or {}).get("official_website"):
                hit = self._accept(f"https://{meta_domain}", source="structured_metadata", evidence=evidence)
                if hit:
                    return hit
            # Explicit official_domain key
            if payload.get("official_domain") or (payload.get("metadata") or {}).get("official_domain"):
                d = payload.get("official_domain") or (payload.get("metadata") or {}).get("official_domain")
                hit = self._accept(f"https://{d}", source="structured_metadata", evidence=evidence)
                if hit:
                    return hit

        evidence.append("no_official_website_evidence")
        return OfficialWebsite(discovered=False, evidence=evidence, source=UNKNOWN)

    def _resolve_redirect(self, url: str, *, fetcher: Fetcher | None = None) -> str | None:
        """Follow Product Hunt /r/p/ redirects to the official site. Never invent."""
        try:
            if fetcher:
                status, html = fetcher(url)
                # Fetcher may return final URL embedded; prefer Location via httpx below
                _ = (status, html)
            import httpx

            with httpx.Client(
                timeout=10.0,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; BeaconEROWD/1.0; +https://beacon.ai)"
                    ),
                    "Accept": "text/html,application/xhtml+xml",
                },
            ) as client:
                resp = client.get(url)
                final = str(resp.url)
                host = urlparse(final).netloc.lower().removeprefix("www.")
                if host and not self._forbidden(host) and "producthunt.com" not in host:
                    return f"{urlparse(final).scheme or 'https'}://{host}"
                # Some challenges return 403 on PH host — no evidence
                return None
        except Exception:  # noqa: BLE001
            return None

    def _get_html(
        self,
        url: str,
        *,
        fetcher: Fetcher | None,
        html_cache: dict[str, str],
        payload: dict[str, Any],
    ) -> str | None:
        if url in html_cache:
            return html_cache[url]
        # Allow preloaded HTML
        for key in ("product_hunt_html", "page_html", "github_html"):
            if payload.get(key):
                return str(payload[key])
        if not payload.get("fetch_official_website") and not payload.get("fetch_product_hunt"):
            return None
        try:
            if fetcher:
                status, html = fetcher(url)
                if status < 400 and html:
                    html_cache[url] = html
                    return html
            import httpx

            with httpx.Client(
                timeout=8.0,
                follow_redirects=True,
                headers={"User-Agent": "BeaconEROWD/1.0 (+https://beacon.ai)"},
            ) as client:
                resp = client.get(url)
                if resp.status_code < 400 and resp.text:
                    html_cache[url] = resp.text
                    return resp.text
        except Exception:  # noqa: BLE001
            return None
        return None

    def _extract_from_html(self, html: str, *, prefer_ph: bool = False) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        # OpenGraph
        for rx in (OG_URL_RE, OG_URL_RE2):
            m = rx.search(html)
            if m:
                out.append((m.group(1), "open_graph"))
        # JSON-LD
        for m in JSONLD_URL_RE.finditer(html):
            out.append((m.group(1), "json_ld_organization"))
        # canonical
        m = CANONICAL_RE.search(html)
        if m:
            out.append((m.group(1), "rss_canonical_company_website" if not prefer_ph else "product_hunt_official_website"))
        for m in HOMEPAGE_META_RE.finditer(html):
            out.append((m.group(1), "structured_metadata"))
        # Product Hunt specific: redirect / visit links
        if prefer_ph:
            for pattern in (
                r"""/r/[^"']+["'][^>]*href=["'](https?://[^"']+)["']""",
                r"""data-test=["'][^"']*visit[^"']*["'][^>]*href=["'](https?://[^"']+)["']""",
                r"""href=["'](https?://(?!www\.producthunt\.com|producthunt\.com)[^"']+)["'][^>]*>\s*Visit""",
                r"""Visit (?:website|site|homepage)[^<]*<[^>]+href=["'](https?://[^"']+)["']""",
            ):
                for m in re.finditer(pattern, html, re.I):
                    out.append((m.group(1), "product_hunt_official_website"))
            # Any external href as last resort for PH pages only when labeled website-like
            for href in HREF_RE.findall(html):
                host = urlparse(href).netloc.lower()
                if host and not self._forbidden(host) and "phcdn" not in host:
                    # Prefer root paths
                    path = urlparse(href).path or "/"
                    if path in {"", "/"} or len(path) < 20:
                        out.append((href, "product_hunt_official_website"))
        return out

    def _extract_github(self, html: str) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        for rx, src in (
            (GITHUB_HOMEPAGE_RE, "github_repository_homepage"),
            (GITHUB_HOMEPAGE_RE2, "github_repository_homepage"),
        ):
            for m in rx.finditer(html):
                out.append((m.group(1), src))
        # org website patterns
        for m in re.finditer(r"""itemprop=["']url["'][^>]*href=["'](https?://(?!github\.com)[^"']+)["']""", html, re.I):
            out.append((m.group(1), "github_organization_website"))
        return out

    def _accept(self, value: Any, *, source: str, evidence: list[str]) -> OfficialWebsite | None:
        if not value or not isinstance(value, str):
            return None
        raw = value.strip()
        if not raw:
            return None
        # Reject listing/article URLs used as identity
        host = urlparse(raw if "://" in raw else f"https://{raw}").netloc.lower().removeprefix("www.")
        if not host:
            host = normalize_domain(raw) or ""
        if self._forbidden(host):
            evidence.append(f"rejected_forbidden:{host or raw}")
            return None
        domain = normalize_domain(host or raw)
        if not domain or is_platform_domain(domain) or self._forbidden(domain):
            evidence.append(f"rejected_platform:{raw}")
            return None
        # Never use version-like strings
        if re.match(r"^\d+(\.\d+)+$", domain) or re.search(r"\.(tsx|ts|js|py|md)$", domain):
            evidence.append(f"rejected_invalid:{domain}")
            return None
        website = raw if raw.startswith("http") else f"https://{domain}"
        # Strip deep paths for canonical identity homepage when clearly a tracking URL
        parsed = urlparse(website)
        if parsed.netloc:
            website = f"{parsed.scheme or 'https'}://{parsed.netloc.removeprefix('www.')}"
            if not website.startswith("http"):
                website = f"https://{domain}"
        evidence.extend([f"source:{source}", f"domain:{domain}", f"website:{website}"])
        return OfficialWebsite(
            website=website,
            domain=domain,
            source=source,
            confidence=self._source_confidence(source),
            verified_at=datetime.now(UTC),
            discovered=True,
            evidence=list(evidence),
        )

    def _source_confidence(self, source: str) -> float:
        ranking = {name: 98.0 - i * 3 for i, name in enumerate(self.PRIORITY)}
        return ranking.get(source, 70.0)

    def _forbidden(self, host: str) -> bool:
        h = host.lower().removeprefix("www.")
        if h in FORBIDDEN_IDENTITY_HOSTS:
            return True
        return any(h.endswith(f".{item}") for item in FORBIDDEN_IDENTITY_HOSTS)
