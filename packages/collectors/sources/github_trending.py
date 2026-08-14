from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import httpx

from collectors.base import BaseCollector
from collectors.events import NormalizedEvent
from collectors.extraction.quality import enrichment_metadata, strip_html
from intelligence.entity_resolution.platform_domains import is_platform_domain

REJECT_NAME_FRAGMENTS = (
    "awesome-",
    "awesome_",
    "/awesome",
    "template",
    "boilerplate",
    "starter-kit",
    "starterkit",
    "dotfiles",
    "curriculum",
    "cheat-sheet",
    "cheatsheet",
    "examples",
    "sample-",
    "hello-world",
    "learn-",
    "tutorial",
)


def _official_homepage(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if not raw.startswith("http"):
        raw = f"https://{raw}"
    try:
        host = urlparse(raw).netloc.lower().removeprefix("www.")
    except ValueError:
        return None
    if not host or is_platform_domain(host) or "github.com" in host:
        return None
    # Reject GitHub Pages as company identity unless clearly a product domain (still github.io = no)
    if host.endswith("github.io"):
        return None
    return raw


def _is_reject_repo(item: dict[str, Any]) -> str | None:
    if item.get("fork"):
        return "fork"
    if item.get("archived"):
        return "archived"
    name = str(item.get("full_name") or "").lower()
    desc = str(item.get("description") or "").lower()
    for frag in REJECT_NAME_FRAGMENTS:
        if frag in name or frag in desc:
            return f"library_or_template:{frag}"
    # Personal dump heuristic: no homepage + very generic name
    if not item.get("homepage") and any(x in name for x in ("/notes", "/config", "/scripts")):
        return "personal_repo"
    return None


class GitHubTrendingCollector(BaseCollector):
    """Company-shaped repos only — homepage required; never github.com as identity."""

    source = "github_trending"

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        max_items: int,
        topics: list[str] | None = None,
    ) -> None:
        super().__init__(http_client, max_items=max_items)
        self.topics = topics or ["saas", "startup", "artificial-intelligence", "automation"]

    async def collect(self) -> Sequence[NormalizedEvent]:
        since = (datetime.now(UTC) - timedelta(days=7)).date().isoformat()
        events: list[NormalizedEvent] = []
        per_topic = max(1, self.max_items // max(1, len(self.topics)))

        for topic in self.topics:
            query = f"{topic} created:>{since}"
            response = await self.http_client.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": min(per_topic, 30),
                },
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "BeaconAI/0.1 (+https://beacon.ai; public-search-collector)",
                },
            )
            response.raise_for_status()
            payload = response.json()
            events.extend(self._events_from_payload(payload, topic=topic))

        deduped: dict[str, NormalizedEvent] = {event.url: event for event in events}
        ranked = sorted(
            deduped.values(),
            key=lambda item: int(item.metadata.get("stars") or 0),
            reverse=True,
        )
        return ranked[: self.max_items]

    def _events_from_payload(self, payload: dict[str, Any], *, topic: str) -> list[NormalizedEvent]:
        events: list[NormalizedEvent] = []
        for item in payload.get("items", []):
            reject = _is_reject_repo(item)
            if reject:
                continue
            name = str(item.get("full_name") or "").strip()
            html_url = str(item.get("html_url") or "").strip()
            if not name or not html_url:
                continue
            repo_homepage = _official_homepage(item.get("homepage"))
            if not repo_homepage:
                # OFC: no company website → not a company candidate
                continue

            description = strip_html(str(item.get("description") or name))
            title = f"GitHub: {name}"
            created_at = str(item.get("created_at") or "")
            try:
                published_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                published_at = datetime.now(UTC)

            owner = item.get("owner") or {}
            host = urlparse(repo_homepage).netloc.lower().removeprefix("www.")
            extra: dict[str, Any] = {
                "topic": topic,
                "stars": item.get("stargazers_count"),
                "language": item.get("language"),
                "owner": owner.get("login"),
                "owner_type": owner.get("type"),
                "company_hints": [name.split("/")[0], name.split("/")[-1]],
                "repo_homepage": repo_homepage,
                "homepage": repo_homepage,
                "github_homepage": repo_homepage,
                "official_website": repo_homepage,
                "official_domain": host,
                "domain": host,
                "website_attribution": {
                    "website": repo_homepage,
                    "source": "github_repository_homepage",
                    "confidence": 95,
                    "collector": "github_trending",
                },
                "buying_signals": ["Open source product", "Engineering activity"],
            }

            metadata = enrichment_metadata(
                title=title,
                content=description,
                url=html_url,
                extra=extra,
            )
            if str(metadata.get("domain") or "").endswith("github.com"):
                metadata["domain"] = host

            events.append(
                NormalizedEvent(
                    source=self.source,
                    url=html_url,
                    title=title,
                    content=description,
                    published_at=published_at.astimezone(UTC),
                    metadata=metadata,
                )
            )
        return events
