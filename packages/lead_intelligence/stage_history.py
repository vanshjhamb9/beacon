"""Stage history, durations, decisions, and failure explanations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from lead_intelligence import PIPELINE_STAGES


STAGE_LABELS: dict[str, str] = {
    "signal": "Signals",
    "identity": "Identity",
    "website": "Website",
    "company": "Company",
    "enrichment": "Enrichment",
    "email": "Email",
    "decision_maker": "Decision Maker",
    "sales_ready": "Sales Ready",
    "revenue_ready": "Revenue Ready",
}


def _as_dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _duration_seconds(start: Any, end: Any) -> float | None:
    a, b = _as_dt(start), _as_dt(end)
    if not a or not b:
        return None
    return round(max((b - a).total_seconds(), 0.0), 2)


def build_stage_decisions(rows: list[dict[str, Any]], facts: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    facts = facts or {}
    by_stage = {str(r.get("stage")): r for r in rows if r.get("stage")}

    out: list[dict[str, Any]] = []
    for stage in PIPELINE_STAGES:
        row = by_stage.get(stage) or {}
        status = row.get("status")
        if not status:
            if facts.get(f"{stage}_rejected") or facts.get("rejected_stage") == stage:
                status = "rejected"
            elif facts.get(f"{stage}_at") or facts.get(f"has_{stage}"):
                status = "passed"
            else:
                status = "pending"
        reason = row.get("reason") or facts.get(f"{stage}_reason") or ""
        if not reason and status == "passed":
            reason = {
                "signal": "Public signal collected",
                "identity": "Identity candidate created",
                "website": "Website verified",
                "company": "Company extracted",
                "enrichment": "Enrichment attempted",
                "email": "Business email recovered",
                "decision_maker": "Decision maker recovered",
                "sales_ready": "Sales Ready criteria met",
                "revenue_ready": "Revenue Ready criteria met",
            }.get(stage, "Stage completed")
        out.append(
            {
                "stage": stage,
                "label": STAGE_LABELS.get(stage, stage.replace("_", " ").title()),
                "status": status,
                "reason": reason,
                "entered_at": row.get("entered_at") or facts.get(f"{stage}_started_at"),
                "exited_at": row.get("exited_at") or facts.get(f"{stage}_at"),
                "duration_seconds": row.get("duration_seconds")
                or _duration_seconds(
                    row.get("entered_at") or facts.get(f"{stage}_started_at"),
                    row.get("exited_at") or facts.get(f"{stage}_at"),
                ),
                "filters_passed": list(row.get("filters_passed") or facts.get(f"{stage}_filters_passed") or []),
                "filters_failed": list(row.get("filters_failed") or facts.get(f"{stage}_filters_failed") or []),
                "payload": row.get("payload") or {},
            }
        )
    return out


def build_stage_durations(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "stage": d["stage"],
            "label": d["label"],
            "duration_seconds": d.get("duration_seconds"),
            "status": d.get("status"),
        }
        for d in decisions
        if d.get("status") in {"passed", "rejected", "failed"}
    ]


def failure_explanation(
    *,
    blockers: list[Any] | None = None,
    rejected_stage: str | None = None,
    reasons: list[str] | None = None,
    facts: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    facts = facts or {}
    reasons = list(reasons or [])
    blockers = list(blockers or facts.get("blockers") or [])
    for b in blockers:
        text = b if isinstance(b, str) else str(b.get("reason") or b.get("label") or b)
        if text and text not in reasons:
            reasons.append(text)

    inferred: list[str] = []
    if facts.get("generic_email_only"):
        inferred.append("Generic email only")
    if facts.get("rejected") or facts.get("current_stage") == "rejected" or blockers or reasons:
        if not facts.get("has_founder") and not facts.get("founder"):
            inferred.append("No founder")
        if not facts.get("has_website") and not facts.get("domain"):
            inferred.append("No website")
        if not facts.get("has_hiring") and not facts.get("hiring"):
            inferred.append("No hiring signals")

    for item in inferred:
        if item not in reasons:
            reasons.append(item)

    explicitly_rejected = bool(
        facts.get("rejected") or facts.get("current_stage") == "rejected" or blockers or rejected_stage
    )
    if not explicitly_rejected and not reasons:
        return None

    if not reasons:
        reasons = ["Rejected by pipeline filters"]

    return {
        "status": "rejected",
        "rejected_stage": rejected_stage or facts.get("rejected_stage") or "unknown",
        "reasons": reasons,
        "detail": "; ".join(reasons),
    }


def compare_revenue_ready_vs_rejected(
    ready: dict[str, Any],
    rejected: dict[str, Any],
) -> dict[str, Any]:
    """Highlight differences between a Revenue Ready lead and a rejected one."""
    keys = (
        ("has_website", "Website verified"),
        ("has_email", "Business email"),
        ("has_founder", "Founder / decision maker"),
        ("has_hiring", "Hiring signals"),
        ("has_funding", "Funding signals"),
        ("has_industry", "Industry match"),
        ("confidence", "Confidence"),
        ("trust", "Trust"),
    )
    diffs: list[dict[str, Any]] = []
    for key, label in keys:
        a = ready.get(key)
        b = rejected.get(key)
        if a != b:
            diffs.append({"field": key, "label": label, "revenue_ready": a, "rejected": b})
    return {
        "revenue_ready_company": ready.get("company_name") or ready.get("company"),
        "rejected_company": rejected.get("company_name") or rejected.get("company"),
        "differences": diffs,
        "ready_advantages": [d["label"] for d in diffs if d["revenue_ready"] and not d["rejected"]],
        "rejected_gaps": [d["label"] for d in diffs if not d["revenue_ready"] and d["rejected"] is False],
    }
