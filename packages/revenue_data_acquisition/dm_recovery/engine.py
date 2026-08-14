"""Decision maker recovery — Team/About/Leadership pages only. No LinkedIn scraping."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from collectors.extraction.public_contacts import extract_public_contacts
from revenue_data_acquisition.models.types import UNKNOWN

# Prefer leadership pages. Avoid /customers and /blog — customer stories create false DMs.
DM_PATHS = (
    "/about",
    "/about-us",
    "/team",
    "/leadership",
    "/company",
    "/founder",
    "/founders",
    "/press/about",
    "",
)


class DecisionMakerRecoveryEngine:
    def recover(self, website: str, *, collector: str = UNKNOWN, timeout: float = 6.0) -> list[dict[str, Any]]:
        if not website:
            return []
        if not website.startswith("http"):
            website = f"https://{website}"
        parsed = urlparse(website)
        domain = parsed.netloc.lower().removeprefix("www.")
        base = f"{parsed.scheme}://{parsed.netloc}"
        people: list[dict[str, Any]] = []
        seen: set[str] = set()
        now = datetime.now(UTC).isoformat()
        try:
            with httpx.Client(
                timeout=timeout,
                follow_redirects=True,
                headers={"User-Agent": "BeaconRDAP/1.0 (+https://beacon.ai)"},
            ) as client:
                for path in DM_PATHS:
                    url = base if not path else urljoin(base + "/", path.lstrip("/"))
                    try:
                        resp = client.get(url)
                    except Exception:  # noqa: BLE001
                        continue
                    if resp.status_code >= 400 or len(resp.text) < 40:
                        continue
                    hit = extract_public_contacts(resp.text, page_url=url, domain=domain)
                    for dm in hit.get("decision_makers") or []:
                        key = f"{dm.get('name','').lower()}|{dm.get('role','').lower()}"
                        if key in seen or not dm.get("name"):
                            continue
                        seen.add(key)
                        people.append(
                            {
                                "name": dm["name"],
                                "role": dm.get("role") or UNKNOWN,
                                "evidence": ["role_pattern_on_page"],
                                "url": url,
                                "confidence": 78.0,
                                "verified_at": now,
                                "source": "company_website",
                                "collector": collector,
                            }
                        )
        except Exception:  # noqa: BLE001
            return people
        return people[:8]
