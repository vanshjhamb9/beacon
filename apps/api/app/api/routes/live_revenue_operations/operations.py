"""Live Revenue Operations Platform (LROP) API — Sprint 38.

Endpoints:
    GET /inbox — Get inbox opportunities
    GET /pipeline — Get pipeline board
    GET /feed — Get live discovery feed
    GET /review — Get review workspace
    GET /connectors/roi — Get connector ROI
    GET /aging — Get opportunity aging
    GET /today — Get today's workspace
    GET /revenue — Get revenue metrics
    POST /opportunity/{id}/status — Update opportunity status
    POST /opportunity/{id}/review — Submit review
    POST /opportunity/bulk — Bulk operations
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query

router = APIRouter(prefix="/lrop", tags=["live-revenue-operations"])


# === In-memory stores ===

_inbox: dict[str, dict[str, Any]] = {}
_pipeline: dict[str, dict[str, Any]] = {}
_feed: list[dict[str, Any]] = []
_reviews: dict[str, list[dict[str, Any]]] = {}
_connector_roi: dict[str, dict[str, Any]] = {}
_aging: dict[str, dict[str, Any]] = {}
_outreach: list[dict[str, Any]] = []
_replies: list[dict[str, Any]] = []
_meetings: list[dict[str, Any]] = []
_proposals: list[dict[str, Any]] = []
_revenue: list[dict[str, Any]] = []


# === Helper functions ===

def _seed_demo_data():
    """Seed demo data for testing."""
    if _inbox:
        return

    demo_opps = [
        {
            "id": "opp-001",
            "company_name": "TechFlow AI",
            "website": "https://techflow.ai",
            "buying_signal": "Hiring",
            "connector": "linkedin_jobs",
            "quality_score": 92,
            "signal_age_days": 5,
            "why_now": "Actively hiring 8 SDRs",
            "status": "new",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "opp-002",
            "company_name": "CloudFirst",
            "website": "https://cloudfirst.com",
            "buying_signal": "Funding",
            "connector": "hacker_news",
            "quality_score": 85,
            "signal_age_days": 15,
            "why_now": "Raised Series A",
            "status": "approved",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "opp-003",
            "company_name": "GrowthEdge",
            "website": "https://growthedge.com",
            "buying_signal": "Expansion",
            "connector": "product_hunt",
            "quality_score": 78,
            "signal_age_days": 20,
            "why_now": "Opening London office",
            "status": "contacted",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    for opp in demo_opps:
        _inbox[opp["id"]] = opp
        _pipeline[opp["id"]] = opp
        _aging[opp["id"]] = {
            "opportunity_id": opp["id"],
            "age_days": opp["signal_age_days"],
            "color": "green" if opp["signal_age_days"] <= 7 else "yellow" if opp["signal_age_days"] <= 14 else "orange",
            "is_expired": False,
        }

    # Seed connector ROI
    _connector_roi["linkedin_jobs"] = {
        "connector_name": "linkedin_jobs",
        "signals": 150,
        "accepted": 45,
        "revenue_ready": 12,
        "contacted": 8,
        "replies": 3,
        "meetings": 2,
        "customers": 1,
        "revenue": 5000.0,
        "acceptance_rate": 0.3,
        "meeting_rate": 0.25,
    }
    _connector_roi["hacker_news"] = {
        "connector_name": "hacker_news",
        "signals": 200,
        "accepted": 30,
        "revenue_ready": 8,
        "contacted": 5,
        "replies": 1,
        "meetings": 0,
        "customers": 0,
        "revenue": 0.0,
        "acceptance_rate": 0.15,
        "meeting_rate": 0.0,
    }

    # Seed feed
    _feed.append({
        "event_type": "signal_detected",
        "source": "linkedin_jobs",
        "connector": "linkedin_jobs",
        "company_name": "TechFlow AI",
        "buying_signal": "Hiring",
        "stage": "new",
        "status": "detected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


_seed_demo_data()


# === API Endpoints ===

@router.get("/inbox")
async def get_inbox(
    status: str | None = None,
    connector: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Get inbox opportunities."""
    records = list(_inbox.values())

    if status:
        records = [r for r in records if r.get("status") == status]
    if connector:
        records = [r for r in records if r.get("connector") == connector]

    total = len(records)
    records = records[offset:offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "records": records,
        "statistics": {
            "total": len(_inbox),
            "new": sum(1 for r in _inbox.values() if r.get("status") == "new"),
            "approved": sum(1 for r in _inbox.values() if r.get("status") == "approved"),
            "contacted": sum(1 for r in _inbox.values() if r.get("status") == "contacted"),
        },
    }


