"""DSIP: Freshness Engine.

Tracks freshness for every company.
Automatically schedules re-enrichment for stale companies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FreshnessData:
    """Freshness tracking data for a company."""
    company_id: str
    last_seen: datetime = field(default_factory=datetime.utcnow)
    last_crawl: datetime | None = None
    last_validated: datetime | None = None

    # Change Tracking
    last_name_change: datetime | None = None
    last_tech_change: datetime | None = None
    last_contact_change: datetime | None = None
    last_traffic_change: datetime | None = None
    last_price_change: datetime | None = None
    last_review_change: datetime | None = None

    # Schedule
    next_scheduled_crawl: datetime | None = None
    crawl_frequency_hours: int = 168  # 7 days
    priority_refresh: bool = False

    # Score
    freshness_score: float = 100.0  # 100=fresh, 0=stale
    days_since_last_seen: int = 0
    staleness_reason: str = ""


class FreshnessEngine:
    """Tracks freshness for every company and schedules re-crawls.

    Freshness is calculated based on:
    - Days since last seen
    - Data change frequency
    - Source reliability
    - Company importance

    Usage:
        engine = FreshnessEngine()
        freshness = engine.get_freshness(company_id)
        stale = engine.get_stale_companies()
        engine.update_freshness(company_id, changes={"tech": True})
    """

    def __init__(self):
        self._freshness: dict[str, FreshnessData] = {}

    def register_company(
        self,
        company_id: str,
        crawl_frequency_hours: int = 168,
    ) -> FreshnessData:
        """Register a company for freshness tracking."""
        freshness = FreshnessData(
            company_id=company_id,
            crawl_frequency_hours=crawl_frequency_hours,
            next_scheduled_crawl=datetime.utcnow() + timedelta(hours=crawl_frequency_hours),
        )
        self._freshness[company_id] = freshness
        return freshness

    def get_freshness(self, company_id: str) -> FreshnessData | None:
        """Get freshness data for a company."""
        return self._freshness.get(company_id)

    def update_freshness(
        self,
        company_id: str,
        changes: dict[str, bool] = None,
        crawl_frequency_hours: int = None,
    ) -> FreshnessData:
        """Update freshness after a crawl."""
        freshness = self._freshness.get(company_id)
        if not freshness:
            freshness = self.register_company(company_id)

        now = datetime.utcnow()
        freshness.last_seen = now
        freshness.last_crawl = now

        # Update change timestamps
        if changes:
            for change_type, occurred in changes.items():
                if occurred:
                    attr_name = f"last_{change_type}_change"
                    if hasattr(freshness, attr_name):
                        setattr(freshness, attr_name, now)

        # Update crawl frequency if provided
        if crawl_frequency_hours is not None:
            freshness.crawl_frequency_hours = crawl_frequency_hours

        # Schedule next crawl
        freshness.next_scheduled_crawl = now + timedelta(
            hours=freshness.crawl_frequency_hours
        )

        # Recalculate freshness score
        freshness.freshness_score = self._calculate_freshness_score(freshness)
        freshness.days_since_last_seen = 0

        return freshness

    def get_stale_companies(
        self,
        threshold_score: float = 50.0,
        limit: int = 100,
    ) -> list[FreshnessData]:
        """Get companies that need re-crawling."""
        stale = []
        now = datetime.utcnow()

        for freshness in self._freshness.values():
            # Check if overdue
            if freshness.next_scheduled_crawl and freshness.next_scheduled_crawl < now:
                stale.append(freshness)
                continue

            # Check freshness score
            if freshness.freshness_score < threshold_score:
                stale.append(freshness)

        # Sort by freshness score (stalest first)
        stale.sort(key=lambda f: f.freshness_score)

        return stale[:limit]

    def get_companies_due_for_crawl(self, limit: int = 50) -> list[str]:
        """Get company IDs due for scheduled crawl."""
        now = datetime.utcnow()
        due = []

        for company_id, freshness in self._freshness.items():
            if freshness.next_scheduled_crawl and freshness.next_scheduled_crawl <= now:
                due.append(company_id)

        return due[:limit]

    def calculate_days_since_seen(self, company_id: str) -> int:
        """Calculate days since company was last seen."""
        freshness = self._freshness.get(company_id)
        if not freshness or not freshness.last_seen:
            return 999  # Never seen

        delta = datetime.utcnow() - freshness.last_seen
        return delta.days

    def _calculate_freshness_score(self, freshness: FreshnessData) -> float:
        """Calculate freshness score (0-100)."""
        if not freshness.last_seen:
            return 0.0

        days_since = (datetime.utcnow() - freshness.last_seen).total_seconds() / 86400

        # Score decreases over time
        if days_since < 1:
            return 100.0
        elif days_since < 7:
            return 90.0
        elif days_since < 14:
            return 80.0
        elif days_since < 30:
            return 60.0
        elif days_since < 60:
            return 40.0
        elif days_since < 90:
            return 20.0
        else:
            return 10.0

    def get_freshness_stats(self) -> dict:
        """Get overall freshness statistics."""
        total = len(self._freshness)
        if total == 0:
            return {"total": 0, "fresh": 0, "stale": 0, "unknown": 0}

        fresh = sum(1 for f in self._freshness.values() if f.freshness_score >= 70)
        stale = sum(1 for f in self._freshness.values() if f.freshness_score < 50)
        unknown = sum(1 for f in self._freshness.values() if not f.last_seen)

        avg_score = sum(f.freshness_score for f in self._freshness.values()) / total

        return {
            "total": total,
            "fresh": fresh,
            "stale": stale,
            "unknown": unknown,
            "avg_freshness_score": avg_score,
            "due_for_crawl": len(self.get_companies_due_for_crawl()),
        }
