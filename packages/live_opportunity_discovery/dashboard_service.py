"""Dashboard aggregation for live opportunity discovery."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from live_opportunity_discovery.priority_ranker import PriorityRanker


FILTER_WINDOWS: dict[str, int] = {
    "today": 0,
    "yesterday": 1,
    "3_days": 3,
    "7_days": 7,
    "14_days": 14,
    "21_days": 21,
}


class DashboardService:
    def __init__(self, ranker: PriorityRanker | None = None) -> None:
        self.ranker = ranker or PriorityRanker()

    def build(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        ranked = self.ranker.rank(rows)
        return {
            "columns": [
                "Company",
                "Buying Event",
                "Freshness",
                "Buying Score",
                "Evidence",
                "Priority",
                "Service Match",
                "Revenue",
                "Decision Maker",
                "Status",
            ],
            "items": ranked,
            "filters": {
                "windows": list(FILTER_WINDOWS),
                "categories": [
                    "Hiring",
                    "Funding",
                    "Expansion",
                    "Technology",
                    "Executive",
                    "Operations",
                    "Marketing",
                ],
            },
            "category_counts": dict(Counter(str(row.get("category") or "Unknown") for row in rows)),
            "priority_counts": dict(Counter(str(row.get("priority") or "P3") for row in rows)),
            "trending": self.trending(rows),
        }

    def timeline(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(
            [
                {
                    "date": str(row.get("event_timestamp") or "")[:10],
                    "event": row.get("event_type"),
                    "category": row.get("category"),
                    "score": row.get("buying_score") or row.get("priority_score"),
                }
                for row in rows
            ],
            key=lambda item: item["date"],
        )

    def trending(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        buckets: defaultdict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "max_score": 0.0})
        for row in rows:
            category = str(row.get("category") or "Unknown")
            buckets[category]["count"] += 1
            buckets[category]["max_score"] = max(
                buckets[category]["max_score"],
                float(row.get("buying_score") or row.get("priority_score") or 0),
            )
        return sorted(
            [{"category": category, **payload} for category, payload in buckets.items()],
            key=lambda item: (item["count"], item["max_score"]),
            reverse=True,
        )
