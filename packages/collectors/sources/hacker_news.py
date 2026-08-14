"""Hacker News collector — fresh launch/hiring signals + website/contact recovery."""

from __future__ import annotations

from collections.abc import Sequence
from urllib.parse import urlparse

import httpx

from collectors.extraction.public_contacts import recover_from_official_website
from collectors.events import NormalizedEvent
from collectors.freshness import NEWS_OR_PLATFORM_HOSTS
from collectors.sources.rss import RSSCollector
from intelligence.entity_resolution.platform_domains import is_platform_domain


class HackerNewsCollector(RSSCollector):
    source = "hacker_news"

    def __init__(self, http_client: httpx.AsyncClient, *, feed_urls: list[str], max_items: int) -> None:
        super().__init__(
            http_client,
            feed_urls=feed_urls,
            max_items=max_items,
            source=self.source,
        )

    async def collect(self) -> Sequence[NormalizedEvent]:
        events = list(await super().collect())
        enriched: list[NormalizedEvent] = []
        for event in events:
            meta = dict(event.metadata or {})
            website = meta.get("official_website") or meta.get("homepage")
            if not website:
                # Prefer direct link host when it is a real company site
                try:
                    host = urlparse(event.url).netloc.lower().removeprefix("www.")
                    if (
                        host
                        and not is_platform_domain(host)
                        and host not in NEWS_OR_PLATFORM_HOSTS
                        and "ycombinator.com" not in host
                    ):
                        website = f"https://{host}"
                except Exception:  # noqa: BLE001
                    website = None

            if website:
                host = urlparse(website).netloc.lower().removeprefix("www.")
                if host in NEWS_OR_PLATFORM_HOSTS or is_platform_domain(host):
                    meta["article_only"] = True
                    meta["ofc_skip_company"] = True
                    meta["ofc_reason"] = "news_or_platform_host"
                    enriched.append(event.model_copy(update={"metadata": meta}))
                    continue
                meta["official_website"] = website
                meta["homepage"] = website
                meta["official_domain"] = host
                meta["domain"] = host
                meta["article_only"] = False
                meta["website_attribution"] = {
                    "website": website,
                    "source": "hacker_news_link",
                    "confidence": 88.0,
                    "collector": self.source,
                }
                contacts = recover_from_official_website(str(website))
                if contacts.get("about_excerpt"):
                    meta["about"] = contacts["about_excerpt"]
                    meta["description"] = contacts["about_excerpt"]
                if contacts.get("emails"):
                    meta["business_email"] = contacts["emails"][0]
                    meta["emails"] = contacts["emails"]
                    meta["email_verified_source"] = "company_website"
                if contacts.get("decision_makers"):
                    # Prefer plausible person names
                    dms = [
                        dm
                        for dm in contacts["decision_makers"]
                        if _plausible_person(str(dm.get("name") or ""))
                    ]
                    if dms:
                        meta["decision_makers"] = dms
                        top = dms[0]
                        meta["decision_maker"] = f"{top['name']} ({top['role']})"
                if contacts.get("linkedin"):
                    meta["linkedin"] = contacts["linkedin"]
                meta["contact_pages"] = contacts.get("pages_fetched") or []
                meta["ofc_hn_recovered"] = True

            blob = f"{event.title} {event.content}".lower()
            signals = list(meta.get("buying_signals") or [])
            if any(k in blob for k in ("hiring", "who's hiring", "is hiring")):
                signals.append(f"HN hiring signal: {event.title[:100]}")
            if any(k in blob for k in ("launch hn", "show hn", "launch")):
                signals.append(f"HN launch signal: {event.title[:100]}")
            if any(k in blob for k in ("funding", "raised", "series")):
                signals.append(f"HN funding signal: {event.title[:100]}")
            meta["buying_signals"] = list(dict.fromkeys(signals))[:5]
            meta["source_kind"] = "event"
            meta["lead_eligible"] = True
            enriched.append(event.model_copy(update={"metadata": meta}))
        return enriched


def _plausible_person(name: str) -> bool:
    parts = [p for p in name.strip().split() if p]
    if len(parts) < 2 or len(parts) > 4:
        return False
    blocked = {
        "rankings",
        "function",
        "team",
        "about",
        "company",
        "report",
        "latest",
        "institute",
        "university",
        "college",
        "foundation",
        "inc",
        "llc",
    }
    if any(p.lower().rstrip(".") in blocked for p in parts):
        return False
    return all(p[:1].isupper() for p in parts)
