"""Reddit Cybersecurity Collector — Finds buying signals from security subreddits."""

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

_PULLPUSH_URL = "https://api.pullpush.io/reddit/search/submission/"
_USER_AGENT = "Mozilla/5.0 (compatible; BeaconCyber/0.1; +https://beacon.ai; cybersecurity-research)"

# Subreddits where cybersecurity buying signals appear
CYBERSECURITY_SUBREDDITS = [
    # Direct security buying signals
    "netsec",
    "cybersecurity",
    "infosec",
    "security",
    "AskNetsec",
    "ciso",
    # Business contexts where security is discussed
    "SaaS",
    "startups",
    "Entrepreneur",
    "smallbusiness",
    "webdev",
    "devops",
    "cloudcomputing",
    # Compliance
    "SOC2compliance",
    # Regional
    "Dubai",
    "singapore",
    "london",
]

# Quick filter keywords for relevance (broadened for better matching)
RELEVANCE_KEYWORDS = [
    # Direct buying signals
    "penetration test", "pentest", "vapt", "vulnerability assessment",
    "security audit", "security test", "security assessment",
    "need security", "looking for security", "security vendor",
    "security company", "rfp security", "security procurement",
    # Compliance
    "soc 2", "soc2", "iso 27001", "compliance", "security testing",
    "hipaa", "gdpr", "pci dss", "security compliance",
    # Specific services
    "web app security", "api security", "mobile security",
    "cloud security", "network security", "ethical hacker",
    "red team", "blue team", "penetration testing company",
    # Incident response
    "remediation", "retesting", "bug bounty",
    "security incident", "data breach", "vulnerability found",
    "failed audit", "security review", "security assessment",
    # Buying intent phrases (broader matching)
    "hire.*security", "contract.*security", "security.*firm",
    "security.*consult", "security.*vendor", "security.*provider",
    "need.*pentest", "need.*vapt", "need.*audit",
    "looking.*pentester", "looking.*security.*company",
    "recommend.*security", "suggest.*security",
    # Pain signals
    "security gap", "security hole", "security weakness",
    "compliance deadline", "audit deadline", "security deadline",
    "failed compliance", "security concern", "security risk",
]

# Compiled patterns for fuzzy matching
_FUZZY_PATTERNS = [
    re.compile(r"hire.{0,20}security"),
    re.compile(r"need.{0,20}(?:pentest|vapt|security|audit)"),
    re.compile(r"looking.{0,20}(?:for|at|into).{0,20}security"),
    re.compile(r"recommend.{0,20}security"),
    re.compile(r"suggest.{0,20}security"),
    re.compile(r"contract.{0,20}security"),
    re.compile(r"security.{0,20}(?:firm|vendor|company|consult|provider)"),
]


