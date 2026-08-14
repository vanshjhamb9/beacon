"""Connector dashboard assembly."""

from __future__ import annotations

from collections import Counter
from typing import Any

from opportunity_connector_platform.connector_quality import ConnectorQuality
from opportunity_connector_platform.connector_yield import ConnectorYield, ConnectorYieldEngine


class ConnectorDashboard:
    """Build dashboard views from connector data."""

    def __init__(
        self,
        *,
        yield_engine: ConnectorYieldEngine | None = None,
        quality: ConnectorQuality | None = None,
    ) -> None:
        self.yield_engine = yield_engine or ConnectorYieldEngine()
        self.quality = quality or ConnectorQuality()

    def cards(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        for row in rows:
            yield_payload = self.yield_engine.calculate(
                ConnectorYield(
                    signals=int(row.get("signals") or 0),
                    accepted=int(row.get("accepted") or 0),
                    revenue_ready=int(row.get("revenue_ready") or 0),
                    meetings=int(row.get("meetings") or 0),
                    won=int(row.get("won") or 0),
                    revenue=float(row.get("revenue") or 0),
                )
            )
            cards.append(
                {
                    "connector": row.get("connector_id"),
                    "status": row.get("status", "unknown"),
                    "signals_today": yield_payload["signals"],
                    "accepted": yield_payload["accepted"],
                    "rejected": max(yield_payload["signals"] - yield_payload["accepted"], 0),
                    "yield": yield_payload["signal_yield"],
                    "revenue_ready": yield_payload["revenue_ready"],
                    "health": row.get("health", "unknown"),
                    "roi_action": self.quality.roi_action(
                        revenue_per_signal=float(yield_payload["revenue_per_signal"]),
                        failure_rate=float(row.get("failure_rate") or 0),
                        acceptance_rate=float(yield_payload["acceptance_rate"]),
                    ),
                }
            )
        return cards

    def details(self, connector_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        events = [row for row in rows if row.get("connector_id") == connector_id]
        return {
            "connector_id": connector_id,
            "events_timeline": events,
            "top_rejections": dict(Counter(str(row.get("rejection_reason") or "accepted") for row in events)),
            "top_event_types": dict(Counter(str(row.get("event_type") or "Unknown") for row in events)),
            "top_companies": dict(Counter(str(row.get("company_name") or "Unknown") for row in events)),
            "pipeline_funnel": self._sum(events, "pipeline_funnel"),
            "revenue_funnel": self._sum(events, "revenue_funnel"),
            "configuration": {},
            "capabilities": [],
            "authentication": "unknown",
        }

    def operations_center_section(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        signals = sum(int(row.get("signals") or 0) for row in rows)
        accepted = sum(int(row.get("accepted") or 0) for row in rows)
        revenue = sum(float(row.get("revenue") or 0) for row in rows)
        failures = sum(int(row.get("failures") or 0) for row in rows)
        return {
            "section": "Opportunity Connector Platform",
            "live_connectors": sum(1 for row in rows if row.get("enabled")),
            "signals_per_sec": round(signals / 86_400, 4),
            "acceptance": round((accepted / signals) * 100, 2) if signals else 0.0,
            "revenue_yield": revenue,
            "failures": failures,
            "rate_limits": [row for row in rows if row.get("rate_limit_remaining") == 0],
            "upcoming_jobs": [row.get("connector_id") for row in rows if row.get("enabled")],
            "disabled_sources": [row.get("connector_id") for row in rows if not row.get("enabled")],
        }

    def _sum(self, rows: list[dict[str, Any]], key: str) -> dict[str, int]:
        totals: Counter[str] = Counter()
        for row in rows:
            for stage, value in dict(row.get(key) or {}).items():
                totals[stage] += int(value or 0)
        return dict(totals)
