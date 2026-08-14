"""Industry ROI engine — calculates ROI per industry from real outcomes."""

from __future__ import annotations

from typing import Any

from validation_engine.models import IndustryRoi


class IndustryRoiEngine:
    """Calculates ROI metrics per industry from real business outcomes."""

    def __init__(self) -> None:
        self._industry_data: dict[str, dict[str, Any]] = {}

    def record_company(self, industry: str) -> None:
        data = self._industry_data.setdefault(industry, {
            "companies": 0, "revenue_ready": 0, "replies": 0,
            "meetings": 0, "deals": 0, "revenue": 0.0,
        })
        data["companies"] += 1

    def record_revenue_ready(self, industry: str) -> None:
        data = self._industry_data.setdefault(industry, {
            "companies": 0, "revenue_ready": 0, "replies": 0,
            "meetings": 0, "deals": 0, "revenue": 0.0,
        })
        data["revenue_ready"] += 1

    def record_reply(self, industry: str) -> None:
        data = self._industry_data.setdefault(industry, {
            "companies": 0, "revenue_ready": 0, "replies": 0,
            "meetings": 0, "deals": 0, "revenue": 0.0,
        })
        data["replies"] += 1

    def record_meeting(self, industry: str) -> None:
        data = self._industry_data.setdefault(industry, {
            "companies": 0, "revenue_ready": 0, "replies": 0,
            "meetings": 0, "deals": 0, "revenue": 0.0,
        })
        data["meetings"] += 1

    def record_deal(self, industry: str, revenue: float = 0.0) -> None:
        data = self._industry_data.setdefault(industry, {
            "companies": 0, "revenue_ready": 0, "replies": 0,
            "meetings": 0, "deals": 0, "revenue": 0.0,
        })
        data["deals"] += 1
        data["revenue"] += revenue

    def calculate(self, industry: str) -> IndustryRoi:
        data = self._industry_data.get(industry, {
            "companies": 0, "revenue_ready": 0, "replies": 0,
            "meetings": 0, "deals": 0, "revenue": 0.0,
        })
        rr = data["revenue_ready"]
        replies = data["replies"]
        return IndustryRoi(
            industry=industry,
            companies=data["companies"],
            revenue_ready=rr,
            replies=replies,
            meetings=data["meetings"],
            deals=data["deals"],
            revenue=data["revenue"],
            reply_rate=(replies / rr * 100.0) if rr > 0 else 0.0,
            meeting_rate=(data["meetings"] / replies * 100.0) if replies > 0 else 0.0,
            win_rate=(data["deals"] / data["meetings"] * 100.0) if data["meetings"] > 0 else 0.0,
        )

    def calculate_all(self) -> list[IndustryRoi]:
        return [self.calculate(i) for i in sorted(self._industry_data.keys())]

    def rank_by_revenue(self) -> list[IndustryRoi]:
        return sorted(self.calculate_all(), key=lambda x: x.revenue, reverse=True)

    def rank_by_win_rate(self) -> list[IndustryRoi]:
        return sorted(self.calculate_all(), key=lambda x: x.win_rate, reverse=True)

    def rank_by_reply_rate(self) -> list[IndustryRoi]:
        return sorted(self.calculate_all(), key=lambda x: x.reply_rate, reverse=True)

    def get_best_industry(self) -> IndustryRoi | None:
        ranked = self.rank_by_revenue()
        return ranked[0] if ranked else None
