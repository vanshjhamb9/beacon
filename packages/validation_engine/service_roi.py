"""Service ROI engine — calculates ROI per service from real outcomes."""

from __future__ import annotations

from typing import Any

from validation_engine.models import ServiceRoi


class ServiceRoiEngine:
    """Calculates ROI metrics per service offering from real business outcomes."""

    def __init__(self) -> None:
        self._service_data: dict[str, dict[str, Any]] = {}

    def record_company(self, service: str) -> None:
        data = self._service_data.setdefault(service, {
            "companies": 0, "replies": 0, "meetings": 0,
            "proposals": 0, "deals": 0, "revenue": 0.0,
        })
        data["companies"] += 1

    def record_reply(self, service: str) -> None:
        data = self._service_data.setdefault(service, {
            "companies": 0, "replies": 0, "meetings": 0,
            "proposals": 0, "deals": 0, "revenue": 0.0,
        })
        data["replies"] += 1

    def record_meeting(self, service: str) -> None:
        data = self._service_data.setdefault(service, {
            "companies": 0, "replies": 0, "meetings": 0,
            "proposals": 0, "deals": 0, "revenue": 0.0,
        })
        data["meetings"] += 1

    def record_proposal(self, service: str) -> None:
        data = self._service_data.setdefault(service, {
            "companies": 0, "replies": 0, "meetings": 0,
            "proposals": 0, "deals": 0, "revenue": 0.0,
        })
        data["proposals"] += 1

    def record_deal(self, service: str, revenue: float = 0.0) -> None:
        data = self._service_data.setdefault(service, {
            "companies": 0, "replies": 0, "meetings": 0,
            "proposals": 0, "deals": 0, "revenue": 0.0,
        })
        data["deals"] += 1
        data["revenue"] += revenue

    def calculate(self, service: str) -> ServiceRoi:
        data = self._service_data.get(service, {
            "companies": 0, "replies": 0, "meetings": 0,
            "proposals": 0, "deals": 0, "revenue": 0.0,
        })
        companies = data["companies"]
        return ServiceRoi(
            service=service,
            companies=companies,
            replies=data["replies"],
            meetings=data["meetings"],
            deals=data["deals"],
            revenue=data["revenue"],
            reply_rate=(
                (data["replies"] / companies * 100.0)
                if companies > 0 else 0.0
            ),
            meeting_rate=(
                (data["meetings"] / data["replies"] * 100.0)
                if data["replies"] > 0 else 0.0
            ),
            proposal_rate=(
                (data["proposals"] / data["meetings"] * 100.0)
                if data["meetings"] > 0 else 0.0
            ),
            win_rate=(
                (data["deals"] / data["proposals"] * 100.0)
                if data["proposals"] > 0 else 0.0
            ),
        )

    def calculate_all(self) -> list[ServiceRoi]:
        return [self.calculate(s) for s in sorted(self._service_data.keys())]

    def rank_by_revenue(self) -> list[ServiceRoi]:
        return sorted(self.calculate_all(), key=lambda x: x.revenue, reverse=True)

    def rank_by_win_rate(self) -> list[ServiceRoi]:
        return sorted(self.calculate_all(), key=lambda x: x.win_rate, reverse=True)

    def get_best_service(self) -> ServiceRoi | None:
        ranked = self.rank_by_revenue()
        return ranked[0] if ranked else None
