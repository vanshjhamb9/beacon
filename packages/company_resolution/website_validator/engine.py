"""Phase 4 — Website validation. Reject blogs, news, repos, parked, docs."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from company_resolution.models.types import OrganizationCandidate, RejectionReason, WebsiteValidation
from intelligence.entity_resolution.platform_domains import is_platform_domain

REJECT_HOST_HINTS = (
    "medium.com",
    "substack.com",
    "github.io",
    "github.com",
    "gist.github.com",
    "readthedocs.io",
    "gitbook.io",
    "notion.site",
    "wordpress.com",
    "blogspot.com",
    "tumblr.com",
    "dev.to",
    "hashnode.dev",
    "news.ycombinator.com",
    "reddit.com",
    "stackoverflow.com",
    "stackexchange.com",
    "wikipedia.org",
    "techcrunch.com",
    "theverge.com",
    "reuters.com",
    "bloomberg.com",
    "cnn.com",
    "bbc.com",
    "nytimes.com",
    "forbes.com",
    "wired.com",
    "arstechnica.com",
    "politico.com",
    "axios.com",
    "techdirt.com",
    "producthunt.com",
    "indiehackers.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "facebook.com",
    "youtube.com",
    "arxiv.org",
    "npmjs.com",
    "pypi.org",
    "crates.io",
)

PARKED_HINTS = (
    "parked",
    "domain for sale",
    "buy this domain",
    "godaddy",
    "sedo.com",
    "hugedomains",
    "this domain is for sale",
    "coming soon",
    "under construction",
    "website coming soon",
)

BLOG_HINTS = ("personal blog", "my blog", "written by", "i wrote this")
DOCS_HINTS = ("documentation", "api reference", "getting started", "read the docs")
REPO_PATH_HINTS = ("/blob/", "/tree/", "/pull/", "/issues/", "/commit/")


class WebsiteValidatorEngine:
    """Validate candidate domain. Supports payload flags or live HTML text."""

    def validate(
        self,
        org: OrganizationCandidate,
        *,
        http_status: int | None = None,
        html_text: str | None = None,
        website_alive: bool | None = None,
        ssl: bool | None = None,
        title: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> WebsiteValidation:
        payload = payload or {}
        domain = org.official_domain
        evidence: list[str] = []
        if not domain:
            return WebsiteValidation(
                domain=None,
                valid=False,
                reject_reason=RejectionReason.NO_DOMAIN,
                evidence=["no_domain"],
            )

        if is_platform_domain(domain) or self._host_rejected(domain):
            reason = self._classify_host(domain)
            return WebsiteValidation(
                domain=domain,
                valid=False,
                reject_reason=reason,
                evidence=[f"host_reject:{domain}", reason.value],
            )

        url = org.homepage or org.official_url or f"https://{domain}"
        for hint in REPO_PATH_HINTS:
            if hint in (url or "").lower():
                return WebsiteValidation(
                    domain=domain,
                    valid=False,
                    reject_reason=RejectionReason.REPOSITORY,
                    evidence=[f"path:{hint}"],
                )

        status = http_status if http_status is not None else payload.get("http_status")
        alive = website_alive if website_alive is not None else payload.get("website_alive")
        text = (html_text or payload.get("website_html_text") or payload.get("website_title") or title or "").lower()

        if status is not None and int(status) >= 400:
            return WebsiteValidation(
                domain=domain,
                valid=False,
                http_status=int(status),
                reject_reason=RejectionReason.WEBSITE_INVALID,
                evidence=[f"http:{status}"],
            )
        if alive is False:
            return WebsiteValidation(
                domain=domain,
                valid=False,
                http_status=status,
                reject_reason=RejectionReason.WEBSITE_INVALID,
                evidence=["website_unreachable"],
            )

        if text:
            if any(h in text for h in PARKED_HINTS):
                return WebsiteValidation(
                    domain=domain,
                    valid=False,
                    http_status=status,
                    reject_reason=RejectionReason.PARKED_DOMAIN,
                    evidence=["parked_or_coming_soon"],
                )
            if any(h in text for h in DOCS_HINTS) and "pricing" not in text and "product" not in text:
                return WebsiteValidation(
                    domain=domain,
                    valid=False,
                    http_status=status,
                    reject_reason=RejectionReason.DOCUMENTATION,
                    evidence=["docs_site"],
                )
            if any(h in text for h in BLOG_HINTS) and "company" not in text and "product" not in text:
                return WebsiteValidation(
                    domain=domain,
                    valid=False,
                    http_status=status,
                    reject_reason=RejectionReason.PERSONAL_BLOG,
                    evidence=["personal_blog"],
                )

        # Heuristic pass when domain is non-platform and not explicitly dead
        evidence.append(f"domain_ok:{domain}")
        if status is None and alive is None:
            evidence.append("assumed_reachable_pending_fetch")
        return WebsiteValidation(
            domain=domain,
            valid=True,
            http_status=int(status) if status is not None else 200,
            ssl=bool(ssl if ssl is not None else payload.get("ssl", True)),
            title=title or payload.get("website_title"),
            evidence=evidence,
        )

    def _host_rejected(self, domain: str) -> bool:
        host = domain.lower().removeprefix("www.")
        if host in REJECT_HOST_HINTS:
            return True
        return any(host.endswith(f".{h}") for h in REJECT_HOST_HINTS)

    def _classify_host(self, domain: str) -> RejectionReason:
        host = domain.lower()
        if "github" in host:
            return RejectionReason.GITHUB_PAGES if "github.io" in host else RejectionReason.REPOSITORY
        if "medium.com" in host:
            return RejectionReason.MEDIUM
        if any(n in host for n in ("techcrunch", "reuters", "verge", "bloomberg", "nytimes", "forbes", "wired", "politico", "axios")):
            return RejectionReason.NEWS_SITE
        if any(n in host for n in ("reddit", "news.ycombinator", "stackoverflow", "stackexchange")):
            return RejectionReason.FORUM
        if any(n in host for n in ("readthedocs", "gitbook")):
            return RejectionReason.DOCUMENTATION
        if is_platform_domain(domain):
            return RejectionReason.PLATFORM_DOMAIN
        return RejectionReason.WEBSITE_INVALID
