"""Validation dashboard — read-only metrics for opportunity quality.

Metrics:
    Collected Today
    Accepted
    Rejected
    Archived
    Spam
    Competitor
    Duplicate
    AI Companies
    Old Opportunities
    Average Signal Age
    Average Evidence Count
    Average Timeline Length
    Top Connectors
    Worst Connectors
    Top Rejection Reasons
    Most Valuable Signal Types
    Median Time To Revenue Ready
    Oldest Opportunity
    Newest Opportunity
    Companies Missing Timeline
    Companies Missing Evidence
    Companies Missing Website
    Companies Missing Decision Maker
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class ValidationDashboard:
    """Read-only dashboard for opportunity quality metrics."""

    def __init__(self):
        self._metrics: dict[str, Any] = {}
        self._opportunities: list[dict[str, Any]] = []

    def collect_metrics(
        self,
        opportunities: list[dict[str, Any]],
        validation_results: list[dict[str, Any]],
        timeline_stats: dict[str, Any],
        connector_stats: dict[str, Any],
    ) -> dict[str, Any]:
        """Collect all dashboard metrics."""
        self._opportunities = opportunities

        metrics = {
            "collected_today": self._count_collected_today(opportunities),
            "accepted": self._count_by_decision(validation_results, "approve"),
            "rejected": self._count_by_decision(validation_results, "reject"),
            "archived": self._count_by_decision(validation_results, "archive"),
            "spam": self._count_by_decision(validation_results, "spam"),
            "competitor": self._count_by_decision(validation_results, "competitor"),
            "duplicate": self._count_by_decision(validation_results, "duplicate"),
            "ai_companies": self._count_ai_companies(opportunities),
            "old_opportunities": self._count_old_opportunities(opportunities),
            "average_signal_age": self._calc_avg_signal_age(opportunities),
            "average_evidence_count": self._calc_avg_evidence_count(opportunities),
            "average_timeline_length": timeline_stats.get("avg_events_per_timeline", 0),
            "top_connectors": self._get_top_connectors(connector_stats),
            "worst_connectors": self._get_worst_connectors(connector_stats),
            "top_rejection_reasons": self._get_top_rejection_reasons(validation_results),
            "most_valuable_signal_types": self._get_most_valuable_signals(opportunities),
            "median_time_to_revenue_ready": self._calc_median_time_to_revenue_ready(opportunities),
            "oldest_opportunity": self._get_oldest_opportunity(opportunities),
            "newest_opportunity": self._get_newest_opportunity(opportunities),
            "companies_missing_timeline": self._count_missing_timeline(opportunities),
            "companies_missing_evidence": self._count_missing_evidence(opportunities),
            "companies_missing_website": self._count_missing_website(opportunities),
            "companies_missing_decision_maker": self._count_missing_decision_maker(opportunities),
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

        self._metrics = metrics
        return metrics

    def get_metrics(self) -> dict[str, Any]:
        """Get collected metrics."""
        return dict(self._metrics)

    def _count_collected_today(self, opportunities: list[dict[str, Any]]) -> int:
        """Count opportunities collected today."""
        today = datetime.now(timezone.utc).date()
        count = 0
        for opp in opportunities:
            collected = opp.get("collection_timestamp", "")
            if isinstance(collected, str) and collected.startswith(str(today)):
                count += 1
        return count

    def _count_by_decision(self, results: list[dict[str, Any]], decision: str) -> int:
        """Count validation results by decision."""
        return sum(1 for r in results if r.get("decision") == decision)

    def _count_ai_companies(self, opportunities: list[dict[str, Any]]) -> int:
        """Count AI companies."""
        ai_keywords = {"ai", "gpt", "llm", "openai", "anthropic", "claude"}
        count = 0
        for opp in opportunities:
            name = opp.get("company_name", "").lower()
            if any(kw in name for kw in ai_keywords):
                count += 1
        return count

    def _count_old_opportunities(self, opportunities: list[dict[str, Any]]) -> int:
        """Count opportunities older than 120 days."""
        count = 0
        for opp in opportunities:
            age = opp.get("signal_age_days", 0)
            if age > 120:
                count += 1
        return count

    def _calc_avg_signal_age(self, opportunities: list[dict[str, Any]]) -> float:
        """Calculate average signal age."""
        if not opportunities:
            return 0.0
        total_age = sum(opp.get("signal_age_days", 0) for opp in opportunities)
        return round(total_age / len(opportunities), 2)

    def _calc_avg_evidence_count(self, opportunities: list[dict[str, Any]]) -> float:
        """Calculate average evidence count."""
        if not opportunities:
            return 0.0
        total_evidence = sum(len(opp.get("evidence", {})) for opp in opportunities)
        return round(total_evidence / len(opportunities), 2)

    def _get_top_connectors(self, connector_stats: dict[str, Any]) -> list[dict[str, Any]]:
        """Get top connectors by acceptance rate."""
        rates = connector_stats.get("connector_rates", {})
        sorted_connectors = sorted(
            rates.items(),
            key=lambda x: x[1].get("acceptance_rate", 0),
            reverse=True,
        )
        return [
            {"connector": c, "stats": s}
            for c, s in sorted_connectors[:5]
        ]

    def _get_worst_connectors(self, connector_stats: dict[str, Any]) -> list[dict[str, Any]]:
        """Get worst connectors by acceptance rate."""
        rates = connector_stats.get("connector_rates", {})
        sorted_connectors = sorted(
            rates.items(),
            key=lambda x: x[1].get("acceptance_rate", 0),
        )
        return [
            {"connector": c, "stats": s}
            for c, s in sorted_connectors[:5]
        ]

    def _get_top_rejection_reasons(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Get top rejection reasons."""
        reasons: dict[str, int] = {}
        for r in results:
            if r.get("decision") == "reject":
                for reason in r.get("reasons", []):
                    reasons[reason] = reasons.get(reason, 0) + 1

        sorted_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)
        return [{"reason": r, "count": c} for r, c in sorted_reasons[:10]]

    def _get_most_valuable_signals(self, opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Get most valuable signal types."""
        signals: dict[str, int] = {}
        for opp in opportunities:
            signal = opp.get("buying_signal", "unknown")
            signals[signal] = signals.get(signal, 0) + 1

        sorted_signals = sorted(signals.items(), key=lambda x: x[1], reverse=True)
        return [{"signal": s, "count": c} for s, c in sorted_signals[:10]]

    def _calc_median_time_to_revenue_ready(self, opportunities: list[dict[str, Any]]) -> float:
        """Calculate median time to revenue ready (placeholder)."""
        return 0.0

    def _get_oldest_opportunity(self, opportunities: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Get oldest opportunity."""
        if not opportunities:
            return None
        return max(opportunities, key=lambda x: x.get("signal_age_days", 0))

    def _get_newest_opportunity(self, opportunities: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Get newest opportunity."""
        if not opportunities:
            return None
        return min(opportunities, key=lambda x: x.get("signal_age_days", 0))

    def _count_missing_timeline(self, opportunities: list[dict[str, Any]]) -> int:
        """Count companies missing timeline."""
        return sum(1 for opp in opportunities if not opp.get("timeline"))

    def _count_missing_evidence(self, opportunities: list[dict[str, Any]]) -> int:
        """Count companies missing evidence."""
        return sum(1 for opp in opportunities if not opp.get("evidence"))

    def _count_missing_website(self, opportunities: list[dict[str, Any]]) -> int:
        """Count companies missing website."""
        return sum(1 for opp in opportunities if not opp.get("website") or opp.get("website") == "unknown")

    def _count_missing_decision_maker(self, opportunities: list[dict[str, Any]]) -> int:
        """Count companies missing decision maker (placeholder)."""
        return 0
