"""GitHub identity resolver — per-repo/org homepage; never invent domains."""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from identity_coverage.models.types import CoverageEvidence, UNKNOWN
from intelligence.entity_resolution.platform_domains import is_platform_domain

API = "https://api.github.com"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _host(url: str | None) -> str | None:
    if not url:
        return None
    raw = str(url).strip()
    if not raw:
        return None
    if not raw.startswith("http"):
        raw = f"https://{raw}"
    try:
        host = urlparse(raw).netloc.lower().removeprefix("www.")
    except ValueError:
        return None
    if not host or is_platform_domain(host) or host.endswith("github.io") or "github.com" in host:
        return None
    return host


class GitHubIdentityResolver:
    name = "github_identity"
    priority = 15

    def __init__(self, *, token: str | None = None, client: httpx.Client | None = None) -> None:
        self.token = (token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or "").strip()
        self._client = client

    def _headers(self) -> dict[str, str]:
        h = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "BeaconICE/1.0 (+https://beacon.ai)",
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def parse_repo(self, payload: dict[str, Any]) -> tuple[str, str] | None:
        url = str(payload.get("url") or "")
        m = re.search(r"github\.com/([^/]+)/([^/#?]+)", url, re.I)
        if m:
            return m.group(1), m.group(2).removesuffix(".git")
        title = str(payload.get("title") or "")
        if "GitHub:" in title:
            slug = title.split("GitHub:", 1)[-1].strip()
            if "/" in slug:
                owner, repo = slug.split("/", 1)
                return owner.strip(), repo.strip()
        return None

    def fetch_repo(self, owner: str, repo: str) -> dict[str, Any] | None:
        try:
            if self._client:
                resp = self._client.get(f"{API}/repos/{owner}/{repo}", headers=self._headers())
            else:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(f"{API}/repos/{owner}/{repo}", headers=self._headers())
            if resp.status_code >= 400:
                return None
            return resp.json()
        except Exception:  # noqa: BLE001
            return None

    def fetch_org(self, owner: str) -> dict[str, Any] | None:
        try:
            if self._client:
                resp = self._client.get(f"{API}/orgs/{owner}", headers=self._headers())
            else:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(f"{API}/orgs/{owner}", headers=self._headers())
            if resp.status_code >= 400:
                return None
            return resp.json()
        except Exception:  # noqa: BLE001
            return None

    def collect(self, payload: dict[str, Any], *, fetch_live: bool = False) -> list[CoverageEvidence]:
        if str(payload.get("source") or "").lower() not in {"github_trending", "github"}:
            return []
        out: list[CoverageEvidence] = []
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}

        # Explicit metadata first (collector already recovered)
        for key, conf in (
            ("repo_homepage", 94.0),
            ("official_website", 96.0),
            ("homepage", 90.0),
            ("github_homepage", 92.0),
        ):
            host = _host(str(meta.get(key) or payload.get(key) or ""))
            if host:
                out.append(
                    CoverageEvidence(
                        field="website",
                        value=f"https://{host}",
                        confidence=conf,
                        collector="github_trending",
                        timestamp=_now(),
                        verification=True,
                        source=self.name,
                        priority=self.priority,
                        reason=f"github_field:{key}",
                        evidence=[f"domain:{host}"],
                    )
                )
                out.append(
                    CoverageEvidence(
                        field="official_domain",
                        value=host,
                        confidence=conf,
                        collector="github_trending",
                        timestamp=_now(),
                        verification=True,
                        source=self.name,
                        priority=self.priority,
                        reason=f"github_field:{key}",
                        evidence=[f"key:{key}"],
                    )
                )
                break

        parsed = self.parse_repo(payload)
        if fetch_live and parsed and not out:
            owner, repo = parsed
            data = self.fetch_repo(owner, repo)
            if data:
                host = _host(data.get("homepage"))
                if host:
                    out.append(
                        CoverageEvidence(
                            field="website",
                            value=f"https://{host}",
                            confidence=93.0,
                            collector="github_trending",
                            timestamp=_now(),
                            verification=True,
                            source=self.name,
                            priority=self.priority,
                            reason="github_api_repo_homepage",
                            evidence=[f"repo:{owner}/{repo}", f"domain:{host}"],
                        )
                    )
                    out.append(
                        CoverageEvidence(
                            field="official_domain",
                            value=host,
                            confidence=93.0,
                            collector="github_trending",
                            timestamp=_now(),
                            verification=True,
                            source=self.name,
                            priority=self.priority,
                            reason="github_api_repo_homepage",
                            evidence=[f"repo:{owner}/{repo}"],
                        )
                    )
                if data.get("language"):
                    out.append(
                        CoverageEvidence(
                            field="language",
                            value=str(data["language"]),
                            confidence=85.0,
                            collector="github_trending",
                            timestamp=_now(),
                            verification=True,
                            source=self.name,
                            priority=40,
                            reason="github_api_language",
                            evidence=[f"repo:{owner}/{repo}"],
                        )
                    )
                if data.get("stargazers_count") is not None:
                    out.append(
                        CoverageEvidence(
                            field="stars",
                            value=str(data["stargazers_count"]),
                            confidence=90.0,
                            collector="github_trending",
                            timestamp=_now(),
                            verification=True,
                            source=self.name,
                            priority=40,
                            reason="github_api_stars",
                            evidence=[f"repo:{owner}/{repo}"],
                        )
                    )
                owner_obj = data.get("owner") or {}
                if owner_obj.get("type") == "Organization":
                    org = self.fetch_org(owner)
                    org_host = _host((org or {}).get("blog")) if org else None
                    if org_host and not any(e.field == "website" for e in out):
                        out.append(
                            CoverageEvidence(
                                field="website",
                                value=f"https://{org_host}",
                                confidence=91.0,
                                collector="github_trending",
                                timestamp=_now(),
                                verification=True,
                                source=self.name,
                                priority=self.priority,
                                reason="github_api_org_blog",
                                evidence=[f"org:{owner}", f"domain:{org_host}"],
                            )
                        )
                    out.append(
                        CoverageEvidence(
                            field="github_organization",
                            value=owner,
                            confidence=88.0,
                            collector="github_trending",
                            timestamp=_now(),
                            verification=True,
                            source=self.name,
                            priority=25,
                            reason="github_owner_organization",
                            evidence=[f"org:{owner}"],
                        )
                    )
        return out
