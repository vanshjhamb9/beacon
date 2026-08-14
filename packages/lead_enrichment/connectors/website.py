from __future__ import annotations

import re
from collections.abc import Callable
from html import unescape
from urllib.parse import urljoin, urlparse

import httpx

from lead_enrichment.models.types import EnrichmentOpportunityInput, WebsiteFetchResult, WebsitePageContent

PageFetcher = Callable[[str], tuple[int, str]]

_PAGE_CANDIDATES: tuple[tuple[str, str], ...] = (
    ("", "homepage"),
    ("/about", "about"),
    ("/about-us", "about"),
    ("/company", "about"),
    ("/team", "team"),
    ("/about/team", "team"),
    ("/people", "team"),
    ("/contact", "contact"),
    ("/contact-us", "contact"),
    ("/careers", "careers"),
    ("/jobs", "careers"),
    ("/privacy", "privacy"),
    ("/privacy-policy", "privacy"),
    ("/terms", "terms"),
    ("/terms-of-service", "terms"),
)

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_domain(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().lower()
    if not cleaned:
        return None
    if "://" not in cleaned:
        cleaned = f"https://{cleaned}"
    parsed = urlparse(cleaned)
    host = parsed.netloc or parsed.path
    host = host.split("/")[0].removeprefix("www.")
    return host or None


def website_url_for_domain(domain: str | None) -> str | None:
    if not domain:
        return None
    return f"https://{domain}"


def html_to_text(html: str) -> str:
    without_scripts = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = _TAG_RE.sub(" ", without_scripts)
    return _WHITESPACE_RE.sub(" ", unescape(text)).strip()


class WebsiteConnector:
    name = "company_website"

    def __init__(
        self,
        *,
        fetcher: PageFetcher | None = None,
        timeout_seconds: float = 4.0,
        max_pages: int = 8,
        enabled: bool = True,
    ) -> None:
        self.fetcher = fetcher
        self.timeout_seconds = timeout_seconds
        self.max_pages = max_pages
        self.enabled = enabled

    def collect(self, item: EnrichmentOpportunityInput) -> WebsiteFetchResult:
        domain = normalize_domain(item.domain or item.website)
        if not self.enabled or not domain:
            return WebsiteFetchResult(domain=domain, fetched=False, error="website_unavailable")

        base = website_url_for_domain(domain)
        assert base is not None
        pages: list[WebsitePageContent] = []
        seen_urls: set[str] = set()

        for path, page_type in _PAGE_CANDIDATES:
            if len(pages) >= self.max_pages:
                break
            url = urljoin(base + "/", path.lstrip("/")) if path else base
            if url in seen_urls:
                continue
            seen_urls.add(url)
            try:
                status_code, html = self._fetch(url)
            except Exception as exc:  # noqa: BLE001 - connector must never fail the pipeline
                if page_type == "homepage":
                    return WebsiteFetchResult(
                        domain=domain,
                        fetched=False,
                        error=f"homepage_fetch_failed:{exc.__class__.__name__}",
                    )
                continue
            if status_code >= 400 or not html.strip():
                continue
            pages.append(
                WebsitePageContent(
                    url=url,
                    page_type=page_type,
                    html=html,
                    text=html_to_text(html),
                    status_code=status_code,
                )
            )

        return WebsiteFetchResult(domain=domain, pages=pages, fetched=bool(pages))

    def _fetch(self, url: str) -> tuple[int, str]:
        if self.fetcher is not None:
            return self.fetcher(url)
        with httpx.Client(
            timeout=self.timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "BeaconAI-LeadEnrichment/1.0 (+https://beacon.ai)"},
        ) as client:
            response = client.get(url)
            return response.status_code, response.text
