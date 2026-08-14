"""Connector ROI math — deterministic unit costs, no AI."""

from __future__ import annotations

from intelligence_center.models import CONNECTOR_UNIT_COST, ConnectorRoiRow


def compute_roi_row(
    *,
    connector: str,
    healthy: bool,
    signals: int = 0,
    companies: int = 0,
    emails: int = 0,
    decision_makers: int = 0,
    revenue_ready: int = 0,
    meetings: int = 0,
    wins: int = 0,
    latency_ms: float = 0.0,
    success_pct: float = 0.0,
    quota_used_pct: float = 0.0,
    detail: str = "",
) -> ConnectorRoiRow:
    unit = CONNECTOR_UNIT_COST.get(connector, 0.0)
    billable = emails + decision_makers if unit > 0 else 0
    # Free collectors: cost stays 0; paid providers billed on enrichment volume.
    if unit > 0 and billable == 0:
        billable = max(signals, companies, revenue_ready)
    api_cost = round(unit * billable, 2)
    # Win % is meetings → wins conversion. No meetings ⇒ 0 (never invent 100%).
    win_pct = round((wins / meetings) * 100.0, 1) if meetings > 0 else 0.0
    win_pct = min(max(win_pct, 0.0), 100.0)
    return ConnectorRoiRow(
        connector=connector,
        healthy=healthy,
        signals=int(signals or 0),
        companies=int(companies or 0),
        emails=int(emails or 0),
        decision_makers=int(decision_makers or 0),
        revenue_ready=int(revenue_ready or 0),
        meetings=int(meetings or 0),
        wins=int(wins or 0),
        win_pct=win_pct,
        latency_ms=round(float(latency_ms or 0.0), 1),
        api_cost=api_cost,
        quota_used_pct=round(float(quota_used_pct or 0.0), 1),
        success_pct=round(float(success_pct or 0.0), 1),
        detail=detail,
    )


def rank_connectors(rows: list[ConnectorRoiRow]) -> list[ConnectorRoiRow]:
    """Highest revenue-ready yield first, then emails, then signals."""
    return sorted(
        rows,
        key=lambda r: (r.revenue_ready, r.emails, r.decision_makers, r.signals),
        reverse=True,
    )
