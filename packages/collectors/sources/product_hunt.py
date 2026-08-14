"""Product Hunt collector — official website + public contact recovery. Never invent."""

from __future__ import annotations

import httpx

from collectors.events import NormalizedEvent
from collectors.extraction.public_contacts import recover_from_official_website
from collectors.sources.rss import RSSCollector
from entity_resolution.website_discovery.engine import OfficialWebsiteDiscoveryEngine
from identity_coverage.product_hunt.engine import ProductHuntApiResolver


class ProductHuntCollector(RSSCollector):
    source = "product_hunt"

    def __init__(self, http_client: httpx.AsyncClient, *, feed_urls: list[str], max_items: int) -> None:
        super().__init__(
            http_client,
            feed_urls=feed_urls,
            max_items=max_items,
            source=self.source,
        )
        self._discovery = OfficialWebsiteDiscoveryEngine()
        self._ph_api = ProductHuntApiResolver()

    async def collect(self) -> list[NormalizedEvent]:
        events = await super().collect()
        enriched: list[NormalizedEvent] = []
        for event in events:
            meta = dict(event.metadata or {})
            if str(meta.get("domain") or "").endswith("producthunt.com"):
                meta.pop("domain", None)

            # ICE: official GraphQL API first (no Cloudflare HTML)
            api_payload = {
                "source": "product_hunt",
                "url": event.url,
                "title": event.title,
                "body": event.content,
                "content": event.content,
                "metadata": meta,
            }
            for ev in self._ph_api.collect(api_payload):
                if ev.field == "website":
                    meta["official_website"] = ev.value
                    meta["product_website"] = ev.value
                    meta["homepage"] = ev.value
                elif ev.field == "official_domain":
                    meta["official_domain"] = ev.value
                    meta["domain"] = ev.value
                elif ev.field == "maker":
                    meta.setdefault("makers", [])
                    if ev.value not in meta["makers"]:
                        meta["makers"].append(ev.value)
                    meta["ph_maker"] = meta.get("ph_maker") or ev.value
                elif ev.field == "ph_post_id":
                    meta["ph_post_id"] = ev.value
                elif ev.field == "description":
                    meta["description"] = ev.value
                elif ev.field == "tagline":
                    meta["tagline"] = ev.value
                elif ev.field == "blocker":
                    meta["ice_ph_blocker"] = ev.value

            # Follow Product Hunt redirect to official site when API token missing
            if not meta.get("official_website") and meta.get("ph_redirect_url"):
                try:
                    from urllib.parse import urlparse

                    from intelligence.entity_resolution.platform_domains import is_platform_domain

                    resp = await self.http_client.head(str(meta["ph_redirect_url"]), follow_redirects=True)
                    final = str(resp.url)
                    host = urlparse(final).netloc.lower().removeprefix("www.")
                    if host and not is_platform_domain(host) and "producthunt.com" not in host:
                        meta["official_website"] = f"https://{host}"
                        meta["homepage"] = f"https://{host}"
                        meta["official_domain"] = host
                        meta["domain"] = host
                        meta["website_attribution"] = {
                            "website": f"https://{host}",
                            "source": "product_hunt_redirect",
                            "confidence": 90.0,
                            "collector": "product_hunt",
                        }
                except Exception:  # noqa: BLE001
                    pass

            if meta.get("official_website") and meta.get("domain"):
                discovered_domain = meta["domain"]
                discovered_website = meta["official_website"]
            else:
                discovered = self._discovery.discover(
                    {
                        "source": "product_hunt",
                        "url": event.url,
                        "title": event.title,
                        "body": event.content,
                        "metadata": meta,
                        "fetch_official_website": True,
                        "fetch_product_hunt": True,
                    }
                )
                if not (discovered.discovered and discovered.domain):
                    meta["ofc_skip_company"] = True
                    meta["ofc_reason"] = "no_official_website"
                    if meta.get("ph_redirect_url") or meta.get("ph_post_id"):
                        meta["ofc_blocker"] = meta.get("ice_ph_blocker") or "product_hunt_api_or_redirect_unresolved"
                    enriched.append(event.model_copy(update={"metadata": meta}))
                    continue
                discovered_domain = discovered.domain
                discovered_website = discovered.website
                meta["website_discovery_evidence"] = discovered.evidence

            # Normalize for contact recovery path below
            class _D:
                website = discovered_website
                domain = discovered_domain
                source = "product_hunt_api_or_erowd"
                confidence = 96.0
                verified_at = None
                evidence = ["ice_ph_or_erowd"]

            discovered = _D()

            meta["official_website"] = discovered.website
            meta["product_website"] = discovered.website
            meta["homepage"] = discovered.website
            meta["official_domain"] = discovered.domain
            meta["domain"] = discovered.domain
            meta["website_attribution"] = {
                "website": discovered.website,
                "source": discovered.source,
                "confidence": discovered.confidence,
                "collector": "product_hunt",
                "verified_at": discovered.verified_at.isoformat() if discovered.verified_at else None,
            }
            meta["website_discovery_evidence"] = discovered.evidence

            # Recover About / Contact / Team evidence from the official site only
            contacts = recover_from_official_website(str(discovered.website))
            if contacts.get("about_excerpt"):
                meta["about"] = contacts["about_excerpt"]
                meta["description"] = contacts["about_excerpt"]
            if contacts.get("emails"):
                meta["business_email"] = contacts["emails"][0]
                meta["emails"] = contacts["emails"]
                meta["email_verified_source"] = "company_website"
            if contacts.get("phones"):
                meta["phone"] = contacts["phones"][0]
                meta["phones"] = contacts["phones"]
                meta["phone_verified_source"] = "company_website"
            if contacts.get("linkedin"):
                company_li = next((u for u in contacts["linkedin"] if "/company/" in u), None)
                person_li = next((u for u in contacts["linkedin"] if "/in/" in u), None)
                if company_li:
                    meta["linkedin_company"] = company_li
                if person_li:
                    meta["linkedin"] = person_li
            if contacts.get("decision_makers"):
                meta["decision_makers"] = contacts["decision_makers"]
                top = contacts["decision_makers"][0]
                meta["decision_maker"] = f"{top['name']} ({top['role']})"
            meta["contact_pages"] = contacts.get("pages_fetched") or []
            meta["buying_signals"] = list(dict.fromkeys([*(meta.get("buying_signals") or []), "Product Hunt launch"]))
            meta["ofc_product_hunt_recovered"] = True

            enriched.append(event.model_copy(update={"metadata": meta}))
        return enriched
