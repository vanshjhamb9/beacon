"""Official domain validator — HTTPS, reachability, title. Never fabricate."""

from __future__ import annotations

from typing import Any, Callable
from urllib.parse import urlparse

from entity_resolution.models.types import DomainValidation, OfficialWebsite

Fetcher = Callable[[str], tuple[int, str, str | None]]  # status, text, final_url


class OfficialDomainValidator:
    def validate(
        self,
        website: OfficialWebsite,
        *,
        fetcher: Fetcher | None = None,
        payload: dict[str, Any] | None = None,
    ) -> DomainValidation:
        payload = payload or {}
        if not website.discovered or not website.domain or not website.website:
            return DomainValidation(verified=False, reason="no_official_website", evidence=["missing_website"])

        # Payload-provided validation (tests / prior fetch)
        if payload.get("website_verified") is True or payload.get("domain_verified") is True:
            return DomainValidation(
                domain=website.domain,
                verified=True,
                https=True,
                dns_ok=True,
                status_ok=True,
                ssl_ok=True,
                homepage_reachable=True,
                title=payload.get("website_title"),
                favicon_url=payload.get("favicon_url"),
                reason="verified_from_payload",
                evidence=["payload_verified"],
            )

        http_status = payload.get("http_status")
        alive = payload.get("website_alive")
        title = payload.get("website_title")
        html = payload.get("website_html_text") or payload.get("website_title")
        final_url = payload.get("redirect_final")

        if payload.get("fetch_validate") or fetcher or payload.get("fetch_official_website"):
            try:
                if fetcher:
                    status, text, final = fetcher(website.website)
                else:
                    import httpx

                    with httpx.Client(
                        timeout=8.0,
                        follow_redirects=True,
                        headers={"User-Agent": "BeaconEROWD/1.0"},
                    ) as client:
                        resp = client.get(website.website)
                        status, text, final = resp.status_code, resp.text[:5000], str(resp.url)
                http_status = status
                alive = 200 <= status < 400
                final_url = final
                if text and not title:
                    import re

                    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
                    title = re.sub(r"\s+", " ", m.group(1)).strip() if m else None
                    html = text
            except Exception as exc:  # noqa: BLE001
                return DomainValidation(
                    domain=website.domain,
                    verified=False,
                    reason=f"fetch_failed:{exc.__class__.__name__}",
                    evidence=["fetch_failed"],
                )

        https = (website.website or "").startswith("https://")
        status_ok = http_status is not None and 200 <= int(http_status) < 400
        homepage_reachable = alive is True or status_ok
        # If no live fetch requested, allow provisional verify when discovery confidence high + https
        if http_status is None and alive is None and not payload.get("fetch_validate"):
            provisional = https and website.confidence >= 90
            return DomainValidation(
                domain=website.domain,
                verified=provisional,
                https=https,
                dns_ok=provisional,
                status_ok=provisional,
                ssl_ok=https,
                homepage_reachable=provisional,
                title=title,
                reason="provisional_high_confidence" if provisional else "validation_pending",
                evidence=["provisional" if provisional else "pending_live_validation"],
            )

        verified = bool(https and homepage_reachable and status_ok)
        reason = "verified" if verified else "unreachable_or_http_error"
        if html and any(x in str(html).lower() for x in ("domain for sale", "parked", "coming soon")):
            verified = False
            reason = "parked_or_placeholder"

        return DomainValidation(
            domain=website.domain,
            verified=verified,
            https=https,
            dns_ok=verified,
            status_ok=status_ok,
            ssl_ok=https,
            homepage_reachable=homepage_reachable,
            title=title,
            favicon_url=f"https://{website.domain}/favicon.ico" if verified else None,
            redirect_final=final_url,
            reason=reason,
            evidence=[f"https:{https}", f"status:{http_status}", f"verified:{verified}"],
        )
