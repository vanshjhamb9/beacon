"""Connector quality decisions — deterministic, no AI scoring."""

from __future__ import annotations


class ConnectorQuality:
    """ROI-based quality assessment for connectors."""

    def roi_action(
        self,
        *,
        revenue_per_signal: float,
        failure_rate: float,
        acceptance_rate: float,
    ) -> str:
        if failure_rate >= 50 or acceptance_rate < 5:
            return "disable_review"
        if revenue_per_signal < 1 and acceptance_rate < 10:
            return "deprioritize"
        return "keep_enabled"

    def health_grade(
        self,
        *,
        success_rate: float,
        acceptance_rate: float,
        revenue_yield: float,
    ) -> str:
        score = (success_rate * 0.3) + (acceptance_rate * 0.3) + (revenue_yield * 0.4)
        if score >= 80:
            return "A"
        if score >= 60:
            return "B"
        if score >= 40:
            return "C"
        if score >= 20:
            return "D"
        return "F"

    def should_disable(
        self,
        *,
        failure_rate: float,
        acceptance_rate: float,
        revenue_per_signal: float,
    ) -> bool:
        return failure_rate >= 50 or (acceptance_rate < 5 and revenue_per_signal < 0.01)

    def priority_score(
        self,
        *,
        signal_yield: float,
        revenue_per_signal: float,
        failure_rate: float,
    ) -> float:
        base = signal_yield * 0.4 + revenue_per_signal * 0.4 - failure_rate * 0.2
        return round(max(0.0, min(100.0, base)), 2)
