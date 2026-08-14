"""Connector metric calculations — deterministic, no AI scoring."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricsInput:
    accepted: int = 0
    rejected: int = 0
    failures: int = 0
    runs: int = 0
    latencies: tuple[float, ...] = ()
    signals: int = 0
    revenue_ready: int = 0
    meetings: int = 0
    won: int = 0
    revenue: float = 0.0


class ConnectorMetrics:
    """Pure deterministic metric calculations."""

    def acceptance_rate(self, accepted: int, rejected: int) -> float:
        total = accepted + rejected
        return round((accepted / total) * 100, 2) if total else 0.0

    def rejection_rate(self, accepted: int, rejected: int) -> float:
        total = accepted + rejected
        return round((rejected / total) * 100, 2) if total else 0.0

    def failure_rate(self, failures: int, runs: int) -> float:
        return round((failures / runs) * 100, 2) if runs else 0.0

    def average_latency(self, latencies: list[float] | tuple[float, ...]) -> float:
        items = list(latencies)
        return round(sum(items) / len(items), 2) if items else 0.0

    def p95_latency(self, latencies: list[float] | tuple[float, ...]) -> float:
        items = sorted(latencies)
        if not items:
            return 0.0
        idx = int(len(items) * 0.95)
        return round(items[min(idx, len(items) - 1)], 2)

    def signal_yield(self, accepted: int, signals: int) -> float:
        return round((accepted / signals) * 100, 2) if signals else 0.0

    def revenue_yield(self, revenue_ready: int, signals: int) -> float:
        return round((revenue_ready / signals) * 100, 2) if signals else 0.0

    def meeting_yield(self, meetings: int, signals: int) -> float:
        return round((meetings / signals) * 100, 2) if signals else 0.0

    def conversion_rate(self, won: int, signals: int) -> float:
        return round((won / signals) * 100, 2) if signals else 0.0

    def revenue_per_signal(self, revenue: float, signals: int) -> float:
        return round(revenue / signals, 2) if signals else 0.0

    def calculate_all(self, inp: MetricsInput) -> dict[str, float]:
        return {
            "acceptance_rate": self.acceptance_rate(inp.accepted, inp.rejected),
            "rejection_rate": self.rejection_rate(inp.accepted, inp.rejected),
            "failure_rate": self.failure_rate(inp.failures, inp.runs),
            "average_latency": self.average_latency(inp.latencies),
            "p95_latency": self.p95_latency(inp.latencies),
            "signal_yield": self.signal_yield(inp.accepted, inp.signals),
            "revenue_yield": self.revenue_yield(inp.revenue_ready, inp.signals),
            "meeting_yield": self.meeting_yield(inp.meetings, inp.signals),
            "conversion_rate": self.conversion_rate(inp.won, inp.signals),
            "revenue_per_signal": self.revenue_per_signal(inp.revenue, inp.signals),
        }
