"""Analytics V2 assembler — every section filled from operational counters."""

from __future__ import annotations

from typing import Any

from intelligence_center.models import ConnectorRoiRow, DatasetStatistics, HeatmapCell


def build_analytics_v2(
    *,
    discovery: dict[str, Any],
    quality: DatasetStatistics,
    revenue: dict[str, Any],
    pipeline: dict[str, Any],
    outreach: dict[str, Any],
    connectors: list[ConnectorRoiRow],
    enrichment: dict[str, Any],
    industries: list[dict[str, Any]],
    services: list[dict[str, Any]],
    decision_makers: dict[str, Any],
    meetings: dict[str, Any],
    forecast: dict[str, Any],
    heatmap: list[HeatmapCell],
) -> dict[str, Any]:
    top_connectors = [
        {
            "connector": c.connector,
            "revenue_ready": c.revenue_ready,
            "emails": c.emails,
            "api_cost": c.api_cost,
            "success_pct": c.success_pct,
            "win_pct": c.win_pct,
        }
        for c in connectors[:10]
    ]
    return {
        "discovery": discovery,
        "quality": {
            "signals_collected": quality.signals_collected,
            "duplicates": quality.duplicates,
            "spam": quality.spam,
            "duplicate_rate": quality.duplicate_rate,
            "spam_rate": quality.spam_rate,
            "verification_rate": quality.verification_rate,
            "enrichment_coverage": quality.enrichment_coverage,
            "working_websites": quality.working_websites,
            "dead_websites": quality.dead_websites,
        },
        "revenue": revenue,
        "pipeline": pipeline,
        "outreach": outreach,
        "connectors": top_connectors,
        "enrichment": enrichment,
        "industries": industries,
        "services": services,
        "decision_makers": decision_makers,
        "meetings": meetings,
        "forecast": forecast,
        "heatmap": [
            {
                "stage": h.stage,
                "tone": h.tone,
                "count": h.count,
                "success_pct": h.success_pct,
                "avg_duration": h.avg_duration,
                "failures": h.failures,
            }
            for h in heatmap
        ],
    }
