"""Connector trace engine — tracks connector performance and signal quality.

Answer: Which connector found this company?
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class ConnectorTrace:
    """Tracks connector performance and signal quality."""

    def __init__(self):
        self._traces: dict[str, list[dict[str, Any]]] = {}
        self._connector_stats: dict[str, dict[str, Any]] = {}

    def record_connector_event(
        self,
        connector_name: str,
        opportunity_id: str,
        company_name: str,
        signal_type: str,
        signal_quality: str,
        validation_decision: str,
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        """Record connector event."""
        trace = {
            "trace_id": str(uuid4()),
            "connector_name": connector_name,
            "opportunity_id": opportunity_id,
            "company_name": company_name,
            "signal_type": signal_type,
            "signal_quality": signal_quality,
            "validation_decision": validation_decision,
            "evidence": evidence,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

        if connector_name not in self._traces:
            self._traces[connector_name] = []
        self._traces[connector_name].append(trace)

        # Update connector stats
        if connector_name not in self._connector_stats:
            self._connector_stats[connector_name] = {
                "total_signals": 0,
                "accepted": 0,
                "rejected": 0,
                "signal_types": {},
            }

        stats = self._connector_stats[connector_name]
        stats["total_signals"] += 1
        if validation_decision == "approve":
            stats["accepted"] += 1
        else:
            stats["rejected"] += 1

        signal_type_count = stats["signal_types"].get(signal_type, 0)
        stats["signal_types"][signal_type] = signal_type_count + 1

        return trace

    def get_connector_traces(self, connector_name: str) -> list[dict[str, Any]]:
        """Get all traces for a connector."""
        return self._traces.get(connector_name, [])

    def get_connector_stats(self, connector_name: str) -> dict[str, Any]:
        """Get statistics for a connector."""
        return self._connector_stats.get(connector_name, {})

    def get_all_connector_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all connectors."""
        return dict(self._connector_stats)

    def get_best_connector(self) -> str | None:
        """Get connector with highest acceptance rate."""
        best_connector = None
        best_rate = -1

        for connector, stats in self._connector_stats.items():
            total = stats["total_signals"]
            if total == 0:
                continue
            accepted = stats["accepted"]
            rate = accepted / total
            if rate > best_rate:
                best_rate = rate
                best_connector = connector

        return best_connector

    def get_worst_connector(self) -> str | None:
        """Get connector with lowest acceptance rate."""
        worst_connector = None
        worst_rate = 2.0

        for connector, stats in self._connector_stats.items():
            total = stats["total_signals"]
            if total == 0:
                continue
            accepted = stats["accepted"]
            rate = accepted / total
            if rate < worst_rate:
                worst_rate = rate
                worst_connector = connector

        return worst_connector

    def get_statistics(self) -> dict[str, Any]:
        """Get overall connector statistics."""
        total_traces = sum(len(traces) for traces in self._traces.values())
        total_connectors = len(self._traces)

        connector_rates = {}
        for connector, stats in self._connector_stats.items():
            total = stats["total_signals"]
            if total > 0:
                rate = stats["accepted"] / total
                connector_rates[connector] = {
                    "total": total,
                    "accepted": stats["accepted"],
                    "rejected": stats["rejected"],
                    "acceptance_rate": round(rate, 3),
                }

        return {
            "total_traces": total_traces,
            "total_connectors": total_connectors,
            "connector_rates": connector_rates,
            "best_connector": self.get_best_connector(),
            "worst_connector": self.get_worst_connector(),
        }

    def clear(self):
        """Clear all traces (for testing)."""
        self._traces.clear()
        self._connector_stats.clear()
