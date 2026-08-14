"""Connector ROI engine — calculates ROI per connector from real outcomes."""

from __future__ import annotations

from typing import Any

from validation_engine.models import ConnectorRoi


class ConnectorRoiEngine:
    """Calculates ROI metrics per connector from real business outcomes."""

    def __init__(self) -> None:
        self._connector_data: dict[str, dict[str, Any]] = {}

    def record_signal(
        self,
        connector: str,
        *,
        companies: int = 0,
        revenue_ready: int = 0,
    ) -> None:
        data = self._connector_data.setdefault(connector, {
            "signals": 0, "companies": 0, "revenue_ready": 0,
            "replies": 0, "meetings": 0, "deals": 0, "revenue": 0.0,
        })
        data["signals"] += 1
        data["companies"] += companies
        data["revenue_ready"] += revenue_ready

    def record_reply(self, connector: str) -> None:
        data = self._connector_data.setdefault(connector, {
            "signals": 0, "companies": 0, "revenue_ready": 0,
            "replies": 0, "meetings": 0, "deals": 0, "revenue": 0.0,
        })
        data["replies"] += 1

    def record_meeting(self, connector: str) -> None:
        data = self._connector_data.setdefault(connector, {
            "signals": 0, "companies": 0, "revenue_ready": 0,
            "replies": 0, "meetings": 0, "deals": 0, "revenue": 0.0,
        })
        data["meetings"] += 1

    def record_deal(self, connector: str, revenue: float = 0.0) -> None:
        data = self._connector_data.setdefault(connector, {
            "signals": 0, "companies": 0, "revenue_ready": 0,
            "replies": 0, "meetings": 0, "deals": 0, "revenue": 0.0,
        })
        data["deals"] += 1
        data["revenue"] += revenue

    def calculate(self, connector: str) -> ConnectorRoi:
        data = self._connector_data.get(connector, {
            "signals": 0, "companies": 0, "revenue_ready": 0,
            "replies": 0, "meetings": 0, "deals": 0, "revenue": 0.0,
        })
        rr = data["revenue_ready"]
        return ConnectorRoi(
            connector=connector,
            signals=data["signals"],
            companies=data["companies"],
            revenue_ready=rr,
            replies=data["replies"],
            meetings=data["meetings"],
            deals=data["deals"],
            revenue=data["revenue"],
            reply_rate=(data["replies"] / rr * 100.0) if rr > 0 else 0.0,
            meeting_rate=(
                (data["meetings"] / data["replies"] * 100.0)
                if data["replies"] > 0 else 0.0
            ),
            win_rate=(data["deals"] / data["meetings"] * 100.0) if data["meetings"] > 0 else 0.0,
        )

    def calculate_all(self) -> list[ConnectorRoi]:
        return [self.calculate(c) for c in sorted(self._connector_data.keys())]

    def rank_by_revenue(self) -> list[ConnectorRoi]:
        return sorted(self.calculate_all(), key=lambda x: x.revenue, reverse=True)

    def rank_by_meetings(self) -> list[ConnectorRoi]:
        return sorted(self.calculate_all(), key=lambda x: x.meetings, reverse=True)

    def rank_by_replies(self) -> list[ConnectorRoi]:
        return sorted(self.calculate_all(), key=lambda x: x.replies, reverse=True)

    def get_best_connector(self) -> ConnectorRoi | None:
        ranked = self.rank_by_revenue()
        return ranked[0] if ranked else None

    def get_worst_connector(self) -> ConnectorRoi | None:
        ranked = self.rank_by_revenue()
        return ranked[-1] if ranked else None
