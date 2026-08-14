"""Persona ROI engine — calculates ROI per persona from real outcomes."""

from __future__ import annotations

from typing import Any

from validation_engine.models import PersonaRoi


class PersonaRoiEngine:
    """Calculates ROI metrics per buyer persona from real business outcomes."""

    def __init__(self) -> None:
        self._persona_data: dict[str, dict[str, Any]] = {}

    def record_contacted(self, persona: str) -> None:
        data = self._persona_data.setdefault(persona, {
            "contacted": 0, "replies": 0, "meetings": 0,
            "deals": 0, "revenue": 0.0,
        })
        data["contacted"] += 1

    def record_reply(self, persona: str) -> None:
        data = self._persona_data.setdefault(persona, {
            "contacted": 0, "replies": 0, "meetings": 0,
            "deals": 0, "revenue": 0.0,
        })
        data["replies"] += 1

    def record_meeting(self, persona: str) -> None:
        data = self._persona_data.setdefault(persona, {
            "contacted": 0, "replies": 0, "meetings": 0,
            "deals": 0, "revenue": 0.0,
        })
        data["meetings"] += 1

    def record_deal(self, persona: str, revenue: float = 0.0) -> None:
        data = self._persona_data.setdefault(persona, {
            "contacted": 0, "replies": 0, "meetings": 0,
            "deals": 0, "revenue": 0.0,
        })
        data["deals"] += 1
        data["revenue"] += revenue

    def calculate(self, persona: str) -> PersonaRoi:
        data = self._persona_data.get(persona, {
            "contacted": 0, "replies": 0, "meetings": 0,
            "deals": 0, "revenue": 0.0,
        })
        contacted = data["contacted"]
        replies = data["replies"]
        return PersonaRoi(
            persona=persona,
            contacted=contacted,
            replies=replies,
            meetings=data["meetings"],
            deals=data["deals"],
            revenue=data["revenue"],
            reply_rate=(replies / contacted * 100.0) if contacted > 0 else 0.0,
            meeting_rate=(data["meetings"] / replies * 100.0) if replies > 0 else 0.0,
        )

    def calculate_all(self) -> list[PersonaRoi]:
        return [self.calculate(p) for p in sorted(self._persona_data.keys())]

    def rank_by_revenue(self) -> list[PersonaRoi]:
        return sorted(self.calculate_all(), key=lambda x: x.revenue, reverse=True)

    def rank_by_reply_rate(self) -> list[PersonaRoi]:
        return sorted(self.calculate_all(), key=lambda x: x.reply_rate, reverse=True)

    def get_best_persona(self) -> PersonaRoi | None:
        ranked = self.rank_by_revenue()
        return ranked[0] if ranked else None
