"""Revenue yield analytics per connector — no assumptions."""

from __future__ import annotations

from typing import Any

from revenue_data_acquisition.connector_quality.engine import ConnectorQualityEngine
from revenue_data_acquisition.models.types import RevenueYield


class RevenueYieldEngine:
    def __init__(self) -> None:
        self.quality = ConnectorQualityEngine()

    def compute(self, rows: list[dict[str, Any]]) -> list[RevenueYield]:
        scores = self.quality.score(rows)
        return [
            RevenueYield(
                connector=s.connector,
                signals=s.signals,
                websites=s.official_websites,
                companies=s.verified_companies,
                emails=s.business_emails,
                decision_makers=s.decision_makers,
                revenue_ready=s.revenue_ready,
                yield_pct=s.revenue_yield,
            )
            for s in scores
        ]
