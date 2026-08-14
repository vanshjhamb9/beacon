"""Validation metrics — collects and aggregates validation statistics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class ValidationMetrics:
    """Collects and aggregates validation statistics."""

    def __init__(self):
        self._metrics: dict[str, Any] = {
            "total_validated": 0,
            "accepted": 0,
            "rejected": 0,
            "archived": 0,
            "spam": 0,
            "competitor": 0,
            "duplicate": 0,
            "future_opportunity": 0,
            "watchlist": 0,
            "by_connector": {},
            "by_signal_type": {},
            "by_industry": {},
            "by_region": {},
            "by_grade": {},
            "rejection_reasons": {},
            "average_quality_score": 0.0,
            "average_signal_age": 0.0,
            "average_confidence": 0.0,
        }
        self._history: list[dict[str, Any]] = []

    def record_validation(
        self,
        opportunity_id: str,
        decision: str,
        connector: str,
        signal_type: str,
        industry: str,
        region: str,
        quality_score: int,
        signal_age_days: int,
        confidence: float,
        rejection_reasons: list[str] | None = None,
    ) -> dict[str, Any]:
        """Record a validation event."""
        record = {
            "opportunity_id": opportunity_id,
            "decision": decision,
            "connector": connector,
            "signal_type": signal_type,
            "industry": industry,
            "region": region,
            "quality_score": quality_score,
            "signal_age_days": signal_age_days,
            "confidence": confidence,
            "rejection_reasons": rejection_reasons or [],
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

        self._history.append(record)

        # Update counters
        self._metrics["total_validated"] += 1

        if decision == "approve":
            self._metrics["accepted"] += 1
        elif decision == "reject":
            self._metrics["rejected"] += 1
        elif decision == "archive":
            self._metrics["archived"] += 1
        elif decision == "spam":
            self._metrics["spam"] += 1
        elif decision == "competitor":
            self._metrics["competitor"] += 1
        elif decision == "duplicate":
            self._metrics["duplicate"] += 1
        elif decision == "future_opportunity":
            self._metrics["future_opportunity"] += 1
        elif decision == "watchlist":
            self._metrics["watchlist"] += 1

        # Update by_connector
        connector_stats = self._metrics["by_connector"].get(connector, {"total": 0, "accepted": 0, "rejected": 0})
        connector_stats["total"] += 1
        if decision == "approve":
            connector_stats["accepted"] += 1
        elif decision == "reject":
            connector_stats["rejected"] += 1
        self._metrics["by_connector"][connector] = connector_stats

        # Update by_signal_type
        signal_stats = self._metrics["by_signal_type"].get(signal_type, {"total": 0, "accepted": 0})
        signal_stats["total"] += 1
        if decision == "approve":
            signal_stats["accepted"] += 1
        self._metrics["by_signal_type"][signal_type] = signal_stats

        # Update by_industry
        industry_stats = self._metrics["by_industry"].get(industry, {"total": 0, "accepted": 0})
        industry_stats["total"] += 1
        if decision == "approve":
            industry_stats["accepted"] += 1
        self._metrics["by_industry"][industry] = industry_stats

        # Update by_region
        region_stats = self._metrics["by_region"].get(region, {"total": 0, "accepted": 0})
        region_stats["total"] += 1
        if decision == "approve":
            region_stats["accepted"] += 1
        self._metrics["by_region"][region] = region_stats

        # Update rejection reasons
        for reason in (rejection_reasons or []):
            self._metrics["rejection_reasons"][reason] = self._metrics["rejection_reasons"].get(reason, 0) + 1

        # Update averages
        total = self._metrics["total_validated"]
        self._metrics["average_quality_score"] = (
            (self._metrics["average_quality_score"] * (total - 1) + quality_score) / total
        )
        self._metrics["average_signal_age"] = (
            (self._metrics["average_signal_age"] * (total - 1) + signal_age_days) / total
        )
        self._metrics["average_confidence"] = (
            (self._metrics["average_confidence"] * (total - 1) + confidence) / total
        )

        return record

    def get_metrics(self) -> dict[str, Any]:
        """Get aggregated metrics."""
        return dict(self._metrics)

    def get_acceptance_rate(self) -> float:
        """Get acceptance rate."""
        total = self._metrics["total_validated"]
        if total == 0:
            return 0.0
        return self._metrics["accepted"] / total

    def get_rejection_rate(self) -> float:
        """Get rejection rate."""
        total = self._metrics["total_validated"]
        if total == 0:
            return 0.0
        return self._metrics["rejected"] / total

    def get_top_connector(self) -> str | None:
        """Get connector with highest acceptance rate."""
        best = None
        best_rate = -1

        for connector, stats in self._metrics["by_connector"].items():
            total = stats["total"]
            if total == 0:
                continue
            rate = stats["accepted"] / total
            if rate > best_rate:
                best_rate = rate
                best = connector

        return best

    def get_worst_connector(self) -> str | None:
        """Get connector with lowest acceptance rate."""
        worst = None
        worst_rate = 2.0

        for connector, stats in self._metrics["by_connector"].items():
            total = stats["total"]
            if total == 0:
                continue
            rate = stats["accepted"] / total
            if rate < worst_rate:
                worst_rate = rate
                worst = connector

        return worst

    def get_history(self) -> list[dict[str, Any]]:
        """Get validation history."""
        return list(self._history)

    def clear(self):
        """Clear all metrics (for testing)."""
        self._metrics = {
            "total_validated": 0,
            "accepted": 0,
            "rejected": 0,
            "archived": 0,
            "spam": 0,
            "competitor": 0,
            "duplicate": 0,
            "future_opportunity": 0,
            "watchlist": 0,
            "by_connector": {},
            "by_signal_type": {},
            "by_industry": {},
            "by_region": {},
            "by_grade": {},
            "rejection_reasons": {},
            "average_quality_score": 0.0,
            "average_signal_age": 0.0,
            "average_confidence": 0.0,
        }
        self._history.clear()
