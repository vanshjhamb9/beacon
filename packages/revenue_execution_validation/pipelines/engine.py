"""Revenue Execution pipeline — evaluate one company against Revenue Ready definition."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from revenue_execution_validation.revenue_ready.engine import RevenueReadyDefinitionEngine
from revenue_execution_validation.models.types import RevSnapshot


class RevenueExecutionPipeline:
    def __init__(self) -> None:
        self.definition = RevenueReadyDefinitionEngine()

    def evaluate(self, payload: dict[str, Any]) -> RevSnapshot:
        t0 = perf_counter()
        check = self.definition.evaluate(payload)
        ms = (perf_counter() - t0) * 1000
        return RevSnapshot(
            company_id=str(payload.get("company_id") or payload.get("id") or "unknown"),
            company_name=check.company_name,
            source=str(payload.get("source") or check.source or "unknown"),
            check=check,
            rejection_reasons=list(check.rejection_reasons),
            processing_ms=round(ms, 3),
            evidence=[
                f"ready:{check.is_revenue_ready}",
                f"email:{check.business_email}",
                f"dm:{check.decision_maker}",
                *[r.value for r in check.rejection_reasons[:5]],
            ],
        )
