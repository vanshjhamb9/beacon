"""Signal trace engine — tracks origin and lifecycle of every signal.

Answer: What evidence created this opportunity?
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .v1_schemas import SignalOrigin


class SignalTrace:
    """Tracks every signal from origin to decision."""

    def __init__(self):
        self._traces: dict[str, list[dict[str, Any]]] = {}

    def record_signal(
        self,
        opportunity_id: str,
        signal_type: str,
        signal_source: str,
        connector: str,
        original_url: str,
        original_timestamp: datetime,
        collection_timestamp: datetime,
        evidence: dict[str, Any],
        origin: SignalOrigin = SignalOrigin.CONNECTOR,
    ) -> dict[str, Any]:
        """Record signal origin and metadata."""
        trace = {
            "trace_id": str(uuid4()),
            "opportunity_id": opportunity_id,
            "signal_type": signal_type,
            "signal_source": signal_source,
            "connector": connector,
            "original_url": original_url,
            "original_timestamp": original_timestamp.isoformat() if isinstance(original_timestamp, datetime) else str(original_timestamp),
            "collection_timestamp": collection_timestamp.isoformat() if isinstance(collection_timestamp, datetime) else str(collection_timestamp),
            "evidence": evidence,
            "origin": origin.value,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

        if opportunity_id not in self._traces:
            self._traces[opportunity_id] = []
        self._traces[opportunity_id].append(trace)

        return trace

    def get_trace(self, opportunity_id: str) -> list[dict[str, Any]]:
        """Get full signal trace for opportunity."""
        return self._traces.get(opportunity_id, [])

    def get_latest_trace(self, opportunity_id: str) -> dict[str, Any] | None:
        """Get most recent signal trace."""
        traces = self._traces.get(opportunity_id, [])
        return traces[-1] if traces else None

    def get_traces_by_connector(self, connector: str) -> list[dict[str, Any]]:
        """Get all traces from a specific connector."""
        results = []
        for opp_id, traces in self._traces.items():
            for trace in traces:
                if trace.get("connector") == connector:
                    results.append(trace)
        return results

    def get_traces_by_signal_type(self, signal_type: str) -> list[dict[str, Any]]:
        """Get all traces for a specific signal type."""
        results = []
        for opp_id, traces in self._traces.items():
            for trace in traces:
                if trace.get("signal_type") == signal_type:
                    results.append(trace)
        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get signal trace statistics."""
        total_traces = sum(len(traces) for traces in self._traces.values())
        connectors = {}
        signal_types = {}
        origins = {}

        for traces in self._traces.values():
            for trace in traces:
                connector = trace.get("connector", "unknown")
                signal_type = trace.get("signal_type", "unknown")
                origin = trace.get("origin", "unknown")
                connectors[connector] = connectors.get(connector, 0) + 1
                signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
                origins[origin] = origins.get(origin, 0) + 1

        return {
            "total_traces": total_traces,
            "unique_opportunities": len(self._traces),
            "by_connector": connectors,
            "by_signal_type": signal_types,
            "by_origin": origins,
        }

    def clear(self):
        """Clear all traces (for testing)."""
        self._traces.clear()
