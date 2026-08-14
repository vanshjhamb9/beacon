"""GitHub enterprise discovery — homepage, org website, README links. Never invent."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import httpx

from identity_coverage.github.engine import GitHubIdentityResolver, _host
from intelligence.entity_resolution.platform_domains import is_platform_domain

README_URL_RE = re.compile(r"https?://[^\s\)\]\>\"']+", re.I)
SKIP_HOSTS = ("github.com", "githubusercontent.com", "youtube.com", "twitter.com", "x.com", "linkedin.com")


class GitHubEnterpriseDiscovery:
    def __init__(self) -> None:
        self.resolver = GitHubIdentityResolver()

    def discover(self, payload: dict[str, Any], *, fetch_live: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "repo_homepage": None,
            "organization_website": None,
            "verified_organization": False,
            "readme_company_links": [],
            "releases_count": 0,
            "website": None,
            "domain": None,
            "trail": [],
        }
        evidence = self.resolver.collect(payload, fetch_live=fetch_live)
        for ev in evidence:
            if ev.field == "website" and not out["website"]:
                out["website"] = ev.value
                out["domain"] = _host(ev.value)
                out["trail"].append(ev.reason)
            if ev.field == "official_domain" and not out["domain"]:
                out["domain"] = ev.value
            if "org" in (ev.reason or ""):
                out["organization_website"] = ev.value
                out["verified_organization"] = True

        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        for key in ("repo_homepage", "homepage", "official_website"):
            host = _host(str(meta.get(key) or payload.get(key) or ""))
            if host and not out["repo_homepage"]:
                out["repo_homepage"] = f"https://{host}"

        parsed = self.resolver.parse_repo(payload)
        if fetch_live and parsed and self.resolver.token:
            owner, repo = parsed
            readme_links = self._readme_links(owner, repo)
            out["readme_company_links"] = readme_links
            if not out["website"] and readme_links:
                out["website"] = readme_links[0]
                out["domain"] = _host(readme_links[0])
                out["trail"].append("readme_company_link")
            releases = self._releases_count(owner, repo)
            out["releases_count"] = releases
            org = self.resolver.fetch_org(owner)
            if org and org.get("type") != "User":
                out["verified_organization"] = True
                blog_host = _host(org.get("blog"))
                if blog_host:
                    out["organization_website"] = f"https://{blog_host}"
                    if not out["website"]:
                        out["website"] = out["organization_website"]
                        out["domain"] = blog_host
                        out["trail"].append("github_org_blog")
        return out

    def _readme_links(self, owner: str, repo: str) -> list[str]:
        try:
            with httpx.Client(timeout=10.0, headers=self.resolver._headers()) as client:
                resp = client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/readme",
                    headers={**self.resolver._headers(), "Accept": "application/vnd.github.raw"},
                )
            if resp.status_code >= 400:
                return []
            links: list[str] = []
            for m in README_URL_RE.findall(resp.text or ""):
                try:
                    host = urlparse(m).netloc.lower().removeprefix("www.")
                except ValueError:
                    continue
                if not host or is_platform_domain(host) or any(s in host for s in SKIP_HOSTS):
                    continue
                url = m.rstrip(".,);]")
                if url not in links:
                    links.append(url)
                if len(links) >= 3:
                    break
            return links
        except Exception:  # noqa: BLE001
            return []

    def _releases_count(self, owner: str, repo: str) -> int:
        try:
            with httpx.Client(timeout=8.0, headers=self.resolver._headers()) as client:
                resp = client.get(f"https://api.github.com/repos/{owner}/{repo}/releases", params={"per_page": 5})
            if resp.status_code >= 400:
                return 0
            data = resp.json()
            return len(data) if isinstance(data, list) else 0
        except Exception:  # noqa: BLE001
            return 0
