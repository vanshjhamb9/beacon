from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from revenue_data_recovery.models.types import AttributedValue, WebsiteRecoveryResult, UNKNOWN

REJECT_HOST_HINTS = (
    "github.com",
    "gist.github.com",
    "medium.com",
    "dev.to",
    "hashnode.dev",
    "substack.com",
    "blogspot.com",
    "wordpress.com",
    "notion.site",
    "readthedocs.io",
    "npmjs.com",
    "pypi.org",
    "crates.io",
    "arxiv.org",
    "stackoverflow.com",
    "reddit.com",
    "news.ycombinator.com",
    "wikipedia.org",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "facebook.com",
)

REJECT_PATH_HINTS = (
    "/blob/",
    "/pull/",
    "/issues/",
    "/tree/",
    "/commit/",
    "/readme",
    "/docs/",
    "/documentation",
    "/blog/",
    "/post/",
    "/article/",
    "/p/",
)

PARKED_HINTS = (
    "parked",
    "domain for sale",
    "buy this domain",
    "godaddy",
    "sedo.com",
    "hugedomains",
    "this domain is for sale",
)

SPAM_HINTS = ("casino", "crypto-airdrop", "viagra", "xxx", "payday-loan")

GITHUB_REPO_RE = re.compile(r"^https?://(www\.)?github\.com/[^/]+/[^/]+/?$", re.I)


