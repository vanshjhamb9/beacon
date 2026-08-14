"""Product Hunt official GraphQL client — posts feed + post lookup. No HTML scrape."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from intelligence.entity_resolution.platform_domains import is_platform_domain

PH_GRAPHQL = "https://api.producthunt.com/v2/api/graphql"
COLLECTOR_VERSION = "odu-ph-graphql-v1"

POST_BY_ID = """
query PostById($id: ID!) {
  post(id: $id) {
    id name tagline description url website createdAt
    topics { edges { node { name } } }
    user { name username }
    makers { name username twitterUsername }
  }
}
"""

POSTS_FEED = """
query PostsFeed($first: Int!) {
  posts(first: $first, order: RANKING) {
    edges {
      node {
        id name tagline description url website createdAt
        topics { edges { node { name } } }
        user { name username }
        makers { name username twitterUsername }
      }
    }
  }
}
"""


def _host(url: str | None) -> str | None:
    if not url:
        return None
    raw = url if "://" in url else f"https://{url}"
    try:
        host = urlparse(raw).netloc.lower().removeprefix("www.")
    except ValueError:
        return None
    if not host or is_platform_domain(host) or "producthunt.com" in host:
        return None
    return host


class ProductHuntGraphQLClient:
    """Official API only. Never treat producthunt.com as company identity."""

    def __init__(self, *, token: str | None = None, client: httpx.Client | None = None) -> None:
        self.token = (
            token
            or os.getenv("PRODUCT_HUNT_DEVELOPER_TOKEN")
            or os.getenv("PRODUCT_HUNT_TOKEN")
            or os.getenv("PRODUCTHUNT_TOKEN")
            or ""
        ).strip()
        self._client = client

    @property
    def has_token(self) -> bool:
        return bool(self.token)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "BeaconODU/1.0 (+https://beacon.ai)",
        }

    def _post(self, query: str, variables: dict[str, Any]) -> dict[str, Any] | None:
        if not self.token:
            return None
        try:
            if self._client:
                resp = self._client.post(
                    PH_GRAPHQL, headers=self._headers(), json={"query": query, "variables": variables}
                )
            else:
                with httpx.Client(timeout=20.0) as client:
                    resp = client.post(
                        PH_GRAPHQL, headers=self._headers(), json={"query": query, "variables": variables}
                    )
            if resp.status_code == 429:
                return {"__error": "rate_limited"}
            if resp.status_code >= 400:
                return {"__error": f"http_{resp.status_code}"}
            return resp.json()
        except Exception:  # noqa: BLE001
            return None

    def fetch_post(self, post_id: str) -> dict[str, Any] | None:
        data = self._post(POST_BY_ID, {"id": str(post_id)})
        if not data or data.get("__error"):
            return data
        return (data.get("data") or {}).get("post")

    def fetch_posts(self, *, first: int = 50) -> list[dict[str, Any]]:
        data = self._post(POSTS_FEED, {"first": min(first, 50)})
        if not data or data.get("__error"):
            return []
        edges = ((data.get("data") or {}).get("posts") or {}).get("edges") or []
        out = []
        for edge in edges:
            node = edge.get("node") if isinstance(edge, dict) else None
            if isinstance(node, dict):
                out.append(node)
        return out

    def normalize_post(self, post: dict[str, Any]) -> dict[str, Any] | None:
        host = _host(post.get("website"))
        if not host:
            return None  # signal-only — never invent
        now = datetime.now(UTC).isoformat()
        topics = []
        for edge in ((post.get("topics") or {}).get("edges") or []):
            name = ((edge or {}).get("node") or {}).get("name")
            if name:
                topics.append(str(name))
        makers = []
        for m in post.get("makers") or []:
            if isinstance(m, dict) and m.get("name"):
                makers.append(str(m["name"]))
        website = f"https://{host}"
        return {
            "source": "product_hunt",
            "title": str(post.get("name") or "Product Hunt launch"),
            "url": str(post.get("url") or website),
            "content": str(post.get("tagline") or post.get("description") or ""),
            "published_at": post.get("createdAt"),
            "metadata": {
                "ph_post_id": str(post.get("id") or ""),
                "official_website": website,
                "product_website": website,
                "homepage": website,
                "official_domain": host,
                "domain": host,
                "description": post.get("description") or post.get("tagline"),
                "tagline": post.get("tagline"),
                "categories": topics,
                "topics": topics,
                "makers": makers,
                "ph_maker": makers[0] if makers else None,
                "launch_date": post.get("createdAt"),
                "content_occurred_at": post.get("createdAt"),
                "source_kind": "event",
                "lead_eligible": True,
                "website_attribution": {
                    "website": website,
                    "source": "product_hunt_graphql",
                    "confidence": 96.0,
                    "collector": "product_hunt",
                    "collector_version": COLLECTOR_VERSION,
                    "verified_at": now,
                },
                "confidence": 96.0,
                "verified_at": now,
                "collector_version": COLLECTOR_VERSION,
                "buying_signals": [f"Product Hunt launch signal: {post.get('name')}"],
                "company_hints": [str(post.get("name"))] if post.get("name") else [],
            },
        }
