from __future__ import annotations

from typing import Any

from revenue_readiness_validation.models.types import MetricTarget


class SuccessMetricsEngine:
    """Compare live rates against M1 production targets."""

    TARGETS: tuple[tuple[str, float, str], ...] = (
        ("collector_uptime", 99.0, "%"),
        ("identity_completeness", 95.0, "%"),
        ("contact_ready_accounts", 60.0, "%"),
        ("sales_ready_accounts", 40.0, "%"),
        ("duplicate_rate", 5.0, "%"),  # target is less-than
        ("fake_companies", 0.0, "count"),
        ("missing_source_attribution", 0.0, "count"),
        ("founder_queue_with_evidence", 100.0, "%"),
        ("unexplained_a_plus", 0.0, "count"),
        ("end_to_end_pipeline_success", 95.0, "%"),
    )

    LOWER_IS_BETTER = frozenset(
        {"duplicate_rate", "fake_companies", "missing_source_attribution", "unexplained_a_plus"}
    )

    def evaluate(self, actuals: dict[str, float | None]) -> list[MetricTarget]:
        out: list[MetricTarget] = []
        for name, target, unit in self.TARGETS:
            actual = actuals.get(name)
            hit = False
            if actual is not None:
                if name in self.LOWER_IS_BETTER:
                    hit = float(actual) <= target
                else:
                    hit = float(actual) >= target
            out.append(
                MetricTarget(
                    name=name,
                    target=target,
                    actual=None if actual is None else round(float(actual), 2),
                    unit=unit,
                    hit=hit,
                    evidence=[f"target:{target}{unit}", f"actual:{actual}"],
                )
            )
        return out

    def estimated_qualified_per_100(self, sales_ready_rate: float | None, contact_ready_rate: float | None) -> float:
        """Heuristic north-star: blend sales-ready + contact-ready rates into per-100 estimate."""
        sr = float(sales_ready_rate or 0.0)
        cr = float(contact_ready_rate or 0.0)
        # Prefer sales-ready; contact-ready contributes partial credit
        return round(min(100.0, sr + max(0.0, cr - sr) * 0.35), 1)
