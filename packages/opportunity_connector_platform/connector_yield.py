"""Revenue impact yield calculations for connectors."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class ConnectorYield:
    signals: int = 0
    accepted: int = 0
    identity_matched: int = 0
    verified_companies: int = 0
    sales_ready: int = 0
    revenue_ready: int = 0
    contacted: int = 0
    replies: int = 0
    meetings: int = 0
    won: int = 0
    revenue: float = 0.0


class ConnectorYieldEngine:
    """Full funnel yield calculation for every connector."""

    def calculate(self, row: ConnectorYield) -> dict[str, float | int]:
        return {
            **asdict(row),
            "signal_yield": self._pct(row.accepted, row.signals),
            "revenue_yield": self._pct(row.revenue_ready, row.signals),
            "meeting_yield": self._pct(row.meetings, row.signals),
            "acceptance_rate": self._pct(row.accepted, row.signals),
            "conversion_rate": self._pct(row.won, row.signals),
            "revenue_per_signal": round(row.revenue / row.signals, 2) if row.signals else 0.0,
            "identity_match_rate": self._pct(row.identity_matched, row.accepted),
            "verification_rate": self._pct(row.verified_companies, row.identity_matched),
            "sales_readiness_rate": self._pct(row.sales_ready, row.verified_companies),
            "revenue_readiness_rate": self._pct(row.revenue_ready, row.sales_ready),
            "contact_rate": self._pct(row.contacted, row.revenue_ready),
            "reply_rate": self._pct(row.replies, row.contacted),
            "meeting_rate": self._pct(row.meetings, row.replies),
            "win_rate": self._pct(row.won, row.meetings),
        }

    def funnel_summary(self, row: ConnectorYield) -> dict[str, int]:
        return {
            "signals": row.signals,
            "accepted": row.accepted,
            "identity_matched": row.identity_matched,
            "verified_companies": row.verified_companies,
            "sales_ready": row.sales_ready,
            "revenue_ready": row.revenue_ready,
            "contacted": row.contacted,
            "replies": row.replies,
            "meetings": row.meetings,
            "won": row.won,
        }

    def _pct(self, numerator: int | float, denominator: int | float) -> float:
        return round((numerator / denominator) * 100, 2) if denominator else 0.0