@router.get("/pipeline")
async def get_pipeline() -> dict[str, Any]:
    """Get pipeline board (Kanban)."""
    stages: dict[str, list[dict[str, Any]]] = {
        "new": [],
        "review": [],
        "approved": [],
        "contacted": [],
        "replied": [],
        "meeting": [],
        "proposal": [],
        "negotiation": [],
        "won": [],
        "lost": [],
    }

    for opp in _pipeline.values():
        stage = opp.get("status", "new")
        if stage in stages:
            stages[stage].append(opp)

    return {
        "stages": stages,
        "stage_counts": {s: len(opp) for s, opp in stages.items()},
        "total": len(_pipeline),
    }


@router.get("/feed")
async def get_feed(
    limit: int = Query(50, ge=1, le=200),
    connector: str | None = None,
    event_type: str | None = None,
) -> dict[str, Any]:
    """Get live discovery feed."""
    events = list(_feed)

    if connector:
        events = [e for e in events if e.get("connector") == connector]
    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]

    # Sort by timestamp (newest first)
    events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {
        "total": len(events),
        "events": events[:limit],
        "auto_refresh_seconds": 5,
    }


@router.get("/review")
async def get_review_workspace() -> dict[str, Any]:
    """Get review workspace."""
    pending = [r for r in _inbox.values() if r.get("status") == "new"]

    return {
        "pending_review": pending,
        "total_pending": len(pending),
        "review_history": _reviews,
    }


@router.get("/connectors/roi")
async def get_connector_roi() -> dict[str, Any]:
    """Get connector ROI metrics."""
    connectors = list(_connector_roi.values())

    # Calculate totals
    total_signals = sum(c.get("signals", 0) for c in connectors)
    total_revenue = sum(c.get("revenue", 0) for c in connectors)

    return {
        "connectors": connectors,
        "total_connectors": len(connectors),
        "total_signals": total_signals,
        "total_revenue": total_revenue,
        "best_connector": max(connectors, key=lambda c: c.get("acceptance_rate", 0)) if connectors else None,
    }


@router.get("/aging")
async def get_aging() -> dict[str, Any]:
    """Get opportunity aging metrics."""
    aging_records = list(_aging.values())

    by_color = {"green": 0, "yellow": 0, "orange": 0, "red": 0}
    for record in aging_records:
        color = record.get("color", "green")
        if color in by_color:
            by_color[color] += 1

    return {
        "total": len(aging_records),
        "by_color": by_color,
        "records": aging_records,
    }


@router.get("/today")
async def get_todays_workspace() -> dict[str, Any]:
    """Get today's workspace."""
    today = datetime.now(timezone.utc).date()

    todays_opps = [
        o for o in _inbox.values()
        if o.get("created_at", "").startswith(str(today))
    ]

    return {
        "date": today.isoformat(),
        "opportunities": {
            "total": len(todays_opps),
            "new": sum(1 for o in todays_opps if o.get("status") == "new"),
            "revenue_ready": sum(1 for o in todays_opps if o.get("status") == "revenue_ready"),
        },
        "connector_winner": _get_connector_winner(),
        "worst_connector": _get_worst_connector(),
        "follow_ups_needed": _get_follow_ups(),
    }


@router.get("/revenue")
async def get_revenue_metrics() -> dict[str, Any]:
    """Get revenue metrics."""
    total_revenue = sum(r.get("amount", 0) for r in _revenue)
    pipeline_value = sum(
        o.get("revenue_potential", 0)
        for o in _pipeline.values()
        if o.get("status") in ("contacted", "replied", "meeting", "proposal", "negotiation")
    )

    return {
        "total_revenue": total_revenue,
        "pipeline_value": pipeline_value,
        "total_deals": len(_revenue),
        "avg_deal_size": total_revenue / max(len(_revenue), 1),
    }


