"""Concrete identity providers — extract evidence from payload / composed discovery only."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from identity_graph.models.types import IdentityEvidence, UNKNOWN
from intelligence.entity_resolution.platform_domains import is_platform_domain


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _host(url: str | None) -> str | None:
    if not url:
        return None
    raw = url if "://" in url else f"https://{url}"
    try:
        host = urlparse(raw).netloc.lower().removeprefix("www.")
    except ValueError:
        return None
    if not host or is_platform_domain(host):
        return None
    return host


class OfficialWebsiteProvider:
    name = "official_website"

    def collect(self, payload: dict[str, Any]) -> list[IdentityEvidence]:
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        out: list[IdentityEvidence] = []
        for key, conf in (
            ("official_website", 96.0),
            ("product_website", 94.0),
            ("homepage", 90.0),
            ("repo_homepage", 92.0),
            ("canonical_website", 88.0),
            ("organization_website", 88.0),
        ):
            value = payload.get(key) or meta.get(key)
            host = _host(str(value) if value else None)
            if not host:
                continue
            website = f"https://{host}"
            out.append(
                IdentityEvidence(
                    source=self.name,
                    field="website",
                    value=website,
                    confidence=conf,
                    collector=str(payload.get("source") or UNKNOWN),
                    timestamp=_now(),
                    verified=True,
                    reason=f"explicit_field:{key}",
                    evidence=[f"key:{key}", f"domain:{host}"],
                )
            )
            out.append(
                IdentityEvidence(
                    source=self.name,
                    field="official_domain",
                    value=host,
                    confidence=conf,
                    collector=str(payload.get("source") or UNKNOWN),
                    timestamp=_now(),
                    verified=True,
                    reason=f"explicit_field:{key}",
                    evidence=[f"key:{key}"],
                )
            )
            break
        return out


class LinkedInCompanyProvider:
    name = "linkedin_company"

    def collect(self, payload: dict[str, Any]) -> list[IdentityEvidence]:
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        value = meta.get("linkedin_company") or payload.get("linkedin_company") or meta.get("linkedin")
        if not value or "linkedin.com/company/" not in str(value).lower():
            return []
        return [
            IdentityEvidence(
                source=self.name,
                field="linkedin_company_url",
                value=str(value),
                confidence=85.0,
                collector=str(payload.get("source") or UNKNOWN),
                timestamp=_now(),
                verified=True,
                reason="linkedin_company_url_present",
                evidence=["linkedin_company"],
            )
        ]


class GitHubOrganizationProvider:
    name = "github_organization"

    def collect(self, payload: dict[str, Any]) -> list[IdentityEvidence]:
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        out: list[IdentityEvidence] = []
        owner = meta.get("owner") or payload.get("owner")
        owner_type = str(meta.get("owner_type") or "").lower()
        if owner and owner_type == "organization":
            out.append(
                IdentityEvidence(
                    source=self.name,
                    field="github_organization",
                    value=str(owner),
                    confidence=80.0,
                    collector=str(payload.get("source") or UNKNOWN),
                    timestamp=_now(),
                    verified=True,
                    reason="github_owner_organization",
                    evidence=[f"owner:{owner}"],
                )
            )
        homepage = meta.get("repo_homepage") or meta.get("github_homepage") or payload.get("github_homepage")
        host = _host(str(homepage) if homepage else None)
        if host:
            out.append(
                IdentityEvidence(
                    source=self.name,
                    field="website",
                    value=f"https://{host}",
                    confidence=92.0,
                    collector=str(payload.get("source") or UNKNOWN),
                    timestamp=_now(),
                    verified=True,
                    reason="github_repository_homepage",
                    evidence=[f"domain:{host}"],
                )
            )
        return out


class CrunchbaseProvider:
    name = "crunchbase"

    def collect(self, payload: dict[str, Any]) -> list[IdentityEvidence]:
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        value = meta.get("crunchbase") or payload.get("crunchbase")
        if not value or "crunchbase.com" not in str(value).lower():
            return []
        return [
            IdentityEvidence(
                source=self.name,
                field="crunchbase",
                value=str(value),
                confidence=90.0,
                collector=str(payload.get("source") or UNKNOWN),
                timestamp=_now(),
                verified=True,
                reason="crunchbase_url_present",
                evidence=["crunchbase"],
            )
        ]


class WebsiteMetadataProvider:
    name = "website_metadata"

    def collect(self, payload: dict[str, Any]) -> list[IdentityEvidence]:
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        out: list[IdentityEvidence] = []
        for field in ("industry", "country", "description", "employee_range", "founded"):
            value = payload.get(field) or meta.get(field)
            if value and str(value).strip() and str(value).lower() != UNKNOWN:
                out.append(
                    IdentityEvidence(
                        source=self.name,
                        field=field,
                        value=str(value)[:2000],
                        confidence=70.0,
                        collector=str(payload.get("source") or UNKNOWN),
                        timestamp=_now(),
                        verified=False,
                        reason=f"metadata:{field}",
                        evidence=[f"field:{field}"],
                    )
                )
        return out


class DnsProvider:
    """Records DNS verification evidence when validation flags are present — never invents domains."""

    name = "dns"

    def collect(self, payload: dict[str, Any]) -> list[IdentityEvidence]:
        if not payload.get("website_verified") and not payload.get("dns_ok"):
            return []
        domain = payload.get("official_domain") or (payload.get("metadata") or {}).get("official_domain")
        host = _host(str(domain) if domain else None) or _host(str(payload.get("official_website") or ""))
        if not host:
            return []
        return [
            IdentityEvidence(
                source=self.name,
                field="dns_ok",
                value=host,
                confidence=75.0,
                collector=str(payload.get("source") or UNKNOWN),
                timestamp=_now(),
                verified=bool(payload.get("website_verified") or payload.get("dns_ok")),
                reason="dns_or_website_verified_flag",
                evidence=["dns_provider"],
            )
        ]


class SchemaOrgProvider:
    name = "schema_org"

    def collect(self, payload: dict[str, Any]) -> list[IdentityEvidence]:
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        value = meta.get("schema_org_url") or payload.get("schema_org_url")
        host = _host(str(value) if value else None)
        if not host:
            return []
        return [
            IdentityEvidence(
                source=self.name,
                field="website",
                value=str(value) if str(value).startswith("http") else f"https://{host}",
                confidence=78.0,
                collector=str(payload.get("source") or UNKNOWN),
                timestamp=_now(),
                verified=True,
                reason="schema_org_organization_url",
                evidence=[f"domain:{host}"],
            )
        ]


class OpenGraphProvider:
    name = "open_graph"

    def collect(self, payload: dict[str, Any]) -> list[IdentityEvidence]:
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        value = meta.get("og_url") or payload.get("og_url")
        host = _host(str(value) if value else None)
        if not host:
            return []
        return [
            IdentityEvidence(
                source=self.name,
                field="website",
                value=str(value) if str(value).startswith("http") else f"https://{host}",
                confidence=72.0,
                collector=str(payload.get("source") or UNKNOWN),
                timestamp=_now(),
                verified=True,
                reason="open_graph_url",
                evidence=[f"domain:{host}"],
            )
        ]


DEFAULT_PROVIDERS = (
    OfficialWebsiteProvider(),
    GitHubOrganizationProvider(),
    LinkedInCompanyProvider(),
    CrunchbaseProvider(),
    WebsiteMetadataProvider(),
    DnsProvider(),
    SchemaOrgProvider(),
    OpenGraphProvider(),
)
