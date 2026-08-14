"""Company website intelligence — crawl public pages; attributed evidence only."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from identity_coverage.models.types import CoverageEvidence, UNKNOWN
from collectors.extraction.public_contacts import extract_public_contacts

PATHS = ("", "/about", "/about-us", "/company", "/team", "/careers", "/contact", "/contact-us", "/privacy", "/terms", "/press", "/customers")
OG_RE = re.compile(r'property=["\']og:(?:url|site_name|description)["\']\s+content=["\']([^"\']+)["\']', re.I)
JSONLD_ORG = re.compile(r'"@type"\s*:\s*"(?:Organization|Corporation)"', re.I)
LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/company/[A-Za-z0-9\-_/]+", re.I)
TWITTER_RE = re.compile(r"https?://(?:www\.)?(?:twitter|x)\.com/[A-Za-z0-9_]+", re.I)
GITHUB_RE = re.compile(r"https?://(?:www\.)?github\.com/[A-Za-z0-9_.\-]+", re.I)


def _now() -> str:
    return datetime.now(UTC).isoformat()


class WebsiteIntelligenceEngine:
    name = "website_intelligence"
    priority = 20

    def collect(self, payload: dict[str, Any], *, timeout: float = 6.0, max_pages: int = 8) -> list[CoverageEvidence]:
        website = (
            payload.get("official_website")
            or payload.get("website")
            or (payload.get("metadata") or {}).get("official_website")
        )
        if not website:
            return []
        if not str(website).startswith("http"):
            website = f"https://{website}"
        parsed = urlparse(str(website))
        domain = parsed.netloc.lower().removeprefix("www.")
        if not domain:
            return []
        base = f"{parsed.scheme or 'https'}://{parsed.netloc}"
        out: list[CoverageEvidence] = []
        try:
            with httpx.Client(
                timeout=timeout,
                follow_redirects=True,
                headers={"User-Agent": "BeaconICE/1.0 (+https://beacon.ai)"},
            ) as client:
                for path in PATHS:
                    if len([e for e in out if e.reason.startswith("page:")]) >= max_pages:
                        break
                    url = base if not path else urljoin(base + "/", path.lstrip("/"))
                    try:
                        resp = client.get(url)
                    except Exception:  # noqa: BLE001
                        continue
                    if resp.status_code >= 400 or len(resp.text) < 40:
                        continue
                    html = resp.text
                    out.append(
                        CoverageEvidence(
                            field="page_fetched",
                            value=url,
                            confidence=80.0,
                            collector=str(payload.get("source") or UNKNOWN),
                            timestamp=_now(),
                            verification=True,
                            source=self.name,
                            priority=self.priority,
                            reason=f"page:{path or '/'}",
                            evidence=[f"status:{resp.status_code}"],
                        )
                    )
                    contacts = extract_public_contacts(html, page_url=url, domain=domain)
                    for email in contacts.get("emails") or []:
                        out.append(
                            CoverageEvidence(
                                field="business_email",
                                value=email,
                                confidence=92.0,
                                collector=str(payload.get("source") or UNKNOWN),
                                timestamp=_now(),
                                verification=True,
                                source=self.name,
                                priority=12,
                                reason="same_domain_email",
                                evidence=[f"page:{url}"],
                            )
                        )
                    for dm in contacts.get("decision_makers") or []:
                        out.append(
                            CoverageEvidence(
                                field="decision_maker",
                                value=f"{dm.get('name')} ({dm.get('role')})",
                                confidence=78.0,
                                collector=str(payload.get("source") or UNKNOWN),
                                timestamp=_now(),
                                verification=True,
                                source=self.name,
                                priority=15,
                                reason="role_on_page",
                                evidence=[f"page:{url}"],
                            )
                        )
                    for li in LINKEDIN_RE.findall(html)[:2]:
                        out.append(
                            CoverageEvidence(
                                field="linkedin_company",
                                value=li,
                                confidence=88.0,
                                collector=str(payload.get("source") or UNKNOWN),
                                timestamp=_now(),
                                verification=True,
                                source=self.name,
                                priority=18,
                                reason="linkedin_on_site",
                                evidence=[f"page:{url}"],
                            )
                        )
                    if JSONLD_ORG.search(html):
                        out.append(
                            CoverageEvidence(
                                field="schema_org",
                                value="Organization",
                                confidence=75.0,
                                collector=str(payload.get("source") or UNKNOWN),
                                timestamp=_now(),
                                verification=True,
                                source=self.name,
                                priority=25,
                                reason="json_ld_organization",
                                evidence=[f"page:{url}"],
                            )
                        )
                    for m in OG_RE.finditer(html):
                        out.append(
                            CoverageEvidence(
                                field="open_graph",
                                value=m.group(1)[:500],
                                confidence=70.0,
                                collector=str(payload.get("source") or UNKNOWN),
                                timestamp=_now(),
                                verification=True,
                                source=self.name,
                                priority=30,
                                reason="open_graph",
                                evidence=[f"page:{url}"],
                            )
                        )
        except Exception:  # noqa: BLE001
            return out
        return out
