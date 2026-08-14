"""Explorer service helpers — pure assembly over LIX payloads."""

from __future__ import annotations

from typing import Any

from lead_intelligence.enrichment_history import summarize_enrichments
from lead_intelligence.evidence_chain import assemble_evidence_chain
from lead_intelligence.lead_explainer import (
    latest_fields,
    lead_summary_dict,
    promotion_explanation,
    serialize_field_history,
)
from lead_intelligence.lead_timeline import build_replay_frames, serialize_timeline_event, sort_timeline
from lead_intelligence.provider_history import connector_contribution, merge_provider_history
from lead_intelligence.score_breakdown import explain_score
from lead_intelligence.stage_history import (
    build_stage_decisions,
    build_stage_durations,
    compare_revenue_ready_vs_rejected,
    failure_explanation,
)


def assemble_company_explorer(bundle: dict[str, Any]) -> dict[str, Any]:
    """Assemble the full Lead Explorer payload from a preloaded bundle."""
    facts = dict(bundle.get("facts") or {})
    summary = lead_summary_dict({**facts, **(bundle.get("summary") or {})})
    timeline_raw = sort_timeline(list(bundle.get("events") or []))
    timeline = [serialize_timeline_event(e) for e in timeline_raw]
    providers = merge_provider_history(list(bundle.get("providers") or []))
    enrichments = summarize_enrichments(list(bundle.get("providers") or []) + list(bundle.get("enrichments") or []))
    evidence = assemble_evidence_chain(list(bundle.get("evidence") or []))
    score = explain_score(
        total_score=float(summary.get("current_score") or summary.get("confidence") or 0),
        facts=facts,
        existing_components=list(bundle.get("score_components") or []),
    )
    fields = serialize_field_history(list(bundle.get("fields") or []))
    stages = build_stage_decisions(list(bundle.get("stages") or []), facts=facts)
    durations = build_stage_durations(stages)
    failure = failure_explanation(
        blockers=list(facts.get("blockers") or []),
        rejected_stage=facts.get("rejected_stage"),
        facts=facts,
    )
    promotion = promotion_explanation(facts)

    return {
        "summary": summary,
        "timeline": timeline,
        "providers": providers,
        "enrichments": enrichments,
        "evidence": evidence,
        "score": score,
        "fields": fields,
        "latest_fields": latest_fields(fields),
        "stages": stages,
        "stage_durations": durations,
        "failure": failure,
        "promotion": promotion,
        "replay": build_replay_frames(timeline_raw),
        "scoring_version": bundle.get("scoring_version") or "lix-v1",
    }


def assemble_search_results(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "company_id": r.get("company_id"),
            "company": r.get("company") or r.get("company_name"),
            "domain": r.get("domain"),
            "email": r.get("email") or r.get("business_email"),
            "founder": r.get("founder"),
            "lead_id": r.get("lead_id") or r.get("company_id"),
            "revenue_ready_id": r.get("revenue_ready_id"),
            "revenue_ready": bool(r.get("revenue_ready")),
            "current_stage": r.get("current_stage"),
            "score": r.get("score") or r.get("confidence"),
            "source": r.get("source"),
        }
        for r in rows
    ]


def assemble_connector_contribution(provider_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return connector_contribution(provider_rows)


def assemble_pipeline_comparison(ready: dict[str, Any], rejected: dict[str, Any]) -> dict[str, Any]:
    return compare_revenue_ready_vs_rejected(ready, rejected)
