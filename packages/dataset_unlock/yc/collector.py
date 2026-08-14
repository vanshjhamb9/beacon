"""Y Combinator company discovery — public directory JSON (yc-oss Algolia mirror).

Phase 0: directory enrichment only — never opens outbound leads.
Events are tagged source_kind=directory / lead_eligible=false.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from collectors.events import NormalizedEvent
from intelligence.entity_resolution.platform_domains import is_platform_domain

# Community mirror of YC public Algolia directory — websites + founders attributed to YC listing
YC_HIRING = "https://yc-oss.github.io/api/companies/hiring.json"
YC_TOP = "https://yc-oss.github.io/api/companies/top.json"

_BATCH_SEASON = {"Winter": 1, "Summer": 6, "Fall": 9, "Spring": 3}


def _host(url: str | None) -> str | None:
    if not url:
        return None
    raw = str(url).strip()
    if not raw.startswith("http"):
        raw = f"https://{raw}"
    try:
        host = urlparse(raw).netloc.lower().removeprefix("www.")
    except ValueError:
        return None
    if not host or is_platform_domain(host) or "ycombinator.com" in host:
        return None
    return host


def _batch_start(batch: Any) -> datetime | None:
    """Approximate YC batch start — historical, not a buying trigger."""
    text = str(batch or "").strip()
    if not text:
        return None
    parts = text.split()
    if len(parts) < 2:
        return None
    season, year_s = parts[0], parts[1]
    try:
        year = int(year_s)
        month = _BATCH_SEASON.get(season, 1)
        return datetime(year, month, 1, tzinfo=UTC)
    except ValueError:
        return None


class YCCompanyCollector:
    source = "yc"

    def __init__(self, *, max_items: int = 120, lead_eligible: bool = False) -> None:
        self.max_items = max_items
        self.lead_eligible = lead_eligible

    def collect(self) -> list[NormalizedEvent]:
        rows: list[dict[str, Any]] = []
        with httpx.Client(timeout=45.0, headers={"User-Agent": "BeaconODU/1.0"}) as client:
            for url in (YC_HIRING, YC_TOP):
                try:
                    resp = client.get(url)
                    if resp.status_code >= 400:
                        continue
                    data = resp.json()
                    if isinstance(data, list):
                        rows.extend(data)
                    elif isinstance(data, dict) and isinstance(data.get("companies"), list):
                        rows.extend(data["companies"])
                except Exception:  # noqa: BLE001
                    continue
        events: list[NormalizedEvent] = []
        seen: set[str] = set()
        now = datetime.now(UTC)
        for row in rows:
            if not isinstance(row, dict):
                continue
            host = _host(row.get("website"))
            if not host or host in seen:
                continue
            seen.add(host)
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            founders = self._founders_from_row(row)
            slug = row.get("slug") or name.lower().replace(" ", "-")
            yc_url = str(row.get("url") or f"https://www.ycombinator.com/companies/{slug}")
            is_hiring = bool(row.get("isHiring") or row.get("is_hiring"))
            batch = row.get("batch")
            batch_at = _batch_start(batch)
            # Honest content time = batch start (often years ago). Never stamp now.
            content_at = batch_at or datetime(2005, 1, 1, tzinfo=UTC)
            meta: dict[str, Any] = {
                "source_kind": "directory",
                "lead_eligible": self.lead_eligible,
                "enrichment_only": not self.lead_eligible,
                "official_website": f"https://{host}",
                "homepage": f"https://{host}",
                "official_domain": host,
                "domain": host,
                "description": row.get("long_description") or row.get("one_liner"),
                "industry": (
                    (row.get("industries") or [None])[0]
                    if isinstance(row.get("industries"), list)
                    else row.get("industry")
                ),
                "batch": batch,
                "content_occurred_at": content_at.isoformat(),
                "location": row.get("all_locations") or row.get("location"),
                "founders": founders,
                "company_hints": [name],
                # Directory membership is NOT a buying signal for outreach
                "directory_signals": [
                    f"YC company directory: {batch or 'batch unknown'}",
                    "YC hiring flag" if is_hiring else "YC portfolio listing",
                ],
                "buying_signals": (
                    [f"YC hiring flag (verify job post date): {name}"] if is_hiring else []
                ),
                "website_attribution": {
                    "website": f"https://{host}",
                    "source": "yc_directory",
                    "confidence": 97.0,
                    "collector": self.source,
                    "verified_at": now.isoformat(),
                },
                "collector_version": "odu-yc-v2-enrichment",
                "confidence": 90.0,
            }
            if founders:
                top = founders[0]
                meta["decision_maker"] = f"{top['name']} ({top['role']})"
                meta["decision_makers"] = founders[:5]
            events.append(
                NormalizedEvent(
                    source=self.source,
                    url=yc_url,
                    title=name,
                    content=str(row.get("one_liner") or row.get("long_description") or name)[:2000],
                    published_at=content_at,
                    metadata=meta,
                )
            )
            if len(events) >= self.max_items:
                break
        return events

    def _founders_from_row(self, row: dict[str, Any]) -> list[dict[str, str]]:
        founders: list[dict[str, str]] = []
        for f in row.get("founders") or []:
            if isinstance(f, dict) and (f.get("full_name") or f.get("name")):
                founders.append(
                    {
                        "name": str(f.get("full_name") or f.get("name")),
                        "role": str(f.get("title") or f.get("role") or "Founder"),
                        "source": "yc_directory",
                    }
                )
        return founders