class RedditCybersecurityCollector(BaseCybersecurityCollector):
    """Collects cybersecurity buying signals from Reddit."""

    source_name = "reddit"
    source_tier = 2

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        subreddits: list[str] | None = None,
        max_items: int = 50,
        lookback_days: int = 90,
    ) -> None:
        super().__init__(http_client)
        self.subreddits = subreddits or CYBERSECURITY_SUBREDDITS
        self.max_items = max_items
        self.lookback_days = lookback_days

    async def collect(self) -> Sequence[RawSignal]:
        """Collect cybersecurity signals from Reddit."""
        all_signals: list[RawSignal] = []
        per_sub_limit = max(5, self.max_items // len(self.subreddits))

        for subreddit in self.subreddits:
            try:
                signals = await self._collect_subreddit(subreddit, per_sub_limit)
                all_signals.extend(signals)
                # Delay between subreddits to avoid rate limiting
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning("Reddit collector failed for r/%s: %s", subreddit, e)
                continue

        # Sort by relevance score
        all_signals.sort(key=lambda s: s.score, reverse=True)
        logger.info("Reddit collector found %d signals total", len(all_signals))
        return all_signals[: self.max_items]

    async def _collect_subreddit(
        self, subreddit: str, limit: int
    ) -> list[RawSignal]:
        """Collect from a single subreddit with retry logic."""
        signals: list[RawSignal] = []
        max_retries = 2

        for attempt in range(max_retries):
            try:
                # Try PullPush API first
                signals = await self._fetch_pullpush(subreddit, limit)
                if signals:
                    return signals
            except httpx.HTTPStatusError as e:
                logger.debug(
                    "PullPush API returned %d for r/%s (attempt %d/%d)",
                    e.response.status_code, subreddit, attempt + 1, max_retries,
                )
            except httpx.RequestError as e:
                logger.debug(
                    "PullPush API request failed for r/%s: %s (attempt %d/%d)",
                    subreddit, e, attempt + 1, max_retries,
                )

            # Exponential backoff on retry
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0 * (2 ** attempt))

        # Fallback to Reddit JSON API (single attempt)
        try:
            signals = await self._fetch_reddit_json(subreddit, limit)
            return signals
        except Exception as e:
            logger.debug(
                "Reddit JSON API failed for r/%s: %s (no more retries)",
                subreddit, e,
            )
            return []

    async def _fetch_pullpush(
        self, subreddit: str, limit: int
    ) -> list[RawSignal]:
        """Fetch from PullPush archive API."""
        # Calculate cutoff date for time-based filtering
        cutoff = datetime.now(UTC) - timedelta(days=self.lookback_days)
        cutoff_ts = int(cutoff.timestamp())

        response = await self.http_client.get(
            _PULLPUSH_URL,
            params={
                "subreddit": subreddit,
                "size": min(limit * 3, 100),  # Fetch more to account for filtering
                "sort": "desc",
                "sort_type": "created_utc",
                "after": str(cutoff_ts),  # Time-based filtering
            },
            headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
            timeout=15.0,
        )
        if response.status_code == 403:
            logger.debug("PullPush API returned 403 for r/%s", subreddit)
            return []
        if response.status_code == 429:
            logger.warning("PullPush API rate limited for r/%s", subreddit)
            await asyncio.sleep(2.0)
            return []
        response.raise_for_status()
        payload = response.json()

        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            return []

        signals = []
        for item in data:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            selftext = str(item.get("selftext") or "").strip()
            full_text = f"{title} {selftext}"

            if not title or not self._is_relevant(full_text):
                continue

            permalink = str(item.get("permalink") or "").strip()
            url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else permalink

            created_utc = float(item.get("created_utc") or 0)
            published = datetime.fromtimestamp(created_utc, tz=UTC) if created_utc else None

            # Skip posts older than cutoff
            if published and published < cutoff:
                continue

            score = self._calculate_score(full_text, item.get("score", 0))

            signals.append(RawSignal(
                source="reddit",
                source_tier=self.source_tier,
                url=url,
                title=title,
                content=selftext[:1000] if selftext else title,
                author=str(item.get("author") or ""),
                published_at=published,
                score=score,
                metadata={
                    "subreddit": subreddit,
                    "reddit_id": item.get("id"),
                    "num_comments": item.get("num_comments"),
                    "upvotes": item.get("score"),
                },
            ))

        return signals[:limit]

    async def _fetch_reddit_json(
        self, subreddit: str, limit: int
    ) -> list[RawSignal]:
        """Fetch from Reddit JSON API."""
        response = await self.http_client.get(
            f"https://www.reddit.com/r/{subreddit}/new.json",
            params={"limit": min(limit * 2, 50), "raw_json": 1},
            headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
            timeout=15.0,
        )
        response.raise_for_status()
        payload = response.json()

        children = payload.get("data", {}).get("children", [])
        signals = []

        # Calculate cutoff date
        cutoff = datetime.now(UTC) - timedelta(days=self.lookback_days)

        for child in children:
            data = child.get("data", {})
            title = str(data.get("title") or "").strip()
            selftext = str(data.get("selftext") or "").strip()
            full_text = f"{title} {selftext}"

            if not title or not self._is_relevant(full_text):
                continue

            permalink = str(data.get("permalink") or "").strip()
            url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else permalink

            created_utc = float(data.get("created_utc") or 0)
            published = datetime.fromtimestamp(created_utc, tz=UTC) if created_utc else None

            # Skip posts older than cutoff
            if published and published < cutoff:
                continue

            score = self._calculate_score(full_text, data.get("score", 0))

            signals.append(RawSignal(
                source="reddit",
                source_tier=self.source_tier,
                url=url,
                title=title,
                content=selftext[:1000] if selftext else title,
                author=str(data.get("author") or ""),
                published_at=published,
                score=score,
                metadata={
                    "subreddit": subreddit,
                    "reddit_id": data.get("id"),
                    "num_comments": data.get("num_comments"),
                    "upvotes": data.get("score"),
                },
            ))

        return signals[:limit]

    def _calculate_score(self, text: str, reddit_score: int) -> int:
        """Calculate relevance score for a signal."""
        text_lower = text.lower()
        score = 0

        # High-value keywords (strong buying signals)
        high_value = [
            "need penetration test", "looking for pentest", "need vapt",
            "need security audit", "need security testing", "rfp security",
            "security procurement", "enterprise requires security",
            "customer requires security", "need vulnerability assessment",
            "hire security", "contract security", "security firm",
            "security vendor", "security company", "security provider",
        ]
        for kw in high_value:
            if kw in text_lower:
                score += 15

        # Medium-value keywords
        medium_value = [
            "penetration test", "pentest", "vapt", "security audit",
            "vulnerability", "compliance", "soc 2", "soc2", "iso 27001",
            "security testing", "security assessment", "hipaa", "gdpr",
            "pci dss", "security compliance", "red team", "blue team",
        ]
        for kw in medium_value:
            if kw in text_lower:
                score += 5

        # Fuzzy pattern matching for buying intent
        for pattern in _FUZZY_PATTERNS:
            if pattern.search(text_lower):
                score += 8

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

        # Reddit engagement boost
        if reddit_score and reddit_score > 10:
            score += 5
        elif reddit_score and reddit_score > 5:
            score += 3
        elif reddit_score and reddit_score > 0:
            score += 1

        return score
