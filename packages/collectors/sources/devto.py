"""Dev.to — company signals only. Reject tutorials / personal blogs / opinion pieces."""

from __future__ import annotations

import re

import httpx

from collectors.events import NormalizedEvent
from collectors.extraction.public_contacts import recover_from_official_website
from collectors.sources.rss import RSSCollector
from entity_resolution.website_discovery.engine import OfficialWebsiteDiscoveryEngine
from intelligence.entity_resolution.platform_domains import is_platform_domain

TUTORIAL_CUES = (
    "how i ",
    "how to ",
    "tutorial",
    "beginner",
    "my journey",
    "i built",
    "opinion",
    "why you should",
    "tips for",
    "cheat sheet",
    "learning ",
)


class DevToCollector(RSSCollector):
    source = "devto"

    def __init__(self, http_client: httpx.AsyncClient, *, feed_urls: list[str], max_items: int) -> None:
        super().__init__(http_client, feed_urls=feed_urls, max_items=max_items, source=self.source)
        self._discovery = OfficialWebsiteDiscoveryEngine()

    async def collect(self) -> list[NormalizedEvent]:
        events = await super().collect()
        kept: list[NormalizedEvent] = []
        for event in events:
            title = (event.title or "").lower()
            body = (event.content or "").lower()
            if any(c in title or c in body[:400] for c in TUTORIAL_CUES):
                continue

            meta = dict(event.metadata or {})
            # Prefer author/org website from feed metadata if present and not a platform
            candidate = meta.get("canonical_website") or meta.get("organization_website") or meta.get("homepage")
            if candidate and not is_platform_domain(str(candidate).replace("https://", "").replace("http://", "").split("/")[0]):
                meta["official_website"] = candidate
                meta["domain"] = re.sub(r"^www\.", "", str(candidate).split("//")[-1].split("/")[0].lower())
            else:
                discovered = self._discovery.discover(
                    {
                        "source": "devto",
                        "url": event.url,
                        "title": event.title,
                        "body": event.content,
                        "metadata": meta,
                        "devto_website": meta.get("devto_website"),
                    }
                )
                if not discovered.discovered:
                    continue
                meta["official_website"] = discovered.website
                meta["domain"] = discovered.domain

            contacts = recover_from_official_website(str(meta["official_website"]))
            if contacts.get("emails"):
                meta["business_email"] = contacts["emails"][0]
                meta["emails"] = contacts["emails"]
            if contacts.get("decision_makers"):
                meta["decision_makers"] = contacts["decision_makers"]
                top = contacts["decision_makers"][0]
                meta["decision_maker"] = f"{top['name']} ({top['role']})"
            if contacts.get("about_excerpt"):
                meta["description"] = contacts["about_excerpt"]
            meta["ofc_devto_company"] = True
            kept.append(event.model_copy(update={"metadata": meta}))
        return kept