class WebsiteRecoveryEngine:
    """Recover and verify company websites from existing evidence — never fabricate."""

    def recover(self, payload: dict[str, Any]) -> WebsiteRecoveryResult:
        candidates: list[tuple[str, str]] = []
        for source, value in self._candidate_pairs(payload):
            normalized = self._normalize_url(value)
            if normalized:
                candidates.append((source, normalized))

        # Deduplicate by host
        seen_hosts: set[str] = set()
        unique: list[tuple[str, str]] = []
        for source, url in candidates:
            host = self._host(url)
            if not host or host in seen_hosts:
                continue
            seen_hosts.add(host)
            unique.append((source, url))

        tried = [u for _, u in unique]
        evidence: list[str] = [f"candidates:{len(unique)}"]

        for source, url in unique:
            reject = self._reject_reason(url, payload)
            if reject:
                evidence.append(f"reject:{host}:{reject}" if (host := self._host(url)) else f"reject:{reject}")
                continue

            # Soft verification from payload flags / status codes when present
            status = payload.get("website_status") or payload.get("http_status")
            if status is not None and int(status) == 404:
                evidence.append(f"reject:404:{url}")
                continue
            if payload.get("is_parked") or self._parked(payload, url):
                evidence.append(f"reject:parked:{url}")
                continue
            if payload.get("is_spam") or self._spam(url):
                evidence.append(f"reject:spam:{url}")
                continue

            domain = self._host(url)
            conf = 90.0 if source in {"existing_website", "canonical_domain"} else 75.0
            if payload.get("website_verified") or payload.get("ssl"):
                conf = min(98.0, conf + 5.0)
            evidence.append(f"verified_from:{source}")
            return WebsiteRecoveryResult(
                verified_website=AttributedValue.of(
                    url,
                    source=source,
                    collected_at=payload.get("collected_at") or payload.get("last_seen_at"),
                    confidence=conf,
                    evidence=[f"website:{url}"],
                ),
                canonical_domain=AttributedValue.of(
                    domain,
                    source="canonical_homepage",
                    collected_at=payload.get("collected_at") or payload.get("last_seen_at"),
                    confidence=conf,
                    evidence=[f"domain:{domain}"],
                ),
                website_verified=True,
                confidence=conf,
                candidates_tried=tried,
                evidence=evidence + ["website_verified:true"],
            )

        reason = "no_valid_website_candidate"
        if not unique:
            reason = "no_website_candidates"
        return WebsiteRecoveryResult(
            website_verified=False,
            rejected_reason=reason,
            confidence=0.0,
            candidates_tried=tried,
            evidence=evidence + [f"rejected:{reason}"],
        )

    def _candidate_pairs(self, payload: dict[str, Any]) -> list[tuple[str, Any]]:
        pairs: list[tuple[str, Any]] = [
            ("existing_website", payload.get("website") or payload.get("primary_domain")),
            ("canonical_domain", payload.get("domain") or payload.get("canonical_domain")),
            ("company_metadata", payload.get("homepage") or payload.get("website_url")),
            ("source_url", payload.get("source_url")),
            ("rss_link", self._nested(payload, "rss", "link")),
            ("github_org", self._github_org_homepage(payload)),
            ("company_profile", self._nested(payload, "public_page", "website")),
            ("goap", self._nested(payload, "goap", "website")),
        ]
        for item in payload.get("evidence") or []:
            if isinstance(item, dict):
                for key in ("website", "url", "homepage", "domain"):
                    if item.get(key):
                        pairs.append(("opportunity_evidence", item.get(key)))
            elif isinstance(item, str) and ("http://" in item or "https://" in item or "." in item):
                pairs.append(("opportunity_evidence", item))
        for url in payload.get("collected_urls") or payload.get("urls") or []:
            pairs.append(("collected_urls", url))
        return pairs

    def _github_org_homepage(self, payload: dict[str, Any]) -> Any:
        org = payload.get("github_org") or self._nested(payload, "github", "org_url")
        if not org:
            return None
        raw = str(org).strip().lower()
        # Accept org URL only (not repo)
        if GITHUB_REPO_RE.match(raw):
            return None
        if "github.com/" in raw and raw.count("/") <= 3:
            # Prefer blog/homepage field if present
            return self._nested(payload, "github", "blog") or self._nested(payload, "github", "homepage")
        return None

    def _reject_reason(self, url: str, payload: dict[str, Any]) -> str | None:
        host = self._host(url) or ""
        path = urlparse(url).path.lower() if "://" in url else ""
        if any(h == host or host.endswith("." + h) for h in REJECT_HOST_HINTS):
            if host in {"github.com", "gist.github.com"}:
                return "github_not_company_website"
            if host in {"medium.com", "dev.to"}:
                return "personal_or_publishing_platform"
            return "non_business_host"
        if any(hint in path for hint in REJECT_PATH_HINTS):
            return "non_homepage_path"
        if GITHUB_REPO_RE.match(url):
            return "github_repository"
        entity = str(payload.get("entity_type") or "").lower()
        if entity in {"repository", "library", "framework", "documentation", "blog", "news"}:
            return f"rejected_entity_type:{entity}"
        return None

    def _parked(self, payload: dict[str, Any], url: str) -> bool:
        blob = " ".join(
            str(x).lower()
            for x in (
                payload.get("website_title"),
                payload.get("website_body_snippet"),
                payload.get("description"),
                url,
            )
            if x
        )
        return any(h in blob for h in PARKED_HINTS)

    def _spam(self, url: str) -> bool:
        return any(h in url.lower() for h in SPAM_HINTS)

    def _normalize_url(self, value: Any) -> str | None:
        if not value:
            return None
        raw = str(value).strip()
        if raw.startswith("//"):
            raw = "https:" + raw
        if "://" not in raw:
            # Domain-only
            if " " in raw or "/" in raw.strip("/"):
                # might be path-only garbage
                if not re.match(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}(/.*)?$", raw):
                    return None
            raw = f"https://{raw}"
        try:
            parsed = urlparse(raw)
        except Exception:  # noqa: BLE001
            return None
        host = (parsed.hostname or "").lower().removeprefix("www.")
        if not host or "." not in host:
            return None
        # Canonical homepage: scheme + host only
        return f"https://{host}"

    def _host(self, url: str) -> str | None:
        try:
            return (urlparse(url).hostname or "").lower().removeprefix("www.") or None
        except Exception:  # noqa: BLE001
            return None

    def _nested(self, payload: dict[str, Any], root: str, key: str) -> Any:
        block = payload.get(root)
        if isinstance(block, dict):
            return block.get(key)
        return None
