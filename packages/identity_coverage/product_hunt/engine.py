"""Product Hunt API resolver — GraphQL when token present; never scrape Cloudflare HTML."""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from identity_coverage.models.types import CoverageEvidence, UNKNOWN
from intelligence.entity_resolution.platform_domains import is_platform_domain

PH_GRAPHQL = "https://api.producthunt.com/v2/api/graphql"

POST_QUERY = """
query PostById($id: ID!) {
  post(id: $id) {
    id
    name
    tagline
    description
    url
    website
    createdAt
    topics { edges { node { name } } }
    user { name username twitterUsername }
    makers { name username twitterUsername }
  }
}
"""


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
    if not host or is_platform_domain(host) or "producthunt.com" in host:
        return None
    return host


class ProductHuntApiResolver:
    name = "product_hunt_api"
    priority = 10

    def __init__(self, *, token: str | None = None, client: httpx.Client | None = None) -> None:
        self.token = (
            token
            or os.getenv("PRODUCT_HUNT_DEVELOPER_TOKEN")
            or os.getenv("PRODUCT_HUNT_TOKEN")
            or os.getenv("PRODUCTHUNT_TOKEN")
            or ""
        ).strip()
        self._client = client

    def extract_post_id(self, payload: dict[str, Any]) -> str | None:
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if meta.get("ph_post_id"):
            return str(meta["ph_post_id"])
        blob = " ".join(
            str(x or "")
            for x in (
                payload.get("url"),
                payload.get("body"),
                payload.get("content"),
                meta.get("ph_redirect_url"),
                meta.get("raw_content"),
            )
        )
        m = re.search(r"producthunt\.com/r/p/(\d+)", blob, re.I)
        if m:
            return m.group(1)
        m = re.search(r"Post/(\d+)", blob)
        if m:
            return m.group(1)
        return None

    def fetch_post(self, post_id: str) -> dict[str, Any] | None:
        if not self.token:
            return None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "BeaconICE/1.0 (+https://beacon.ai)",
        }
        try:
            if self._client:
                resp = self._client.post(
                    PH_GRAPHQL,
                    headers=headers,
                    json={"query": POST_QUERY, "variables": {"id": str(post_id)}},
                )
            else:
                with httpx.Client(timeout=12.0) as client:
                    resp = client.post(
                        PH_GRAPHQL,
                        headers=headers,
                        json={"query": POST_QUERY, "variables": {"id": str(post_id)}},
                    )
            if resp.status_code >= 400:
                return None
            data = resp.json()
            return (data.get("data") or {}).get("post")
        except Exception:  # noqa: BLE001
            return None

    def collect(self, payload: dict[str, Any]) -> list[CoverageEvidence]:
        if str(payload.get("source") or "").lower() != "product_hunt":
            return []
        out: list[CoverageEvidence] = []
        post_id = self.extract_post_id(payload)
        post = self.fetch_post(post_id) if post_id else None

        if post:
            website = post.get("website")
            host = _host(website)
            if host:
                out.append(
                    CoverageEvidence(
                        field="website",
                        value=f"https://{host}",
                        confidence=96.0,
                        collector="product_hunt",
                        timestamp=_now(),
                        verification=True,
                        source=self.name,
                        priority=self.priority,
                        reason="product_hunt_graphql_website",
                        evidence=[f"post_id:{post_id}", f"domain:{host}"],
                    )
                )
                out.append(
                    CoverageEvidence(
                        field="official_domain",
                        value=host,
                        confidence=96.0,
                        collector="product_hunt",
                        timestamp=_now(),
                        verification=True,
                        source=self.name,
                        priority=self.priority,
                        reason="product_hunt_graphql_website",
                        evidence=[f"post_id:{post_id}"],
                    )
                )
            for field, key in (("description", "description"), ("tagline", "tagline"), ("name", "name")):
                if post.get(key):
                    out.append(
                        CoverageEvidence(
                            field=field if field != "name" else "trade_name",
                            value=str(post[key])[:2000],
                            confidence=90.0,
                            collector="product_hunt",
                            timestamp=_now(),
                            verification=True,
                            source=self.name,
                            priority=self.priority,
                            reason=f"ph_api:{key}",
                            evidence=[f"post_id:{post_id}"],
                        )
                    )
            makers = post.get("makers") or []
            if isinstance(makers, list):
                for maker in makers[:5]:
                    if isinstance(maker, dict) and maker.get("name"):
                        out.append(
                            CoverageEvidence(
                                field="maker",
                                value=str(maker["name"]),
                                confidence=80.0,
                                collector="product_hunt",
                                timestamp=_now(),
                                verification=True,
                                source=self.name,
                                priority=20,
                                reason="ph_api_maker",
                                evidence=[f"post_id:{post_id}"],
                            )
                        )
            if post.get("url"):
                out.append(
                    CoverageEvidence(
                        field="launch_url",
                        value=str(post["url"]),
                        confidence=95.0,
                        collector="product_hunt",
                        timestamp=_now(),
                        verification=True,
                        source=self.name,
                        priority=30,
                        reason="ph_api_launch_url",
                        evidence=[f"post_id:{post_id}"],
                    )
                )
            return out

        # Token missing or API miss — emit structured blocker evidence only (never invent website)
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if post_id:
            out.append(
                CoverageEvidence(
                    field="ph_post_id",
                    value=str(post_id),
                    confidence=70.0,
                    collector="product_hunt",
                    timestamp=_now(),
                    verification=True,
                    source=self.name,
                    priority=40,
                    reason="atom_post_id_without_api_token" if not self.token else "ph_api_miss",
                    evidence=["signal_only_until_website"],
                )
            )
        if meta.get("ph_maker"):
            out.append(
                CoverageEvidence(
                    field="maker",
                    value=str(meta["ph_maker"]),
                    confidence=60.0,
                    collector="product_hunt",
                    timestamp=_now(),
                    verification=True,
                    source="product_hunt_atom",
                    priority=45,
                    reason="atom_author_maker",
                    evidence=["atom_feed"],
                )
            )
        if not self.token:
            out.append(
                CoverageEvidence(
                    field="blocker",
                    value="PRODUCT_HUNT_DEVELOPER_TOKEN missing",
                    confidence=100.0,
                    collector="product_hunt",
                    timestamp=_now(),
                    verification=True,
                    source=self.name,
                    priority=5,
                    reason="api_token_required",
                    evidence=["cloudflare_html_blocked"],
                )
            )
        return out
