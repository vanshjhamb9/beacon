"""Company trace engine — tracks company discovery and validation history.

Answer: Why did Beacon discover this company?
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class CompanyTrace:
    """Tracks company discovery history and validation state."""

    def __init__(self):
        self._traces: dict[str, dict[str, Any]] = {}

    def record_company(
        self,
        company_id: str,
        company_name: str,
        website: str,
        industry: str,
        country: str,
        discovery_source: str,
        discovery_connector: str,
        discovery_timestamp: datetime,
        first_evidence_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record company discovery."""
        trace = {
            "trace_id": str(uuid4()),
            "company_id": company_id,
            "company_name": company_name,
            "website": website,
            "industry": industry,
            "country": country,
            "discovery_source": discovery_source,
            "discovery_connector": discovery_connector,
            "discovery_timestamp": discovery_timestamp.isoformat() if isinstance(discovery_timestamp, datetime) else str(discovery_timestamp),
            "first_evidence_url": first_evidence_url,
            "validation_history": [],
            "current_state": "discovered",
            "metadata": metadata or {},
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

        self._traces[company_id] = trace
        return trace

    def add_validation_event(
        self,
        company_id: str,
        event_type: str,
        decision: str,
        reasons: list[str],
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        """Add validation event to company history."""
        if company_id not in self._traces:
            return {"error": "Company not found"}

        trace = self._traces[company_id]
        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "decision": decision,
            "reasons": reasons,
            "evidence": evidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        trace["validation_history"].append(event)
        trace["current_state"] = decision

        return event

    def get_company_trace(self, company_id: str) -> dict[str, Any] | None:
        """Get full company trace."""
        return self._traces.get(company_id)

    def get_companies_by_state(self, state: str) -> list[dict[str, Any]]:
        """Get all companies in a specific state."""
        return [
            trace for trace in self._traces.values()
            if trace.get("current_state") == state
        ]

    def get_companies_by_connector(self, connector: str) -> list[dict[str, Any]]:
        """Get all companies discovered by a specific connector."""
        return [
            trace for trace in self._traces.values()
            if trace.get("discovery_connector") == connector
        ]

    def get_statistics(self) -> dict[str, Any]:
        """Get company trace statistics."""
        total = len(self._traces)
        states = {}
        connectors = {}
        industries = {}

        for trace in self._traces.values():
            state = trace.get("current_state", "unknown")
            connector = trace.get("discovery_connector", "unknown")
            industry = trace.get("industry", "unknown")
            states[state] = states.get(state, 0) + 1
            connectors[connector] = connectors.get(connector, 0) + 1
            industries[industry] = industries.get(industry, 0) + 1

        return {
            "total_companies": total,
            "by_state": states,
            "by_connector": connectors,
            "by_industry": industries,
        }

    def clear(self):
        """Clear all traces (for testing)."""
        self._traces.clear()
