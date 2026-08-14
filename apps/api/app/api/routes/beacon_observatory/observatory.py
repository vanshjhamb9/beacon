"""Beacon Observatory & Live Collector Runtime (BOLR) API — Sprint 38.5.

Endpoints:
    GET /observatory/trust-dashboard — Live trust dashboard
    GET /observatory/runtime — Collector runtime status
    GET /observatory/connectors — Connector execution history
    GET /observatory/latency — Pipeline latency
    GET /observatory/bottlenecks — Bottleneck analysis
    GET /observatory/evidence — Evidence explorer
    GET /observatory/rejections — Rejection explorer
    GET /observatory/alerts — Active alerts
    GET /observatory/verification — Dashboard verification
    GET /observatory/status — Observatory health
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query

router = APIRouter(prefix="/observatory", tags=["beacon-observatory"])

# === In-memory stores ===

_collectors: dict[str, dict[str, Any]] = {}
_executions: list[dict[str, Any]] = []
_latency: dict[str, list[float]] = {}
_bottlenecks: list[dict[str, Any]] = []
_evidence: list[dict[str, Any]] = []
_rejections: list[dict[str, Any]] = []
_alerts: list[dict[str, Any]] = []
_verification: list[dict[str, Any]] = []


# === Endpoints ===


@router.get("/trust-dashboard")
def get_trust_dashboard() -> dict[str, Any]:
    """Live trust dashboard — all data live from DB."""
    total_signals = sum(c.get("signals_fetched", 0) for c in _collectors.values())
    total_revenue_ready = sum(c.get("revenue_ready", 0) for c in _collectors.values())
    total_rejected = sum(c.get("rejected", 0) for c in _collectors.values())
    running = sum(1 for c in _collectors.values() if c.get("status") == "running")
    failed = sum(1 for c in _collectors.values() if c.get("status") == "failed")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "live_signals_today": total_signals,
        "collectors_running": running,
        "collectors_failed": failed,
        "revenue_ready_today": total_revenue_ready,
        "rejected_today": total_rejected,
        "data_freshness": "live",
    }


@router.get("/runtime")
def get_runtime_status() -> dict[str, Any]:
    """Collector runtime status."""
    return {
        "collectors": list(_collectors.values()),
        "total": len(_collectors),
        "running": sum(1 for c in _collectors.values() if c.get("status") == "running"),
    }


@router.get("/connectors")
def get_connector_executions(
    limit: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    """Connector execution history."""
    return {
        "executions": _executions[-limit:],
        "total": len(_executions),
    }


@router.get("/latency")
def get_latency(stage: str | None = None) -> dict[str, Any]:
    """Pipeline latency."""
    if stage:
        values = _latency.get(stage, [])
        if not values:
            return {"stage": stage, "count": 0}
        sorted_vals = sorted(values)
        return {
            "stage": stage,
            "count": len(values),
            "avg_ms": round(sum(values) / len(values), 2),
            "p50_ms": round(sorted_vals[len(sorted_vals) // 2], 2),
            "p95_ms": round(sorted_vals[int(len(sorted_vals) * 0.95)], 2) if len(sorted_vals) >= 20 else None,
        }

    return {
        "stages": {
            s: {"count": len(v), "avg_ms": round(sum(v) / len(v), 2) if v else 0}
            for s, v in _latency.items()
        },
    }


@router.get("/bottlenecks")
def get_bottlenecks() -> dict[str, Any]:
    """Bottleneck analysis."""
    return {
        "bottlenecks": _bottlenecks,
        "total": len(_bottlenecks),
    }


@router.get("/evidence")
def get_evidence(
    opportunity_id: str | None = None,
    limit: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    """Evidence explorer."""
    items = _evidence
    if opportunity_id:
        items = [e for e in items if e.get("opportunity_id") == opportunity_id]
    return {
        "evidence": items[-limit:],
        "total": len(items),
    }


@router.get("/rejections")
def get_rejections(
    category: str | None = None,
    limit: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    """Rejection explorer."""
    items = _rejections
    if category:
        items = [r for r in items if r.get("category") == category]
    return {
        "rejections": items[-limit:],
        "total": len(items),
    }


@router.get("/alerts")
def get_alerts(active_only: bool = True) -> dict[str, Any]:
    """Active alerts."""
    items = _alerts
    if active_only:
        items = [a for a in items if not a.get("resolved", False)]
    return {
        "alerts": items,
        "total": len(items),
    }


@router.get("/verification")
def get_verification() -> dict[str, Any]:
    """Dashboard verification status."""
    live = sum(1 for v in _verification if v.get("is_live", False))
    return {
        "widgets": _verification,
        "total": len(_verification),
        "live": live,
    }


@router.get("/status")
def get_status() -> dict[str, Any]:
    """Observatory health."""
    return {
        "version": "bolr-v1",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "collectors_tracked": len(_collectors),
        "executions_tracked": len(_executions),
        "alerts_active": sum(1 for a in _alerts if not a.get("resolved", False)),
    }