@router.post("/opportunity/{opportunity_id}/status")
async def update_status(
    opportunity_id: str,
    new_status: str,
    notes: str = "",
) -> dict[str, Any]:
    """Update opportunity status."""
    opp = _inbox.get(opportunity_id)
    if not opp:
        return {"error": "Opportunity not found"}

    old_status = opp.get("status", "unknown")
    opp["status"] = new_status
    opp["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Update pipeline
    if opportunity_id in _pipeline:
        _pipeline[opportunity_id]["status"] = new_status

    # Record in feed
    _feed.insert(0, {
        "event_type": "status_changed",
        "source": "manual",
        "connector": opp.get("connector", "unknown"),
        "company_name": opp.get("company_name", "unknown"),
        "buying_signal": opp.get("buying_signal", "unknown"),
        "stage": new_status,
        "status": "updated",
        "evidence": {"from": old_status, "to": new_status, "notes": notes},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "opportunity_id": opportunity_id,
        "old_status": old_status,
        "new_status": new_status,
        "updated_at": opp["updated_at"],
    }


@router.post("/opportunity/{opportunity_id}/review")
async def submit_review(
    opportunity_id: str,
    decision: str,
    notes: str = "",
    reviewer: str = "founder",
) -> dict[str, Any]:
    """Submit review for opportunity."""
    if opportunity_id not in _reviews:
        _reviews[opportunity_id] = []

    review = {
        "decision": decision,
        "notes": notes,
        "reviewer": reviewer,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    _reviews[opportunity_id].append(review)

    # Update status based on decision
    if decision == "approve":
        await update_status(opportunity_id, "approved", notes)
    elif decision == "reject":
        await update_status(opportunity_id, "archived", notes)
    elif decision == "spam":
        await update_status(opportunity_id, "spam", notes)

    return {
        "opportunity_id": opportunity_id,
        "review": review,
    }


@router.post("/opportunity/bulk")
async def bulk_action(
    opportunity_ids: list[str],
    action: str,
    notes: str = "",
) -> dict[str, Any]:
    """Bulk operations on opportunities."""
    results = []

    for opp_id in opportunity_ids:
        if action == "approve":
            result = await update_status(opp_id, "approved", notes)
        elif action == "reject":
            result = await update_status(opp_id, "archived", notes)
        elif action == "spam":
            result = await update_status(opp_id, "spam", notes)
        elif action == "delete":
            if opp_id in _inbox:
                del _inbox[opp_id]
                result = {"opportunity_id": opp_id, "status": "deleted"}
            else:
                result = {"opportunity_id": opp_id, "error": "Not found"}
        else:
            result = {"opportunity_id": opp_id, "error": f"Unknown action: {action}"}

        results.append(result)

    return {
        "action": action,
        "total": len(opportunity_ids),
        "results": results,
    }


# === Helper functions ===

def _get_connector_winner() -> dict[str, Any]:
    """Get best performing connector."""
    if not _connector_roi:
        return {"connector": "none", "score": 0}
    best = max(_connector_roi.values(), key=lambda c: c.get("revenue_ready", 0))
    return {"connector": best.get("connector_name"), "revenue_ready": best.get("revenue_ready", 0)}


def _get_worst_connector() -> dict[str, Any]:
    """Get worst performing connector."""
    if not _connector_roi:
        return {"connector": "none", "score": 0}
    worst = min(_connector_roi.values(), key=lambda c: c.get("acceptance_rate", 0))
    return {"connector": worst.get("connector_name"), "acceptance_rate": worst.get("acceptance_rate", 0)}


def _get_follow_ups() -> list[dict[str, Any]]:
    """Get opportunities needing follow-up."""
    follow_ups = []
    for opp in _inbox.values():
        if opp.get("status") == "contacted":
            follow_ups.append({
                "opportunity_id": opp.get("id"),
                "company_name": opp.get("company_name"),
                "days_since_contact": 3,
            })
    return follow_ups
