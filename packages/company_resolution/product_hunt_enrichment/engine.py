"""Product Hunt identity enrichment — recover product homepage from PH page HTML."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from intelligence.entity_resolution.normalization import normalize_domain
from intelligence.entity_resolution.platform_domains import is_platform_domain

HREF_RE = re.compile(r'href=["\'](https?://[^"\']+)["\']', re.I)


class ProductHuntHomepageEngine:
    """Extract official product website from a Product Hunt product page. Never invent."""

    def extract(self, *, product_url: str | None, html: str | None = None, fetcher=None) -> dict[str, Any]:
        html_text = html
        if not html_text and product_url and fetcher is not None:
            try:
                html_text = fetcher(product_url)
            except Exception:  # noqa: BLE001
                html_text = None
        if not html_text and product_url and "producthunt.com" in (product_url or ""):
            try:
                import httpx

                with httpx.Client(timeout=6.0, follow_redirects=True, headers={"User-Agent": "BeaconCRE/1.0"}) as client:
                    resp = client.get(product_url)
                    if resp.status_code < 400:
                        html_text = resp.text
            except Exception:  # noqa: BLE001
                html_text = None

        if not html_text:
            return {"homepage": None, "domain": None, "evidence": ["ph_html_unavailable"]}

        candidates: list[str] = []
        for href in HREF_RE.findall(html_text):
            host = urlparse(href).netloc.lower().removeprefix("www.")
            if not host or is_platform_domain(host):
                continue
            if "producthunt.com" in host or "phcdn.com" in host:
                continue
            if any(x in href.lower() for x in ("twitter.com", "x.com", "facebook.com", "linkedin.com", "youtube.com", "instagram.com")):
                continue
            domain = normalize_domain(host)
            if domain and not is_platform_domain(domain):
                candidates.append(domain)

        # Prefer first unique
        seen: set[str] = set()
        ordered: list[str] = []
        for d in candidates:
            if d not in seen:
                seen.add(d)
                ordered.append(d)
        if not ordered:
            return {"homepage": None, "domain": None, "evidence": ["ph_no_external_domain"]}
        domain = ordered[0]
        return {
            "homepage": f"https://{domain}",
            "domain": domain,
            "evidence": [f"ph_homepage:{domain}", f"candidates:{len(ordered)}"],
        }
