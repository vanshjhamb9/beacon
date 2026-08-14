"""Funnel engine — calculates conversion between every pipeline stage."""

from __future__ import annotations

from typing import Any

from validation_engine import VALIDATION_STAGES
from validation_engine.lead_validator import LeadValidator


class FunnelEngine:
    """Calculates funnel conversion rates between pipeline stages."""

    def __init__(self, lead_validator: LeadValidator | None = None) -> None:
        self.lead_validator = lead_validator or LeadValidator()

    def calculate_funnel(self) -> list[dict[str, Any]]:
        return self.lead_validator.get_funnel()

    def calculate_conversion(
        self, from_stage: str, to_stage: str
    ) -> dict[str, Any]:
        from_count = self.lead_validator.get_stage_count(from_stage)
        to_count = self.lead_validator.get_stage_count(to_stage)
        conversion_rate = 0.0
        drop_off = 100.0
        if from_count > 0:
            conversion_rate = (to_count / from_count) * 100.0
            drop_off = 100.0 - conversion_rate
        return {
            "from_stage": from_stage,
            "to_stage": to_stage,
            "from_count": from_count,
            "to_count": to_count,
            "conversion_rate": round(conversion_rate, 2),
            "drop_off": round(drop_off, 2),
        }

    def get_biggest_bottleneck(self) -> dict[str, Any]:
        funnel = self.calculate_funnel()
        if not funnel:
            return {"stage": "none", "drop_off": 0.0}
        worst = max(funnel, key=lambda x: x["drop_off"])
        return {"stage": worst["stage"], "drop_off": worst["drop_off"]}

    def get_stage_conversions(self) -> list[dict[str, Any]]:
        conversions = []
        for i in range(len(VALIDATION_STAGES) - 1):
            from_stage = VALIDATION_STAGES[i]
            to_stage = VALIDATION_STAGES[i + 1]
            conversions.append(self.calculate_conversion(from_stage, to_stage))
        return conversions

    def get_conversion_summary(self) -> dict[str, Any]:
        conversions = self.get_stage_conversions()
        total_companies = self.lead_validator.get_stage_count(VALIDATION_STAGES[0])
        total_won = self.lead_validator.get_stage_count("WON")
        overall_conversion = 0.0
        if total_companies > 0:
            overall_conversion = (total_won / total_companies) * 100.0
        return {
            "total_companies": total_companies,
            "total_won": total_won,
            "overall_conversion_rate": round(overall_conversion, 2),
            "stage_conversions": conversions,
            "biggest_bottleneck": self.get_biggest_bottleneck(),
        }
