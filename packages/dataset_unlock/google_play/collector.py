"""Google Play developer discovery — public store pages only. Never invent emails/domains.

Phase 0: directory enrichment only — not an outbound lead source.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

import httpx

from collectors.events import NormalizedEvent
from intelligence.entity_resolution.platform_domains import is_platform_domain

# Curated high-signal package IDs (public listings). Expand via search later.
SEED_PACKAGES = (
    "com.notion.id",
    "com.slack",
    "com.asana.app",
    "com.todoist",
    "com.calendly.app",
    "io.intercom.android",
    "com.hubspot.android",
    "com.zendesk.android",
    "com.monday.monday",
    "com.clickup.mobile",
    "com.airtable.android",
    "com.figma.mirror",
    "com.canva.editor",
    "com.miro.miroboard",
    "com.linear.app",
)

DEV_URL_RE = re.compile(r'"developerWebsite"\s*:\s*"([^"]+)"')
DEV_EMAIL_RE = re.compile(r'"developerEmail"\s*:\s*"([^"]+)"')
DEV_NAME_RE = re.compile(r'"author(?:Name)?"\s*:\s*"([^"]+)"|"developerName"\s*:\s*"([^"]+)"')
PRIVACY_RE = re.compile(r'"privacyPolicyUrl"\s*:\s*"([^"]+)"')


def _host(url: str | None) -> str | None:
    if not url:
        return None
    from urllib.parse import urlparse

    raw = url if "://" in url else f"https://{url}"
    try:
        host = urlparse(raw.replace("\\u003d", "=").replace("\\u0026", "&")).netloc.lower().removeprefix("www.")
    except ValueError:
        return None
    if not host or is_platform_domain(host) or "play.google.com" in host:
        return None
    return host


class GooglePlayDeveloperCollector:
    source = "google_play"

    def __init__(
        self,
        *,
        max_items: int = 30,
        packages: tuple[str, ...] | None = None,
        lead_eligible: bool = False,
    ) -> None:
        self.max_items = max_items
        self.packages = packages or SEED_PACKAGES
        self.lead_eligible = lead_eligible

    def collect(self) -> list[NormalizedEvent]:
        events: list[NormalizedEvent] = []
        now = datetime.now(UTC)
        # Seed listings have no reliable post date — use epoch so freshness gate rejects them as leads
        content_at = datetime(2012, 1, 1, tzinfo=UTC)
        seen: set[str] = set()
        with httpx.Client(
            timeout=12.0,
            follow_redirects=True,
            headers={"User-Agent": "BeaconODU/1.0 (+https://beacon.ai)"},
        ) as client:
            for pkg in self.packages:
                if len(events) >= self.max_items:
                    break
                url = f"https://play.google.com/store/apps/details?id={pkg}&hl=en&gl=US"
                try:
                    resp = client.get(url)
                except Exception:  # noqa: BLE001
                    continue
                if resp.status_code >= 400:
                    continue
                html = resp.text
                m_web = DEV_URL_RE.search(html)
                website = m_web.group(1).encode().decode("unicode_escape") if m_web else None
                host = _host(website)
                if not host or host in seen:
                    continue
                seen.add(host)
                m_email = DEV_EMAIL_RE.search(html)
                email = m_email.group(1) if m_email else None
                # Only accept same-org developer email
                if email and not email.lower().endswith("@" + host) and not email.lower().endswith("." + host):
                    # still store as support if google-listed; prefer same domain later
                    pass
                m_name = DEV_NAME_RE.search(html)
                name = (m_name.group(1) or m_name.group(2)) if m_name else pkg
                privacy = PRIVACY_RE.search(html)
                meta: dict = {
                    "source_kind": "directory",
                    "lead_eligible": self.lead_eligible,
                    "enrichment_only": not self.lead_eligible,
                    "official_website": f"https://{host}",
                    "homepage": f"https://{host}",
                    "official_domain": host,
                    "domain": host,
                    "publisher": name,
                    "developer_name": name,
                    "support": email,
                    "privacy": privacy.group(1) if privacy else None,
                    "package_id": pkg,
                    "company_hints": [name],
                    "content_occurred_at": content_at.isoformat(),
                    "directory_signals": [f"Google Play listing: {pkg}"],
                    "buying_signals": [],
                    "website_attribution": {
                        "website": f"https://{host}",
                        "source": "google_play_store",
                        "confidence": 92.0,
                        "collector": self.source,
                        "verified_at": now.isoformat(),
                    },
                    "collector_version": "odu-google-play-v2-enrichment",
                }
                if email and ("@" + host) in email.lower():
                    meta["business_email"] = email.lower()
                    meta["emails"] = [email.lower()]
                    meta["email_verified_source"] = "google_play_developer"
                events.append(
                    NormalizedEvent(
                        source=self.source,
                        url=url,
                        title=str(name),
                        content=f"Google Play developer {name} ({pkg})",
                        published_at=content_at,
                        metadata=meta,
                    )
                )
        return events
