"""Trigger ROI engine — calculates ROI per buying trigger from real outcomes."""

from __future__ import annotations

from typing import Any

from validation_engine.models import TriggerRoi


class TriggerRoiEngine:
    """Calculates ROI metrics per buying trigger from real business outcomes."""

    def __init__(self) -> None:
        self._trigger_data: dict[str, dict[str, Any]] = {}

    def record_company(self, trigger: str) -> None:
        data = self._trigger_data.setdefault(trigger, {
            "companies": 0, "replies": 0, "meetings": 0,
            "deals": 0, "revenue": 0.0,
        })
        data["companies"] += 1

    def record_reply(self, trigger: str) -> None:
        data = self._trigger_data.setdefault(trigger, {
            "companies": 0, "replies": 0, "meetings": 0,
            "deals": 0, "revenue": 0.0,
        })
        data["replies"] += 1

    def record_meeting(self, trigger: str) -> None:
        data = self._trigger_data.setdefault(trigger, {
            "companies": 0, "replies": 0, "meetings": 0,
            "deals": 0, "revenue": 0.0,
        })
        data["meetings"] += 1

    def record_deal(self, trigger: str, revenue: float = 0.0) -> None:
        data = self._trigger_data.setdefault(trigger, {
            "companies": 0, "replies": 0, "meetings": 0,
            "deals": 0, "revenue": 0.0,
        })
        data["deals"] += 1
        data["revenue"] += revenue

    def calculate(self, trigger: str) -> TriggerRoi:
        data = self._trigger_data.get(trigger, {
            "companies": 0, "replies": 0, "meetings": 0,
            "deals": 0, "revenue": 0.0,
        })
        companies = data["companies"]
        replies = data["replies"]
        meetings = data["meetings"]
        return TriggerRoi(
            trigger=trigger,
            companies=companies,
            replies=replies,
            meetings=meetings,
            deals=data["deals"],
            revenue=data["revenue"],
            reply_rate=(replies / companies * 100.0) if companies > 0 else 0.0,
            meeting_rate=(meetings / replies * 100.0) if replies > 0 else 0.0,
            revenue_rate=(data["deals"] / companies * 100.0) if companies > 0 else 0.0,
        )

    def calculate_all(self) -> list[TriggerRoi]:
        return [self.calculate(t) for t in sorted(self._trigger_data.keys())]

    def rank_by_revenue(self) -> list[TriggerRoi]:
        return sorted(self.calculate_all(), key=lambda x: x.revenue, reverse=True)

    def rank_by_conversion(self) -> list[TriggerRoi]:
        return sorted(self.calculate_all(), key=lambda x: x.revenue_rate, reverse=True)

    def get_best_trigger(self) -> TriggerRoi | None:
        ranked = self.rank_by_revenue()
        return ranked[0] if ranked else None
