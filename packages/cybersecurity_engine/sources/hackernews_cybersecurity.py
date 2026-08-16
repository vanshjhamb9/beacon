"""Hacker News Cybersecurity Collector — Finds buying signals from HN."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from cybersecurity_engine.sources import BaseCybersecurityCollector, RawSignal

logger = logging.getLogger(__name__)

_ALGOLIA_API = "https://hn.algolia.com/api/v1/search_by_date"

# Search queries for cybersecurity buying signals (broadened)
HN_SEARCH_QUERIES = [
    # Direct buying signals
    "penetration testing",
    "need security audit",
    "vulnerability assessment",
    "VAPT",
    "security testing company",
    "looking for pentester",
    "security compliance SOC2",
    "ISO 27001 certification",
    # Specific services
    "web application security",
    "API security testing",
    "mobile app security",
    "cloud security assessment",
    "network penetration test",
    # Procurement
    "security RFP",
    "security vendor",
    "security consultant",
    # Incident/pain
    "data breach",
    "security incident",
    "remediation security",
    # Broader buying intent
    "hire security",
    "contract security",
    "security firm",
    "security company",
    "recommend security",
    "security gap",
    "compliance deadline",
]

# Compiled patterns for buying intent
_BUYING_PATTERNS = [
    re.compile(r"hire.{0,20}security"),
    re.compile(r"need.{0,20}(?:pentest|vapt|security|audit)"),
    re.compile(r"looking.{0,20}(?:for|at|into).{0,20}security"),
    re.compile(r"recommend.{0,20}security"),
    re.compile(r"suggest.{0,20}security"),
    re.compile(r"contract.{0,20}security"),
    re.compile(r"security.{0,20}(?:firm|vendor|company|consult|provider)"),
]


class HackerNewsCybersecurityCollector(BaseCybersecurityCollector):
    """Collects cybersecurity buying signals from Hacker News."""

    source_name = "hacker_news"
    source_tier = 2

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        max_items: int = 50,
        lookback_days: int = 90,
    ) -> None:
        super().__init__(http_client)
        self.max_items = max_items
        self.lookback_days = lookback_days

    async def collect(self) -> Sequence[RawSignal]:
        """Collect cybersecurity signals from Hacker News."""
        all_signals: list[RawSignal] = []
        seen_ids: set[str] = set()

        # Calculate cutoff timestamp
        cutoff = datetime.now(UTC) - timedelta(days=self.lookback_days)
        cutoff_ts = int(cutoff.timestamp())

        for query in HN_SEARCH_QUERIES:
            try:
                signals = await self._search_query(query, cutoff_ts)
                for signal in signals:
                    signal_id = signal.metadata.get("hn_id", signal.url)
                    if signal_id not in seen_ids:
                        seen_ids.add(signal_id)
                        all_signals.append(signal)
                # Delay between queries to respect rate limits
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning("HN search failed for query '%s': %s", query, e)
                continue

        all_signals.sort(key=lambda s: s.score, reverse=True)
        logger.info("HN collector found %d signals total", len(all_signals))
        return all_signals[: self.max_items]

    async def _search_query(self, query: str, cutoff_ts: int) -> list[RawSignal]:
        """Search HN for a specific query."""
        response = await self.http_client.get(
            _ALGOLIA_API,
            params={
                "query": query,
                "tags": "story",
                "hitsPerPage": 20,
                "numericFilters": f"created_at_i>{cutoff_ts}",
            },
            headers={"Accept": "application/json"},
            timeout=15.0,
        )
        if response.status_code == 429:
            logger.warning("HN Algolia rate limited for query: %s", query)
            await asyncio.sleep(2.0)
            return []
        response.raise_for_status()
        data = response.json()

        hits = data.get("hits", [])
        signals = []

        for hit in hits:
            title = str(hit.get("title") or "").strip()
            story_text = str(hit.get("story_text") or hit.get("comment_text") or "").strip()
            full_text = f"{title} {story_text}"

            if not full_text.strip():
                continue

            hn_id = str(hit.get("objectID") or "")
            url = f"https://news.ycombinator.com/item?id={hn_id}" if hn_id else ""

            created_at = hit.get("created_at")
            published = None
            if created_at:
                try:
                    published = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass

            points = hit.get("points", 0)
            num_comments = hit.get("num_comments", 0)
            score = self._calculate_score(full_text, points, num_comments)

            signals.append(RawSignal(
                source="hacker_news",
                source_tier=self.source_tier,
                url=url,
                title=title or full_text[:100],
                content=story_text[:1000] if story_text else title,
                author=str(hit.get("author") or ""),
                author_url=f"https://news.ycombinator.com/user?id={hit.get('author', '')}" if hit.get("author") else "",
                published_at=published,
                score=score,
                metadata={
                    "hn_id": hn_id,
                    "points": points,
                    "num_comments": num_comments,
                    "query": query,
                },
            ))

        return signals

    def _calculate_score(self, text: str, points: int, num_comments: int) -> int:
        """Calculate relevance score."""
        text_lower = text.lower()
        score = 0

        # Direct buying signals (highest value)
        direct_keywords = [
            "need penetration test", "looking for pentest", "need vapt",
            "need security audit", "security testing company", "rfp security",
            "hire security", "contract security", "security firm",
            "security vendor", "security company", "security provider",
        ]
        for kw in direct_keywords:
            if kw in text_lower:
                score += 15

        # Fuzzy pattern matching for buying intent
        for pattern in _BUYING_PATTERNS:
            if pattern.search(text_lower):
                score += 10

        # Security topics (medium value)
        security_keywords = [
            "penetration test", "pentest", "vulnerability", "security audit",
            "compliance", "soc 2", "soc2", "iso 27001", "breach", "incident",
            "hipaa", "gdpr", "pci dss", "security testing", "security assessment",
        ]
        for kw in security_keywords:
            if kw in text_lower:
                score += 5

        # Pain signal keywords
        pain_keywords = [
            "security gap", "security hole", "security weakness",
            "compliance deadline", "audit deadline", "failed compliance",
            "security concern", "security risk", "data breach",
            "security incident", "vulnerability found",
        ]
        for kw in pain_keywords:
            if kw in text_lower:
                score += 3

        # HN engagement boost (time-weighted)
        if points and points > 50:
            score += 8
        elif points and points > 20:
            score += 5
        elif points and points > 5:
            score += 2

        if num_comments and num_comments > 20:
            score += 5
        elif num_comments and num_comments > 10:
            score += 3

        return score
