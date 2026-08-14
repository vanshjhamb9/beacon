"""Backend-only dashboard aggregation for Opportunity Intelligence."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any


class DashboardService:
    def build(self, opportunities: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "top_opportunities": sorted(
                opportunities,
                key=lambda row: (
                    float(row.get("opportunity_score") or 0),
                    float(row.get("confidence") or row.get("confidence_score") or 0),
                    float(row.get("freshness_score") or 0),
                ),
                reverse=True,
            )[:10],
            "buying_window_counts": self._counts(opportunities, "buying_window"),
            "signal_distribution": self._counts(opportunities, "signal_category"),
            "industry_distribution": self._counts(opportunities, "industry"),
            "country_distribution": self._counts(opportunities, "country"),
            "opportunity_timeline": self._timeline(opportunities),
            "freshness_distribution": self._freshness(opportunities),
            "evidence_distribution": self._evidence(opportunities),
        }

    def _counts(self, rows: list[dict[str, Any]], key: str) -> dict[str, int]:
        counter = Counter(str(row.get(key) or "Unknown") for row in rows)
        return dict(sorted(counter.items()))

    def _timeline(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        counter: defaultdict[str, int] = defaultdict(int)
        for row in rows:
            created = row.get("created_at") or row.get("signal_timestamp")
            if isinstance(created, datetime):
                bucket = created.date().isoformat()
            else:
                bucket = str(created or "Unknown")[:10]
            counter[bucket] += 1
        return dict(sorted(counter.items()))

    def _freshness(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        buckets = {
            "0-7 days": 0,
            "8-30 days": 0,
            "31-60 days": 0,
            "61-90 days": 0,
            "91-180 days": 0,
            "180+ days": 0,
        }
        for row in rows:
            age = int(row.get("signal_age_days") or 0)
            if age <= 7:
                buckets["0-7 days"] += 1
            elif age <= 30:
                buckets["8-30 days"] += 1
            elif age <= 60:
                buckets["31-60 days"] += 1
            elif age <= 90:
                buckets["61-90 days"] += 1
            elif age <= 180:
                buckets["91-180 days"] += 1
            else:
                buckets["180+ days"] += 1
        return buckets

    def _evidence(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        counter: defaultdict[str, int] = defaultdict(int)
        for row in rows:
            count = int(row.get("evidence_count") or len(row.get("evidence") or []))
            if count >= 5:
                counter["5+"] += 1
            else:
                counter[str(count)] += 1
        return dict(sorted(counter.items()))
