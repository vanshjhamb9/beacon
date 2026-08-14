"""Connector ROI — tracks connector performance through entire pipeline.

Every connector displays:
    Signals → Accepted → Validated → Revenue Ready → Contacted → Replies
    → Meetings → Customers → Revenue

Calculate:
    Acceptance %
    Meeting %
    Revenue %
    Cost per Opportunity
    Revenue per Signal
    Revenue per Meeting

Automatically recommend: Keep, Investigate, Disable
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class ConnectorROI:
    """Tracks ROI metrics for a single connector."""

    def __init__(self, connector_name: str):
        self.connector_name = connector_name
        self.signals: int = 0
        self.accepted: int = 0
        self.validated: int = 0
        self.revenue_ready: int = 0
        self.contacted: int = 0
        self.replies: int = 0
        self.meetings: int = 0
        self.customers: int = 0
        self.revenue: float = 0.0
        self.cost: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector_name": self.connector_name,
            "signals": self.signals,
            "accepted": self.accepted,
            "validated": self.validated,
            "revenue_ready": self.revenue_ready,
            "contacted": self.contacted,
            "replies": self.replies,
            "meetings": self.meetings,
            "customers": self.customers,
            "revenue": self.revenue,
            "cost": self.cost,
            "acceptance_rate": self.get_acceptance_rate(),
            "meeting_rate": self.get_meeting_rate(),
            "revenue_rate": self.get_revenue_rate(),
            "cost_per_opportunity": self.get_cost_per_opportunity(),
            "revenue_per_signal": self.get_revenue_per_signal(),
            "revenue_per_meeting": self.get_revenue_per_meeting(),
            "recommendation": self.get_recommendation(),
        }

    def get_acceptance_rate(self) -> float:
        """Calculate acceptance rate."""
        if self.signals == 0:
            return 0.0
        return round(self.accepted / self.signals, 3)

    def get_meeting_rate(self) -> float:
        """Calculate meeting rate."""
        if self.contacted == 0:
            return 0.0
        return round(self.meetings / self.contacted, 3)

    def get_revenue_rate(self) -> float:
        """Calculate revenue rate (customers per meetings)."""
        if self.meetings == 0:
            return 0.0
        return round(self.customers / self.meetings, 3)

    def get_cost_per_opportunity(self) -> float:
        """Calculate cost per opportunity."""
        if self.revenue_ready == 0:
            return 0.0
        return round(self.cost / self.revenue_ready, 2)

    def get_revenue_per_signal(self) -> float:
        """Calculate revenue per signal."""
        if self.signals == 0:
            return 0.0
        return round(self.revenue / self.signals, 2)

    def get_revenue_per_meeting(self) -> float:
        """Calculate revenue per meeting."""
        if self.meetings == 0:
            return 0.0
        return round(self.revenue / self.meetings, 2)

    def get_recommendation(self) -> str:
        """Get automatic recommendation."""
        acceptance = self.get_acceptance_rate()
        meeting_rate = self.get_meeting_rate()
        revenue_rate = self.get_revenue_rate()

        # High performers
        if acceptance >= 0.3 and meeting_rate >= 0.2:
            return "Keep"

        # Need investigation
        if acceptance >= 0.1 or meeting_rate >= 0.1:
            return "Investigate"

        # Low performers
        return "Disable"


class ConnectorROITracker:
    """Tracks ROI for all connectors."""

    def __init__(self):
        self._connectors: dict[str, ConnectorROI] = {}

    def record_signal(self, connector: str):
        """Record a signal from connector."""
        if connector not in self._connectors:
            self._connectors[connector] = ConnectorROI(connector)
        self._connectors[connector].signals += 1

    def record_acceptance(self, connector: str):
        """Record an acceptance."""
        if connector not in self._connectors:
            self._connectors[connector] = ConnectorROI(connector)
        self._connectors[connector].accepted += 1

    def record_validation(self, connector: str):
        """Record a validation."""
        if connector not in self._connectors:
            self._connectors[connector] = ConnectorROI(connector)
        self._connectors[connector].validated += 1

    def record_revenue_ready(self, connector: str):
        """Record a revenue ready opportunity."""
        if connector not in self._connectors:
            self._connectors[connector] = ConnectorROI(connector)
        self._connectors[connector].revenue_ready += 1

    def record_contacted(self, connector: str):
        """Record a contacted opportunity."""
        if connector not in self._connectors:
            self._connectors[connector] = ConnectorROI(connector)
        self._connectors[connector].contacted += 1

    def record_reply(self, connector: str):
        """Record a reply."""
        if connector not in self._connectors:
            self._connectors[connector] = ConnectorROI(connector)
        self._connectors[connector].replies += 1

    def record_meeting(self, connector: str):
        """Record a meeting."""
        if connector not in self._connectors:
            self._connectors[connector] = ConnectorROI(connector)
        self._connectors[connector].meetings += 1

    def record_customer(self, connector: str, revenue: float = 0.0):
        """Record a customer."""
        if connector not in self._connectors:
            self._connectors[connector] = ConnectorROI(connector)
        self._connectors[connector].customers += 1
        self._connectors[connector].revenue += revenue

    def record_cost(self, connector: str, cost: float):
        """Record cost for connector."""
        if connector not in self._connectors:
            self._connectors[connector] = ConnectorROI(connector)
        self._connectors[connector].cost += cost

    def get_connector(self, connector: str) -> ConnectorROI | None:
        """Get connector ROI."""
        return self._connectors.get(connector)

    def get_all_connectors(self) -> list[ConnectorROI]:
        """Get all connector ROIs."""
        return list(self._connectors.values())

    def get_best_connector(self) -> ConnectorROI | None:
        """Get best performing connector by acceptance rate."""
        if not self._connectors:
            return None
        return max(self._connectors.values(), key=lambda c: c.get_acceptance_rate())

    def get_worst_connector(self) -> ConnectorROI | None:
        """Get worst performing connector by acceptance rate."""
        if not self._connectors:
            return None
        return min(self._connectors.values(), key=lambda c: c.get_acceptance_rate())

    def get_statistics(self) -> dict[str, Any]:
        """Get overall connector ROI statistics."""
        total_signals = sum(c.signals for c in self._connectors.values())
        total_revenue = sum(c.revenue for c in self._connectors.values())
        total_customers = sum(c.customers for c in self._connectors.values())
        total_meetings = sum(c.meetings for c in self._connectors.values())

        return {
            "total_connectors": len(self._connectors),
            "total_signals": total_signals,
            "total_revenue": total_revenue,
            "total_customers": total_customers,
            "total_meetings": total_meetings,
            "avg_acceptance_rate": round(
                sum(c.get_acceptance_rate() for c in self._connectors.values()) / max(len(self._connectors), 1),
                3,
            ),
        }
