"""Live Opportunity Validation Platform (LOVP) API — Sprint 37.5.

Read-only API for opportunity validation.

Endpoints:
    GET /validation/dashboard — Dashboard metrics
    GET /validation/company/{id} — Company validation
    GET /validation/opportunity/{id} — Opportunity validation
    GET /validation/timeline/{id} — Opportunity timeline
    GET /validation/root-cause/{id} — Root cause analysis
    GET /validation/replay/{id} — Replay opportunity
    GET /validation/rejections — Rejection analysis
    GET /validation/connectors — Connector performance
    GET /validation/statistics — Validation statistics
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query

router = APIRouter(prefix="/validation", tags=["opportunity-validation"])


# === In-memory stores (replace with DB in production) ===

_opportunities: dict[str, dict[str, Any]] = {}
_validations: dict[str, dict[str, Any]] = {}
_timelines: dict[str, list[dict[str, Any]]] = {}
_replays: dict[str, dict[str, Any]] = {}
_human_reviews: dict[str, dict[str, Any]] = {}


# === Helper functions ===

def _seed_demo_data():
    """Seed demo data for testing."""
    if _opportunities:
        return

    demo_opps = [
        {
            "opportunity_id": "opp-001",
            "company_name": "TechFlow AI",
            "website": "https://techflow.ai",
            "connector": "linkedin_jobs",
            "signal_type": "hiring",
            "signal_age_days": 5,
            "quality_score": 92,
            "freshness": "fresh",
            "buying_signal": "Hiring",
            "icp_match": True,
            "region_match": True,
            "industry_match": True,
            "collection_timestamp": datetime.now(timezone.utc).isoformat(),
            "evidence": {"source": "LinkedIn", "title": "Hiring 8 SDRs", "url": "https://linkedin.com/jobs/123"},
        },
        {
            "opportunity_id": "opp-002",
            "company_name": "CloudFirst",
            "website": "https://cloudfirst.com",
            "connector": "hacker_news",
            "signal_type": "funding",
            "signal_age_days": 15,
            "quality_score": 82,
            "freshness": "fresh",
            "buying_signal": "Funding",
            "icp_match": True,
            "region_match": True,
            "industry_match": True,
            "collection_timestamp": datetime.now(timezone.utc).isoformat(),
            "evidence": {"source": "Hacker News", "title": "Raised Series A", "url": "https://news.ycombinator.com/123"},
        },
        {
            "opportunity_id": "opp-003",
            "company_name": "StaleSignals",
            "website": "https://stalesignals.com",
            "connector": "reddit",
            "signal_type": "blog_post",
            "signal_age_days": 180,
            "quality_score": 45,
            "freshness": "ancient",
            "buying_signal": "Blog posts",
            "icp_match": False,
            "region_match": True,
            "industry_match": False,
            "collection_timestamp": datetime.now(timezone.utc).isoformat(),
            "evidence": {"source": "Reddit", "title": "Blog post about AI", "url": "https://reddit.com/123"},
        },
    ]

    for opp in demo_opps:
        _opportunities[opp["opportunity_id"]] = opp
        _validations[opp["opportunity_id"]] = {
            "opportunity_id": opp["opportunity_id"],
            "decision": "approve" if opp["quality_score"] >= 75 else "reject",
            "reasons": [] if opp["quality_score"] >= 75 else ["Low quality score", "Invalid buying signal"],
            "root_cause": "passes_all_gates" if opp["quality_score"] >= 75 else "no_buying_signal",
            "validated_at": datetime.now(timezone.utc).isoformat(),
        }
        _timelines[opp["opportunity_id"]] = [
            {
                "event_type": "signal_detected",
                "description": f"{opp['buying_signal']} signal detected",
                "source": opp["connector"],
                "timestamp": opp["collection_timestamp"],
            }
        ]


_seed_demo_data()


# === API Endpoints ===

@router.get("/dashboard")
async def get_dashboard() -> dict[str, Any]:
    """Get validation dashboard metrics."""
    total = len(_opportunities)
    accepted = sum(1 for v in _validations.values() if v.get("decision") == "approve")
    rejected = sum(1 for v in _validations.values() if v.get("decision") == "reject")

    avg_score = 0
    if _opportunities:
        avg_score = sum(o.get("quality_score", 0) for o in _opportunities.values()) / total

    avg_age = 0
    if _opportunities:
        avg_age = sum(o.get("signal_age_days", 0) for o in _opportunities.values()) / total

    return {
        "collected_today": total,
        "accepted": accepted,
        "rejected": rejected,
        "archived": 0,
        "spam": 0,
        "competitor": 0,
        "duplicate": 0,
        "ai_companies": 0,
        "old_opportunities": sum(1 for o in _opportunities.values() if o.get("signal_age_days", 0) > 120),
        "average_signal_age": round(avg_age, 2),
        "average_quality_score": round(avg_score, 2),
        "average_timeline_length": 1.0,
        "top_connectors": _get_top_connectors(),
        "worst_connectors": _get_worst_connectors(),
        "top_rejection_reasons": _get_top_rejection_reasons(),
        "most_valuable_signal_types": _get_most_valuable_signals(),
        "median_time_to_revenue_ready": 0,
        "oldest_opportunity": _get_oldest_opportunity(),
        "newest_opportunity": _get_newest_opportunity(),
        "companies_missing_timeline": 0,
        "companies_missing_evidence": 0,
        "companies_missing_website": 0,
        "companies_missing_decision_maker": 0,
    }


@router.get("/company/{company_id}")
async def get_company_validation(company_id: str) -> dict[str, Any]:
    """Get company validation details."""
    opp = _opportunities.get(company_id)
    if not opp:
        return {"error": "Company not found"}

    validation = _validations.get(company_id, {})
    timeline = _timelines.get(company_id, [])

    return {
        "company_id": company_id,
        "company_name": opp.get("company_name", "unknown"),
        "website": opp.get("website", "unknown"),
        "validation": validation,
        "timeline": timeline,
        "timeline_length": len(timeline),
        "explanation": _build_explanation(opp, validation),
    }


@router.get("/opportunity/{opportunity_id}")
async def get_opportunity_validation(opportunity_id: str) -> dict[str, Any]:
    """Get opportunity validation details."""
    opp = _opportunities.get(opportunity_id)
    if not opp:
        return {"error": "Opportunity not found"}

    validation = _validations.get(opportunity_id, {})
    timeline = _timelines.get(opportunity_id, [])

    return {
        "opportunity_id": opportunity_id,
        "company_name": opp.get("company_name", "unknown"),
        "website": opp.get("website", "unknown"),
        "connector": opp.get("connector", "unknown"),
        "signal_type": opp.get("signal_type", "unknown"),
        "signal_age_days": opp.get("signal_age_days", 0),
        "quality_score": opp.get("quality_score", 0),
        "freshness": opp.get("freshness", "unknown"),
        "buying_signal": opp.get("buying_signal", "unknown"),
        "icp_match": opp.get("icp_match", False),
        "validation": validation,
        "timeline": timeline,
        "timeline_length": len(timeline),
        "explanation": _build_explanation(opp, validation),
    }


@router.get("/timeline/{opportunity_id}")
async def get_timeline(opportunity_id: str) -> dict[str, Any]:
    """Get opportunity timeline."""
    opp = _opportunities.get(opportunity_id)
    if not opp:
        return {"error": "Opportunity not found"}

    timeline = _timelines.get(opportunity_id, [])

    return {
        "opportunity_id": opportunity_id,
        "company_name": opp.get("company_name", "unknown"),
        "timeline": timeline,
        "timeline_length": len(timeline),
        "event_types": list(set(e.get("event_type", "unknown") for e in timeline)),
        "connectors_involved": list(set(e.get("source", "unknown") for e in timeline)),
    }


@router.get("/root-cause/{opportunity_id}")
async def get_root_cause(opportunity_id: str) -> dict[str, Any]:
    """Get root cause analysis."""
    opp = _opportunities.get(opportunity_id)
    if not opp:
        return {"error": "Opportunity not found"}

    validation = _validations.get(opportunity_id, {})
    decision = validation.get("decision", "unknown")
    reasons = validation.get("reasons", [])

    root_causes = []
    for reason in reasons:
        root_causes.append(_map_reason_to_root_cause(reason))

    return {
        "opportunity_id": opportunity_id,
        "company_name": opp.get("company_name", "unknown"),
        "decision": decision,
        "reasons": reasons,
        "root_causes": root_causes,
        "primary_root_cause": root_causes[0] if root_causes else {"root_cause": "unknown"},
    }


@router.get("/replay/{opportunity_id}")
async def replay_opportunity(opportunity_id: str) -> dict[str, Any]:
    """Replay opportunity through all engines."""
    opp = _opportunities.get(opportunity_id)
    if not opp:
        return {"error": "Opportunity not found"}

    validation = _validations.get(opportunity_id, {})
    timeline = _timelines.get(opportunity_id, [])

    replay = {
        "replay_id": f"replay-{opportunity_id}",
        "opportunity_id": opportunity_id,
        "company_name": opp.get("company_name", "unknown"),
        "replayed_at": datetime.now(timezone.utc).isoformat(),
        "stages": {
            "connector": {
                "stage": "connector",
                "connector": opp.get("connector", "unknown"),
                "signal_type": opp.get("signal_type", "unknown"),
                "original_url": opp.get("evidence", {}).get("url", "unknown"),
                "decision": "collected",
            },
            "dqe": {
                "stage": "dqe",
                "quality_score": opp.get("quality_score", 0),
                "freshness": opp.get("freshness", "unknown"),
                "buying_signal": opp.get("buying_signal", "unknown"),
                "icp_match": opp.get("icp_match", False),
                "decision": "passed" if opp.get("quality_score", 0) >= 75 else "failed",
            },
            "validation": {
                "stage": "validation",
                "decision": validation.get("decision", "unknown"),
                "reasons": validation.get("reasons", []),
                "root_cause": validation.get("root_cause", "unknown"),
            },
            "opportunity_intelligence": {
                "stage": "opportunity_intelligence",
                "status": "not_processed",
                "decision": "unknown",
            },
            "revenue_ready": {
                "stage": "revenue_ready",
                "status": "not_reached",
                "decision": "unknown",
            },
        },
        "summary": {
            "stages_completed": ["connector", "dqe", "validation"],
            "final_decision": validation.get("decision", "unknown"),
            "connector": opp.get("connector", "unknown"),
            "quality_score": opp.get("quality_score", 0),
        },
    }

    _replays[opportunity_id] = replay
    return replay


@router.get("/rejections")
async def get_rejections() -> dict[str, Any]:
    """Get rejection analysis."""
    rejections = []
    for opp_id, validation in _validations.items():
        if validation.get("decision") == "reject":
            opp = _opportunities.get(opp_id, {})
            rejections.append({
                "opportunity_id": opp_id,
                "company_name": opp.get("company_name", "unknown"),
                "reasons": validation.get("reasons", []),
                "root_cause": validation.get("root_cause", "unknown"),
            })

    reasons_count = {}
    for r in rejections:
        for reason in r.get("reasons", []):
            reasons_count[reason] = reasons_count.get(reason, 0) + 1

    return {
        "total_rejections": len(rejections),
        "rejections": rejections,
        "top_reasons": [{"reason": r, "count": c} for r, c in sorted(reasons_count.items(), key=lambda x: x[1], reverse=True)[:10]],
    }


@router.get("/connectors")
async def get_connector_performance() -> dict[str, Any]:
    """Get connector performance."""
    connector_stats: dict[str, dict[str, Any]] = {}

    for opp in _opportunities.values():
        connector = opp.get("connector", "unknown")
        if connector not in connector_stats:
            connector_stats[connector] = {"total": 0, "accepted": 0, "rejected": 0}

        connector_stats[connector]["total"] += 1
        validation = _validations.get(opp.get("opportunity_id", ""), {})
        if validation.get("decision") == "approve":
            connector_stats[connector]["accepted"] += 1
        else:
            connector_stats[connector]["rejected"] += 1

    connector_rates = {}
    for connector, stats in connector_stats.items():
        total = stats["total"]
        rate = stats["accepted"] / total if total > 0 else 0
        connector_rates[connector] = {
            "total": total,
            "accepted": stats["accepted"],
            "rejected": stats["rejected"],
            "acceptance_rate": round(rate, 3),
        }

    best = max(connector_rates.items(), key=lambda x: x[1]["acceptance_rate"])[0] if connector_rates else None
    worst = min(connector_rates.items(), key=lambda x: x[1]["acceptance_rate"])[0] if connector_rates else None

    return {
        "total_connectors": len(connector_rates),
        "connector_rates": connector_rates,
        "best_connector": best,
        "worst_connector": worst,
    }


@router.get("/statistics")
async def get_statistics() -> dict[str, Any]:
    """Get validation statistics."""
    total = len(_opportunities)
    decisions = {}
    connectors = {}
    signal_types = {}

    for opp in _opportunities.values():
        opp_id = opp.get("opportunity_id", "unknown")
        validation = _validations.get(opp_id, {})
        decision = validation.get("decision", "unknown")
        connector = opp.get("connector", "unknown")
        signal_type = opp.get("signal_type", "unknown")

        decisions[decision] = decisions.get(decision, 0) + 1
        connectors[connector] = connectors.get(connector, 0) + 1
        signal_types[signal_type] = signal_types.get(signal_type, 0) + 1

    return {
        "total_opportunities": total,
        "by_decision": decisions,
        "by_connector": connectors,
        "by_signal_type": signal_types,
        "acceptance_rate": round(decisions.get("approve", 0) / total, 3) if total > 0 else 0,
        "rejection_rate": round(decisions.get("reject", 0) / total, 3) if total > 0 else 0,
    }


# === Helper functions ===

def _build_explanation(opp: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    """Build explanation for opportunity."""
    decision = validation.get("decision", "unknown")
    reasons = validation.get("reasons", [])

    if decision == "approve":
        why = f"You are seeing {opp.get('company_name', 'unknown')} because {opp.get('connector', 'unknown')} discovered them with a {opp.get('buying_signal', 'unknown')} signal."
    else:
        why = f"{opp.get('company_name', 'unknown')} was rejected because: {'; '.join(reasons)}"

    return {
        "why_am_i_seeing_this": why,
        "collected_by": opp.get("connector", "unknown"),
        "evidence": opp.get("evidence", {}),
        "freshness": opp.get("freshness", "unknown"),
        "buying_signal": opp.get("buying_signal", "unknown"),
        "icp_match": opp.get("icp_match", False),
        "quality_score": opp.get("quality_score", 0),
    }


def _map_reason_to_root_cause(reason: str) -> dict[str, Any]:
    """Map reason to root cause."""
    reason_lower = reason.lower()

    if "no buying signal" in reason_lower or "invalid buying signal" in reason_lower:
        return {"root_cause": "no_buying_signal", "category": "signal", "description": "No valid buying signal"}
    if "signal too old" in reason_lower or "stale" in reason_lower:
        return {"root_cause": "stale_signal", "category": "freshness", "description": "Signal too old"}
    if "ai company" in reason_lower:
        return {"root_cause": "ai_company", "category": "company", "description": "AI/LLM company"}
    if "low quality" in reason_lower:
        return {"root_cause": "low_quality_score", "category": "quality", "description": "Low quality score"}
    if "no icp" in reason_lower:
        return {"root_cause": "no_icp_match", "category": "targeting", "description": "No ICP match"}

    return {"root_cause": "unknown", "category": "unknown", "description": reason}


def _get_top_connectors() -> list[dict[str, Any]]:
    """Get top connectors."""
    connector_stats: dict[str, dict[str, Any]] = {}
    for opp in _opportunities.values():
        connector = opp.get("connector", "unknown")
        if connector not in connector_stats:
            connector_stats[connector] = {"total": 0, "accepted": 0}
        connector_stats[connector]["total"] += 1
        validation = _validations.get(opp.get("opportunity_id", ""), {})
        if validation.get("decision") == "approve":
            connector_stats[connector]["accepted"] += 1

    rates = []
    for connector, stats in connector_stats.items():
        total = stats["total"]
        rate = stats["accepted"] / total if total > 0 else 0
        rates.append({"connector": connector, "acceptance_rate": round(rate, 3), "total": total})

    return sorted(rates, key=lambda x: x["acceptance_rate"], reverse=True)[:5]


def _get_worst_connectors() -> list[dict[str, Any]]:
    """Get worst connectors."""
    return list(reversed(_get_top_connectors()))[:5]


def _get_top_rejection_reasons() -> list[dict[str, Any]]:
    """Get top rejection reasons."""
    reasons_count: dict[str, int] = {}
    for validation in _validations.values():
        if validation.get("decision") == "reject":
            for reason in validation.get("reasons", []):
                reasons_count[reason] = reasons_count.get(reason, 0) + 1

    return [{"reason": r, "count": c} for r, c in sorted(reasons_count.items(), key=lambda x: x[1], reverse=True)[:10]]


def _get_most_valuable_signals() -> list[dict[str, Any]]:
    """Get most valuable signal types."""
    signals_count: dict[str, int] = {}
    for opp in _opportunities.values():
        signal = opp.get("buying_signal", "unknown")
        signals_count[signal] = signals_count.get(signal, 0) + 1

    return [{"signal": s, "count": c} for s, c in sorted(signals_count.items(), key=lambda x: x[1], reverse=True)[:10]]


def _get_oldest_opportunity() -> dict[str, Any] | None:
    """Get oldest opportunity."""
    if not _opportunities:
        return None
    return max(_opportunities.values(), key=lambda x: x.get("signal_age_days", 0))


def _get_newest_opportunity() -> dict[str, Any] | None:
    """Get newest opportunity."""
    if not _opportunities:
        return None
    return min(_opportunities.values(), key=lambda x: x.get("signal_age_days", 0))
